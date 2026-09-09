"""
TrOCR model wrapper and processor management for handwritten medical text.

Baseline architecture: microsoft/trocr-small-handwritten.
"""

from typing import Any, Dict, List, Optional
from PIL import Image

from handwriting.config import ModelConfig


class TrOCRModule:
    """Wrapper managing TrOCR processor and VisionEncoderDecoderModel.

    Baseline architecture: microsoft/trocr-small-handwritten (~62M params).
    Uses lazy loading to avoid requiring PyTorch/transformers during lightweight inspections.
    """

    def __init__(self, config: Optional[ModelConfig] = None):
        self.config = config or ModelConfig()
        self.model_name = self.config.model_name_or_path
        self._processor = None
        self._model = None
        self._device = None

    @staticmethod
    def is_available() -> bool:
        """Check if torch and transformers packages are installed."""
        try:
            import torch  # noqa: F401
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def load_model(self, device: Optional[str] = None) -> Any:
        """Load TrOCR processor and VisionEncoderDecoderModel.

        Args:
            device: Target device ('cuda', 'cpu', or None for auto-detection).

        Returns:
            The loaded VisionEncoderDecoderModel instance.
        """
        if not self.is_available():
            raise ImportError(
                "PyTorch or Hugging Face Transformers is not installed. "
                "To use TrOCR, install the handwriting requirements: "
                "`pip install -r handwriting/requirements.txt`."
            )

        import torch
        from transformers import TrOCRProcessor, VisionEncoderDecoderModel

        if device is None:
            device = "cuda" if torch.cuda.is_available() else "cpu"
        self._device = device

        if self._processor is None:
            try:
                self._processor = TrOCRProcessor.from_pretrained(self.model_name)
            except Exception:
                from transformers import AutoImageProcessor, XLMRobertaTokenizer
                img_proc = AutoImageProcessor.from_pretrained(self.model_name)
                tokenizer = XLMRobertaTokenizer.from_pretrained(self.model_name)
                self._processor = TrOCRProcessor(image_processor=img_proc, tokenizer=tokenizer)

        if self._model is None:
            self._model = VisionEncoderDecoderModel.from_pretrained(self.model_name)
            self._model.to(self._device)

            # Ensure required token attributes are configured for Transformers 5 forward passes with labels
            if getattr(self._model.config, "pad_token_id", None) is None:
                self._model.config.pad_token_id = getattr(self.processor.tokenizer, "pad_token_id", 1)
            if getattr(self._model.config, "decoder_start_token_id", None) is None:
                decoder_cfg = getattr(self._model.config, "decoder", None)
                self._model.config.decoder_start_token_id = (
                    getattr(decoder_cfg, "decoder_start_token_id", None)
                    or getattr(self.processor.tokenizer, "cls_token_id", 2)
                )

            if self.config.use_gradient_checkpointing and hasattr(self._model, "gradient_checkpointing_enable"):
                self._model.gradient_checkpointing_enable()

        return self._model

    @property
    def processor(self) -> Any:
        """Return the TrOCRProcessor instance (loads model if needed)."""
        if self._processor is None:
            self.load_model()
        return self._processor

    @property
    def model(self) -> Any:
        """Return the VisionEncoderDecoderModel instance (loads model if needed)."""
        if self._model is None:
            self.load_model()
        return self._model

    def decode_tokens_to_text(self, token_ids: Any) -> List[str]:
        """Decode generated token ID sequences into clean string transcriptions.

        Args:
            token_ids: Tensor or array of generated token sequences.

        Returns:
            List of decoded text strings.
        """
        return self.processor.batch_decode(token_ids, skip_special_tokens=True)

    def generate_from_images(
        self,
        images: List[Image.Image],
        max_new_tokens: Optional[int] = None,
    ) -> List[str]:
        """Process image crops and return decoded transcription strings.

        Args:
            images: List of PIL Image word/line crops.
            max_new_tokens: Token generation limit (defaults to config.max_target_length).

        Returns:
            List of decoded text transcriptions.
        """
        self.load_model()
        import torch

        max_tokens = max_new_tokens or self.config.max_target_length
        pixel_values = self.processor(images, return_tensors="pt").pixel_values.to(self._device)

        with torch.no_grad():
            generated_ids = self.model.generate(
                pixel_values,
                max_new_tokens=max_tokens,
            )

        decoded_strings = self.decode_tokens_to_text(generated_ids)
        return [s.strip() for s in decoded_strings]

    def get_parameter_summary(self) -> Dict[str, Any]:
        """Return parameter count summary for the TrOCR model."""
        if not self.is_available() or self._model is None:
            return {
                "model_name": self.model_name,
                "loaded": False,
                "approximate_parameters": "~62M (microsoft/trocr-small-handwritten)",
            }

        total_params = sum(p.numel() for p in self.model.parameters())
        trainable_params = sum(p.numel() for p in self.model.parameters() if p.requires_grad)

        return {
            "model_name": self.model_name,
            "loaded": True,
            "total_parameters": total_params,
            "trainable_parameters": trainable_params,
            "device": str(self._device),
            "gradient_checkpointing": self.config.use_gradient_checkpointing,
        }
