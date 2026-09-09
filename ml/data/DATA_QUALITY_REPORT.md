# MedIntel AI — Data Quality Report

> Phase 3: Data Collection & Preparation
>
> Note: Actual dataset files are stored outside the Git repository.
> This report documents dataset characteristics based on the verified
> dataset source documentation and expected inspection results.

---

## 1. Pima Indians Diabetes Database

### Source Information

| Property | Value |
|----------|-------|
| Source Row Count | 768 |
| Source Column Count | 9 (8 features + 1 target) |
| Feature Count | 8 |
| Target | `Outcome` (0 = No diabetes, 1 = Diabetes) |

### Missing Values

**No explicit NaN values** in the source file.

However, zero values in the following columns are physiologically implausible and represent missing data:

| Column | Known Issue |
|--------|------------|
| Glucose | 0 mm Hg is impossible for a living person |
| BloodPressure | 0 mm Hg is impossible |
| SkinThickness | 0 mm is implausible |
| Insulin | 0 mu U/ml is implausible |
| BMI | 0 kg/m² is impossible |

### Duplicates

Minimal or no exact duplicate rows expected.

### Class Distribution

| Class | Approximate Count | Approximate % |
|-------|-------------------|----------------|
| 0 (No diabetes) | ~500 | ~65% |
| 1 (Diabetes) | ~268 | ~35% |

Moderately imbalanced toward the negative class.

### Invalid / Suspicious Values

- Zero values in Glucose, BloodPressure, SkinThickness, Insulin, BMI
- These are NOT true zeros — they represent missing measurements

### Planned Cleaning

1. Replace zeros in the five columns above with NaN
2. Fill NaN with column median
3. Validate target encoding (only 0 and 1)
4. Remove exact duplicates

### Expected Processed Output

- ~768 rows (minus any duplicates)
- 9 columns unchanged
- No zero values in the five cleaned columns
- Target distribution preserved

### Limitations

- **Single demographic**: All Pima Indian females, ≥21 years old, Phoenix AZ
- **Not generalizable**: Results may not apply to other populations
- **Data age**: Collected in the 1980s–1990s

---

## 2. UCI Heart Disease Dataset (Cleveland)

### Source Information

| Property | Value |
|----------|-------|
| Source Row Count | 303 |
| Source Column Count | 14 (13 features + 1 target) |
| Feature Count | 13 |
| Target | `num` → `target` (0 = absence, 1–4 = presence → binary 0/1) |

### Missing Values

| Column | Expected Missing | Encoding |
|--------|-----------------|----------|
| ca | ~4 values | `?` in original UCI format |
| thal | ~2 values | `?` in original UCI format |

Note: Pre-processed Kaggle versions may already have these handled.

### Duplicates

Minimal or no exact duplicate rows expected.

### Class Distribution (after binarization)

| Class | Approximate Count | Approximate % |
|-------|-------------------|----------------|
| 0 (No heart disease) | ~164 | ~54% |
| 1 (Heart disease) | ~139 | ~46% |

Relatively balanced.

### Invalid / Suspicious Values

- `ca` values outside 0–3 range
- `thal` values (3, 6, 7) — some versions use different encodings
- `?` strings in original UCI format

### Planned Cleaning

1. Handle `?` missing values → NaN → drop affected rows
2. Normalize target to binary: 0 stays 0, 1–4 → 1
3. Convert all numeric columns to proper numeric types
4. Remove exact duplicates

### Expected Processed Output

- ~297–303 rows (depending on missing value rows dropped)
- 14 columns
- Binary target (0 or 1)
- All numeric types validated

### Limitations

- **Small sample**: Only 303 records
- **Data age**: Collected in the 1980s
- **Single site**: Cleveland Clinic Foundation
- **Potential sex imbalance**: More male patients in the dataset

---

## 3. UCI Chronic Kidney Disease Dataset

### Source Information

| Property | Value |
|----------|-------|
| Source Row Count | 400 |
| Source Column Count | 25–26 (24 features + target, optional id) |
| Feature Count | 24 |
| Target | `classification` or `class` (ckd / notckd → 1 / 0) |

### Missing Values

**Significant missing data** across many columns.

| Column | Approximate Missing % |
|--------|----------------------|
| rbc | ~38% |
| pc | ~16% |
| pcc | ~1% |
| ba | ~1% |
| bgr | ~11% |
| bu | ~5% |
| sc | ~4% |
| sod | ~21% |
| pot | ~22% |
| hemo | ~13% |
| pcv | ~18% |
| wc | ~26% |
| rc | ~33% |
| sg | ~12% |
| al | ~12% |
| su | ~12% |
| rbc | ~38% |

Note: Exact percentages depend on the version downloaded. The above are approximate based on the original UCI dataset documentation.

### Duplicates

Minimal or no exact duplicate rows expected.

### Class Distribution

| Class | Approximate Count | Approximate % |
|-------|-------------------|----------------|
| ckd (→ 1) | ~250 | ~62.5% |
| notckd (→ 0) | ~150 | ~37.5% |

Moderately imbalanced toward the CKD class.

### Invalid / Suspicious Values

- Leading/trailing whitespace in string values
- Tab characters in target column (e.g., `ckd\t`)
- Inconsistent yes/no formatting in some columns
- `?` used as missing value marker
- Some numeric columns stored as strings

### Planned Cleaning

1. Strip all whitespace from string values
2. Normalize target: `ckd` → 1, `notckd` → 0
3. Normalize categorical values
4. Replace `?` with NaN
5. Convert numeric columns to proper types
6. Fill numeric NaN with column median
7. Fill categorical NaN with column mode
8. Drop `id` column if present
9. Remove exact duplicates

### Expected Processed Output

- ~400 rows (minus any duplicates)
- 24 feature columns + 1 target column
- Binary target (0 or 1)
- No missing values
- Consistent categorical values

### Limitations

- **Small sample**: Only 400 records
- **Single hospital**: Apollo Hospitals, Tamil Nadu, India
- **Heavy imputation**: Many features require median/mode imputation
- **Potential bias**: Indian patient population

---

## Data Leakage Prevention Strategy

The **future** ML Model Development phase (Phase 6) must follow this workflow to prevent data leakage:

```
External Raw Dataset
        ↓
Basic deterministic cleaning (Phase 3 scripts)
        ↓
X / y separation
        ↓
Train / Validation / Test split (e.g., 70/15/15 or 80/10/10)
        ↓
Fit preprocessing ONLY on training data
  └── Scaling, encoding, SMOTE (if used) — training set only
        ↓
Transform validation and test sets using training-fitted preprocessors
        ↓
ML model training on training set only
        ↓
Evaluation on validation set (hyperparameter tuning)
        ↓
Final evaluation on test set (one time)
```

**Critical rules:**
- SMOTE or other resampling must be applied **only to the training set**, never before splitting.
- Scaling/normalization must be **fit** on the training set, then **transform** applied to validation/test.
- No information from validation/test sets may influence training decisions.
- The Phase 3 preparation scripts perform only **deterministic cleaning** (not ML-dependent transforms).

---

## Summary

| Dataset | Rows | Features | Target | Missing Strategy | Key Issue |
|---------|------|----------|--------|-----------------|----------|
| Diabetes | 768 | 8 | Outcome (0/1) | Zeros → NaN → median | Implausible zeros |
| Heart Disease | 303 | 13 | num → binary (0/1) | `?` → NaN → drop rows | Small sample, `?` markers |
| Kidney Disease | 400 | 24 | class → binary (0/1) | NaN → median/mode | Heavy missing data, formatting |

**These exact three datasets will be used for the subsequent ML Model Development phase.**
