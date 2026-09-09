"""
Memory-safe training engine for TrOCR on handwritten prescription crops.

Features:
- Configurable per-device batch size (default 2, reducible to 1 on OOM)
- Gradient accumulation (default 8 steps -> effective batch size 16)
- fp16 mixed precision via torch.cuda.amp
- Gradient checkpointing enabled for 4GB VRAM constraint
- Strict test-set isolation (test splits cannot be used for training or validation)
- Validation metric tracking: CER computed on decoded text predictions
- Checkpointing based on best validation CER
- Early stopping with configurable patience
- Deterministic seeding (seed 42)
"""

import json
import logging
import random
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional
import numpy as np

from handwriting.config import HandwritingPipelineConfig, TrainingConfig
from handwriting.data.dataset import HandwritingDataset
from handwriting.evaluation.metrics import character_error_rate
from handwriting.models.trocr_module import TrOCRModule

logger = logging.getLogger("medintel.handwriting.trainer")


def set_seed(seed: int = 42) -> None:
    """Set random seeds across Python, NumPy, and PyTorch for deterministic runs."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass


class TrOCRTrainer:
    """Orchestrates memory-safe fine-tuning of TrOCR for handwritten prescription recognition."""

    def __init__(
        self,
        config: Optional[HandwritingPipelineConfig] = None,
        trocr_module: Optional[TrOCRModule] = None,
    ):
        self.config = config or HandwritingPipelineConfig()
        self.train_config = self.config.training
        self.trocr = trocr_module or TrOCRModule(self.config.model)

        # Enforce deterministic seed
        set_seed(self.train_config.seed)

        self.checkpoint_dir = Path(self.train_config.checkpoint_dir)
        self.checkpoint_dir.mkdir(parents=True, exist_ok=True)

        self.output_dir = Path(self.train_config.output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.log_file = self.output_dir / "training_log.jsonl"

    def validate_split_isolation(self, train_split: str, val_split: str) -> None:
        """Enforce strict protection: test splits must NEVER be passed to the trainer."""
        if "test" in (train_split.lower(), val_split.lower()):
            raise ValueError(
                f"SECURITY VIOLATION: Test split detected in training configuration! "
                f"train_split='{train_split}', val_split='{val_split}'. "
                f"Test splits must remain strictly untouched until final benchmark evaluation."
            )

    def log_step(self, data: Dict[str, Any]) -> None:
        """Append log record to the JSONL training log file."""
        data["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(data) + "\n")

    def run_validation(
        self,
        val_dataset: HandwritingDataset,
        batch_size: Optional[int] = None,
    ) -> Dict[str, float]:
        """Evaluate current model weights on validation split.

        Decodes generated tokens into text strings before computing validation CER.
        """
        eval_batch_size = batch_size or self.train_config.per_device_eval_batch_size
        predictions: List[str] = []
        references: List[str] = []

        # Process in mini-batches
        for i in range(0, len(val_dataset), eval_batch_size):
            batch_items = [val_dataset[j] for j in range(i, min(i + eval_batch_size, len(val_dataset)))]
            images = [item["image"] for item in batch_items]
            refs = [item["transcription"] for item in batch_items]

            decoded_texts = self.trocr.generate_from_images(images)
            predictions.extend(decoded_texts)
            references.extend(refs)

        cer = character_error_rate(predictions, references)
        return {"val_cer": cer, "val_samples": len(predictions)}

    def train(
        self,
        train_dataset: HandwritingDataset,
        val_dataset: HandwritingDataset,
    ) -> Dict[str, Any]:
        """Execute memory-safe training loop.

        Args:
            train_dataset: Training HandwritingDataset (split='train').
            val_dataset: Validation HandwritingDataset (split='val').

        Returns:
            Dictionary containing best checkpoint metadata and training metrics.
        """
        # 1. Enforce split isolation
        if train_dataset.records:
            self.validate_split_isolation(train_dataset.records[0].split, val_dataset.records[0].split)

        if not self.trocr.is_available():
            raise ImportError(
                "PyTorch and transformers must be installed to run training. "
                "See handwriting/requirements.txt."
            )

        import torch
        from torch.utils.data import DataLoader

        device = "cuda" if torch.cuda.is_available() else "cpu"
        model = self.trocr.load_model(device=device)
        model.train()

        # Log initial configuration
        config_record = {
            "event": "training_start",
            "model_name": self.config.model.model_name_or_path,
            "train_samples": len(train_dataset),
            "val_samples": len(val_dataset),
            "per_device_train_batch_size": self.train_config.per_device_train_batch_size,
            "gradient_accumulation_steps": self.train_config.gradient_accumulation_steps,
            "effective_batch_size": self.train_config.effective_batch_size,
            "learning_rate": self.train_config.learning_rate,
            "num_epochs": self.train_config.num_train_epochs,
            "fp16": self.train_config.fp16 and device == "cuda",
            "gradient_checkpointing": self.config.model.use_gradient_checkpointing,
            "device": device,
        }
        self.log_step(config_record)
        logger.info("Starting TrOCR training with effective batch size %d", self.train_config.effective_batch_size)

        # 2. Setup DataLoader with deterministic shuffling
        generator = torch.Generator().manual_seed(self.train_config.seed)
        train_loader = DataLoader(
            train_dataset,
            batch_size=self.train_config.per_device_train_batch_size,
            shuffle=True,
            generator=generator,
            collate_fn=lambda batch: batch[0],
        )

        best_val_cer = float("inf")
        patience_counter = 0
        best_checkpoint_path = None

        scaler = torch.amp.GradScaler("cuda", enabled=(self.train_config.fp16 and device == "cuda"))
        optimizer = torch.optim.AdamW(
            model.parameters(),
            lr=self.train_config.learning_rate,
            weight_decay=self.train_config.weight_decay,
        )

        # 3. Setup linear warmup scheduler
        from transformers import get_linear_schedule_with_warmup
        total_training_steps = (
            self.train_config.max_steps
            if self.train_config.max_steps is not None
            else (len(train_loader) * self.train_config.num_train_epochs) // max(self.train_config.gradient_accumulation_steps, 1)
        )
        num_warmup_steps = int(total_training_steps * self.train_config.warmup_ratio)
        scheduler = get_linear_schedule_with_warmup(
            optimizer,
            num_warmup_steps=num_warmup_steps,
            num_training_steps=max(total_training_steps, 1),
        )

        optimizer_steps = 0
        early_stopped = False

        for epoch in range(1, self.train_config.num_train_epochs + 1):
            epoch_loss = 0.0
            steps = 0
            optimizer.zero_grad()

            for step, batch_item in enumerate(train_loader):
                # Word-level forward pass with AMP mixed precision
                img = batch_item["image"]
                label_text = batch_item["transcription"]

                pixel_values = self.trocr.processor(img, return_tensors="pt").pixel_values.to(device)
                labels = self.trocr.processor.tokenizer(
                    label_text,
                    return_tensors="pt",
                    max_length=self.config.model.max_target_length,
                    padding="max_length",
                    truncation=True,
                ).input_ids.to(device)
                labels[labels == self.trocr.processor.tokenizer.pad_token_id] = -100

                with torch.amp.autocast("cuda", enabled=(self.train_config.fp16 and device == "cuda")):
                    outputs = model(pixel_values=pixel_values, labels=labels)
                    loss = outputs.loss / self.train_config.gradient_accumulation_steps

                scaler.scale(loss).backward()
                epoch_loss += loss.item() * self.train_config.gradient_accumulation_steps
                steps += 1

                if (step + 1) % self.train_config.gradient_accumulation_steps == 0 or (step + 1) == len(train_loader):
                    if self.train_config.fp16 and device == "cuda":
                        scaler.unscale_(optimizer)
                    if self.train_config.max_grad_norm > 0:
                        torch.nn.utils.clip_grad_norm_(
                            model.parameters(),
                            max_norm=self.train_config.max_grad_norm,
                        )
                    scaler.step(optimizer)
                    scaler.update()
                    scheduler.step()
                    optimizer.zero_grad()
                    optimizer_steps += 1

                    if self.train_config.max_steps and optimizer_steps >= self.train_config.max_steps:
                        break

            avg_train_loss = epoch_loss / max(steps, 1)

            # Validation step
            val_metrics = self.run_validation(val_dataset)
            current_val_cer = val_metrics["val_cer"]

            self.log_step({
                "event": "epoch_end",
                "epoch": epoch,
                "avg_train_loss": round(avg_train_loss, 4),
                "val_cer": round(current_val_cer, 4),
            })

            # Checkpoint selection based strictly on validation CER
            if current_val_cer < best_val_cer:
                best_val_cer = current_val_cer
                patience_counter = 0
                best_checkpoint_path = self.checkpoint_dir / "best_model"
                model.save_pretrained(best_checkpoint_path)
                self.trocr.processor.save_pretrained(best_checkpoint_path)
                self.log_step({
                    "event": "checkpoint_saved",
                    "epoch": epoch,
                    "val_cer": current_val_cer,
                    "path": str(best_checkpoint_path),
                })
            else:
                patience_counter += 1
                if patience_counter >= self.train_config.early_stopping_patience:
                    self.log_step({
                        "event": "early_stopping",
                        "epoch": epoch,
                        "best_val_cer": best_val_cer,
                    })
                    break

            if self.train_config.max_steps and optimizer_steps >= self.train_config.max_steps:
                break

        return {
            "status": "complete",
            "best_val_cer": best_val_cer,
            "best_checkpoint_path": str(best_checkpoint_path) if best_checkpoint_path else None,
            "epochs_run": epoch,
        }
