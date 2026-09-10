# Handwriting Recognition Module

> MedIntel AI — Phase 5: Handwriting Recognition
>
> Deep-learning pipeline for recognizing handwritten medical prescription text crops using Microsoft TrOCR.

---

## 1. Executive Summary & Status

Phase 5 implements a deep learning handwriting recognition architecture using **Microsoft TrOCR (`microsoft/trocr-small-handwritten`)** optimized for word and line-level medical prescription crops.

- **Status**: **Complete & Evaluated**. Native 2,000-step training completed; official held-out test evaluation completed.
- **Hardware Profile**: Configured and executed on an NVIDIA GeForce RTX 3050 Laptop GPU (**4 GB VRAM**) using batch size 1, gradient accumulation 8 (effective batch size 8), FP16 mixed precision, and gradient checkpointing.

### 1.1 Phase 5 Official Results Summary

Full evaluation report available at [docs/PHASE5_HANDWRITING_RESULTS.md](../docs/PHASE5_HANDWRITING_RESULTS.md).

- **Combined Held-Out Test Set (1,776 samples)**:
  - **Case-Insensitive Exact Match**: **67.68%** (1,202 / 1,776 exact matches)
  - **Character Error Rate (CER)**: **20.34%**
  - **Word Error Rate (WER)**: **43.89%**
  - **Case-Sensitive Exact Match**: 59.07% (1,049 / 1,776 exact matches)
- **Doctor Prescription BD Test Split (661 samples)**: **5.55% CER**, **8.06% WER**, **91.83% Exact Match**.
- **RxHandBD Test Split (1,115 samples)**: **28.78% CER**, **63.30% WER**, **53.36% Exact Match**.
- **Frozen Checkpoint**: `D:\MedIntel-Datasets\handwriting\phase5_training_output_2000_native\best_checkpoint` (SHA-256: `189f9695e33e8229805940cbece72a12c57df4ff638e29d21769c15840469322`).

---

## 2. External Dataset & Audit

The dataset was curated and verified externally under `D:\MedIntel-Datasets\handwriting\phase5_derived\` using clean manifests.

### 2.1 Dataset Composition & Splits

| Dataset | Train | Validation | Test | Total Unique Images | Notes |
|---|---|---|---|---|---|
| **RxHandBD** | 4,017 | 446 | 1,115 | 5,578 | Official 1,115 test split preserved untouched |
| **Doctor's Prescription BD** | 3,084 | 661 | 661 | 4,406 | 274 redundant duplicate copies deduplicated |
| **Combined Primary** | **7,101** | **1,107** | **1,776** | **9,984** | **Consolidated real-world benchmark** |

### 2.2 Important Dataset Rules & Integrity
1. **Synthetic Data Excluded**: The `chinmays18` dataset is synthetic and is strictly **excluded** from the primary TrOCR training and evaluation pool.
2. **Zero Cross-Split Leakage**: Cryptographic SHA-256 analysis confirmed 0 byte-for-byte image leakage between train, validation, and test splits.
3. **Writer-Independent Generalization Disclaimer**: Writer-independent evaluation **cannot be guaranteed** because source contributor metadata did not provide distinct writer IDs.
4. **Test Set Protection**: Test splits are used exclusively for final evaluation and are strictly rejected by the training loop.

---

## 3. Architectural Boundary: Word/Line vs. Full Document

> [!IMPORTANT]
> **TrOCR is a WORD/LINE Image Recognition Model.**
> It is designed to recognize individual cropped words or short lines of handwriting. It cannot directly read an entire unsegmented multi-line prescription page.

Pipeline flow for prescription analysis:
```
Full Prescription Document / Image
                ↓
Document / Region Detection (Bounding Box Crops)
                ↓
Handwritten Word / Line Crop
                ↓
Aspect-Ratio Preserving Preprocessing
                ↓
TrOCR Vision-Encoder Decoder
                ↓
Predicted Decoded Transcription
                ↓
Mandatory User Verification
```

---

## 4. Image Preprocessing

Narrow prescription word crops (e.g. 300x50) must not be stretched directly into squares, which causes severe character distortion.

The preprocessing pipeline (`AspectRatioPreservingResize` in `handwriting/data/transforms.py`) strictly distinguishes three coordinate representations:
1. **Raw Dimensions**: `(orig_width, orig_height)` of the incoming crop.
2. **Preprocessing Dimensions**: `(scaled_width, scaled_height)` scaled proportionally to fit within 384x384.
3. **Model Input Dimensions**: `(384, 384)` square canvas with white padding (`pad_color = 255`).

---

## 5. Metric Evaluation Protocol

Metrics are computed strictly on **DECODED TEXT PREDICTIONS**, never directly on raw logits:

```
model outputs / logits
          ↓
    token decoding
          ↓
 predicted transcription
          ↓
compare against ground-truth transcription
          ↓
  CER / WER / Exact Match
```

- **Character Error Rate (CER)**: Levenshtein distance on character sequences / total reference characters.
- **Word Error Rate (WER)**: Levenshtein distance on word tokens / total reference words.
- **Exact Match (EM)**: Proportion of exact string matches (reported case-insensitive and case-sensitive).
- **Metric Integrity**: Raw metrics are computed without any dictionary post-processing or fuzzy matching. If dictionary correction is introduced later, raw and corrected metrics must be reported side-by-side.

Evaluation is disaggregated across three separate benchmarks:
1. `RxHandBD Test` (1,115 images)
2. `Doctor BD Test` (661 images)
3. `Combined Test` (1,776 images)

---

## 6. Model Confidence vs. Clinical Decision-Making

> [!WARNING]
> **Model Confidence is NOT Clinical Certainty.**
> Numerical confidence scores generated during decoding are model-derived heuristic metrics representing token log-probabilities. They do NOT guarantee pharmacological accuracy or clinical safety.
> Every prediction requires human clinician or patient verification.

---

## 7. Memory-Safe Training Configuration (4GB VRAM)

| Parameter | Setting | Rationale |
|---|---|---|
| **Base Model** | `microsoft/trocr-small-handwritten` | ~62M parameters; lightweight for laptop GPU |
| **Train Batch Size** | 2 | Configurable; can be reduced to 1 if OOM occurs |
| **Gradient Accumulation** | 8 | Effective batch size = 16 |
| **Precision** | `fp16` (Automatic Mixed Precision) | Halves memory footprint on Tensor Cores |
| **Gradient Checkpointing** | Enabled | Trades minor compute for significant VRAM savings |
| **Eval Batch Size** | 4 | Configurable per-device evaluation batch size |
| **Seed** | 42 | Deterministic random seed across Python, NumPy, PyTorch |
| **Early Stopping** | Patience = 2 epochs | Monitored on validation CER |

---

## 8. Module Structure

```
handwriting/
├── __init__.py               # Public package exports
├── config.py                 # Hyperparameters, hardware constraints, paths
├── requirements.txt          # ML-specific dependency definitions
├── data/
│   ├── __init__.py
│   ├── dataset.py            # Manifest-driven dataset loader & records
│   └── transforms.py         # Aspect-ratio preserving transforms
├── models/
│   ├── __init__.py
│   └── trocr_module.py       # TrOCR wrapper & processor management
├── training/
│   ├── __init__.py
│   └── trainer.py            # Memory-safe trainer with validation checkpointing
├── evaluation/
│   ├── __init__.py
│   ├── metrics.py            # Decoded string CER, WER, Exact Match
│   └── evaluate.py           # Multi-dataset benchmark evaluator
├── inference/
│   ├── __init__.py
│   └── predictor.py          # Word/line crop predictor
└── adapter.py                # BaseOCREngine adapter for backend integration
```

---

## 9. Safety & Disclaimer

> **Mandatory Disclaimer**: *This is not a medical diagnosis. Please consult a qualified healthcare professional.*
