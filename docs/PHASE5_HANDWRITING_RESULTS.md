# Phase 5: Handwriting Recognition — Final Evaluation & Benchmark Results

> MedIntel AI — Intelligent Medical Report Analyzer
>
> Final-Year Academic Project

---

## 1. Objective

The objective of Phase 5 is to establish, train, and evaluate a memory-safe deep-learning optical character/handwriting recognition pipeline capable of transcribing cropped words and line-level medical prescription text (medicine names, forms, and dosages) from real-world handwritten prescriptions.

---

## 2. Model Architecture

- **Base Architecture**: Microsoft TrOCR (`microsoft/trocr-small-handwritten`)
- **Framework**: PyTorch `VisionEncoderDecoderModel`
- **Vision Encoder**: Data-efficient Image Transformer (`DeiT`), patch size $16 \times 16$, input resolution $384 \times 384$
- **Language Decoder**: TrOCR autoregressive Transformer decoder with cross-attention
- **Total Parameters**: **61,596,672** (~61.6M parameters)
- **Trainable Parameters**: **61,596,672**
- **Tokenizer**: Byte-level BPE tokenizer (XLM-RoBERTa based, vocabulary size 64,002)

---

## 3. Training Configuration & Hardware Profile

The model was fine-tuned under strict memory constraints for an NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM):

| Parameter | Value | Technical Context |
| :--- | :--- | :--- |
| **Total Optimizer Steps** | 2,000 | 16,000 forward/backward passes (~2.25 epochs over training split) |
| **Per-Device Batch Size** | 1 | Preserves VRAM overhead on consumer GPU |
| **Gradient Accumulation** | 8 | Effective batch size = 8 |
| **Mixed Precision** | FP16 (`torch.amp.autocast`) | Halves activation and gradient storage memory |
| **Gradient Checkpointing** | Enabled | Recomputes activations in backward pass to fit in 4 GB VRAM |
| **Peak VRAM Allocated** | 1,205.56 MB (~1.18 GB) | ~29.4% of total GPU memory |
| **Peak VRAM Reserved** | 1,246.00 MB (~1.22 GB) | ~30.4% of total GPU memory |
| **Random Seed** | 42 | Deterministic seed for PyTorch, CuDNN, NumPy, and DataLoader |
| **DataLoader Shuffling** | Enabled (`shuffle=True`) | Seeded generator per epoch breaks contiguous identical-label blocks |
| **Optimization Algorithm** | AdamW (`weight_decay=0.01`) | Standard decoupled weight decay |
| **Peak Learning Rate** | $5.0 \times 10^{-5}$ | Reached after warmup |
| **Learning Rate Warmup** | 200 optimizer steps | Linear warmup over first 10% of training steps |
| **Learning Rate Decay** | Linear decay | Smooth monotonic decay to $\sim 0$ at step 2,000 |
| **Gradient Clipping** | `max_grad_norm = 1.0` | Scaler unscaled prior to norm clipping to prevent gradient explosion |
| **Image Preprocessing** | Aspect-Ratio Preserving | Scaled proportionally with white padding (`pad_color=255`) to $384 \times 384$ |
| **Decoding Protocol** | Raw greedy decoding | Argmax token generation without beam search, dictionaries, or language models |

---

## 4. Dataset Preparation & Curation Summary

The training and evaluation data was sourced exclusively from external curated datasets stored outside the Git repository:

1. **RxHandBD**: Real handwritten prescription word crops collected in clinical contexts. Official test split preserved.
2. **Doctor's Handwritten Prescription BD**: Real prescription word crops. 274 redundant exact-duplicate copies were removed during Phase 5 data preparation.
3. **Synthetic Data Exclusion**: Synthetic handwriting datasets (such as `chinmays18`) were strictly **excluded** from both primary training and evaluation pools to ensure purely real-world handwriting evaluation.
4. **Data Leakage Safeguards**: Cryptographic SHA-256 hash comparison across all image files confirmed **zero byte-for-byte image leakage** between train, validation, and test splits.
5. **Split Boundaries**:
   - **Combined Train**: 7,101 samples
   - **Combined Validation**: 1,107 samples
   - **Combined Held-Out Test**: 1,776 samples (1,115 RxHandBD + 661 Doctor BD)

---

## 5. Validation Performance

During training, validation was evaluated at every 100 optimizer steps using an identical fixed subset of 200 samples selected deterministically from `combined/val` (seed 42):

| Checkpoint | Validation CER | Validation WER | Validation Exact Match | Training Loss |
| :---: | :---: | :---: | :---: | :---: |
| **Base Model (Pre-trained)** | 68.72% | 156.80% | 6.50% | — |
| **Step 500** | 37.60% | 72.33% | 28.50% | 0.6579 |
| **Step 1000** | 21.19% | 47.57% | 57.50% | 1.2129 |
| **Step 1500** | 14.41% | 36.41% | 71.00% | 0.6584 |
| **Step 2000 (Best)** | **6.47%** | **20.87%** | **84.50%** | 0.1616 |

*The best validation checkpoint achieved **6.47% CER**, **20.87% WER**, and **84.50% Exact Match**.*

---

## 6. Official Held-Out Test Results

> [!IMPORTANT]
> **Evaluation Protocol Notice**:
> The official test set was used **ONLY** after training and checkpoint selection were complete. No test result was used for model tuning or hyperparameter selection.
> All metrics are calculated strictly on **raw model predictions** without applying any medicine dictionaries, spelling correction, or vocabulary post-processing.

### 6.1 Benchmark Results Summary

| Benchmark Split | Samples | Character Error Rate (CER) | Word Error Rate (WER) | Exact Match (Case-Insensitive) | Exact Match (Case-Sensitive) | Correct Transcriptions |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **RxHandBD Test** | 1,115 | **28.78%** | **63.30%** | **53.36%** | 39.64% | 595 / 1,115 |
| **Doctor BD Test** | 661 | **5.55%** | **8.06%** | **91.83%** | 91.83% | 607 / 661 |
| **Combined Test** | **1,776** | **20.34%** | **43.89%** | **67.68%** | **59.07%** | **1,202 / 1,776** |

### 6.2 Key Benchmark Takeaways
- **Doctor Prescription BD Benchmark**: The model exhibited strong generalization on standard prescription crops, achieving **5.55% CER**, **8.06% WER**, and **91.83% exact match accuracy** on 661 held-out test images.
- **RxHandBD Benchmark**: RxHandBD contains rapid, unconstrained, multi-writer clinical cursive script. The model achieved **28.78% CER** and **53.36% exact match accuracy**, demonstrating that even on challenging doctor cursive, more than half of all words are transcribed with zero character errors on raw greedy decoding.
- **Combined Test Benchmark**: Across all 1,776 held-out test samples, **67.68% (1,202 / 1,776)** of prescriptions were transcribed perfectly without vocabulary aids.

---

## 7. Error Analysis

Out of 1,776 held-out test samples, **574 predictions contained one or more discrepancies** (32.32% inexact rate). Analysis of these errors revealed the following patterns:

```
Observed Error Categorization (574 Inexact Samples):
├── Character Substitution:       250 (43.55%)
├── Complete Word Misrecognition: 120 (20.91%)
├── Character Deletion:            90 (15.68%)
├── Character Insertion:           82 (14.29%)
├── Digit / Dosage Confusion:      36  (6.27%)
├── Multi-Word Truncation:         31  (5.40%)
└── Spacing Difference:             1  (0.17%)
```

1. **Visually Ambiguous Cursive Substitutions (43.6%)**: The most frequent error mode involves visually identical lowercase cursive loops, such as `u` $\leftrightarrow$ `o` (`Lactu` $\rightarrow$ `lacto`), `c` $\leftrightarrow$ `e`, `m` $\leftrightarrow$ `n`, and `t` $\leftrightarrow$ `x` (`xyflo` $\rightarrow$ `tyflo`).
2. **Severely Degraded Cursive Handwriting (20.9%)**: In a subset of RxHandBD samples where physician handwriting consists of undifferentiated continuous wave-like strokes (e.g., `Domin`, `Clavutil`), the vision encoder cannot resolve character boundaries, resulting in misrecognition.
3. **Dosage & Strength Confusion (6.3%)**: Number confusion occurred in crops containing both a drug name and numeric strength, such as digit ambiguity between `3` and `5` (`DDR 30` $\rightarrow$ `DDR 50`).
4. **Multi-Word Truncation (5.4%)**: In crops with multiple words (e.g., brand name plus form/dosage like `Nexum Mups 20`), the model occasionally omitted trailing tokens (`Nexe mups`).
5. **Capitalization Variations**: 153 predictions matched the ground-truth text semantically but differed in case formatting (e.g., `zimax` $\rightarrow$ `Zimax`).

---

## 8. Limitations & Engineering Constraints

1. **No Writer-Independent Guarantee**: Neither source dataset provided distinct writer/physician identification metadata. Consequently, formal writer-independent split partitioning cannot be guaranteed, and performance may vary across unseen physician handwriting styles.
2. **Cross-Dataset Difficulty Disparity**: RxHandBD is substantially more challenging (28.78% CER) than Doctor BD (5.55% CER) due to faster, less legible penmanship and lower contrast scanning.
3. **Word/Line Crop Scope**: The TrOCR model is trained on word and short line-level crops. It **cannot** parse an entire unsegmented full-page prescription document end-to-end without an upstream text detector or bounding-box region locator.
4. **Numeric Dosage Sensitivity**: Handwritten numeric dosages require careful validation, as single-digit misreadings (`20mg` vs. `50mg`) represent a known failure mode of vision models on rapid handwriting.

---

## 9. Medical Safety Boundary & Clinical Non-Diagnosis Notice

> [!CAUTION]
> **Safety Boundary**:
> 1. The handwriting recognition pipeline is an **extraction assistance tool only**. It does **NOT** diagnose medical conditions, recommend therapies, or confirm medication safety.
> 2. Handwritten prescription recognition outputs must **ALWAYS** be presented to the user/clinician for explicit confirmation and editing before being passed downstream to reference-range lookups or risk estimation pipelines.
> 3. Never make automated clinical decisions or medication dispensing actions based solely on raw HTR/OCR model predictions.

---

## 10. Reproducibility & Artifact Registry

All evaluation artifacts, weights, and prediction logs are preserved outside the Git repository:

- **Model Checkpoint Path**: `D:\MedIntel-Datasets\handwriting\phase5_training_output_2000_native\best_checkpoint`
- **Model Weight File**: `model.safetensors`
- **SHA-256 Checksum**: `189f9695e33e8229805940cbece72a12c57df4ff638e29d21769c15840469322`
- **Prediction CSV Files**:
  - `D:\MedIntel-Datasets\handwriting\phase5_test_evaluation\rxhandbd_test_predictions.csv` (1,115 rows)
  - `D:\MedIntel-Datasets\handwriting\phase5_test_evaluation\doctor_bd_test_predictions.csv` (661 rows)
  - `D:\MedIntel-Datasets\handwriting\phase5_test_evaluation\combined_test_predictions.csv` (1,776 rows)
- **Metrics JSON File**: `D:\MedIntel-Datasets\handwriting\phase5_test_evaluation\phase5_official_test_metrics.json`
- **Runtime Environment**:
  - Python: `3.12.10`
  - PyTorch: `2.6.0+cu124`
  - Transformers: `5.17.0`
  - GPU: NVIDIA GeForce RTX 3050 Laptop GPU (4 GB VRAM, Driver: 572.70, CUDA: 12.8)
  - Operating System: Windows 11
