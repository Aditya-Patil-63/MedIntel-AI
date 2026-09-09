# ML Data Directory

Dataset documentation, metadata, and quality reports for MedIntel AI.

## Status

**Phase 3 — Data Collection & Preparation** ✅

## Important

> **Actual dataset files are NOT stored in this repository.**
>
> Datasets are stored in an external directory configured via the `MEDINTEL_DATA_DIR` environment variable.
>
> See [DATASET_SETUP.md](DATASET_SETUP.md) for setup instructions.

## Contents

| File/Directory | Purpose |
|----------------|----------|
| [DATASET_SOURCES.md](DATASET_SOURCES.md) | Detailed source documentation for all three datasets |
| [DATASET_SETUP.md](DATASET_SETUP.md) | Setup guide for external dataset storage |
| [DATA_QUALITY_REPORT.md](DATA_QUALITY_REPORT.md) | Data quality analysis for all datasets |
| [metadata/](metadata/) | Per-dataset metadata files |

## Datasets

| Dataset | Task | Records | Features | Target |
|---------|------|---------|----------|--------|
| Pima Indians Diabetes | Diabetes Risk | 768 | 8 | Outcome (0/1) |
| Heart Disease (Cleveland) | Heart Disease Risk | 303 | 13 | num → binary (0/1) |
| Chronic Kidney Disease | Kidney Disease Risk | 400 | 24 | class (ckd/notckd) |
