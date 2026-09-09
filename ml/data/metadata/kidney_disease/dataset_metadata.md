# UCI Chronic Kidney Disease — Metadata

| Property | Value |
|----------|-------|
| **Dataset Name** | Chronic Kidney Disease |
| **Source** | UCI Machine Learning Repository |
| **Original Contributor** | Dr. P. Soundarapandian, Apollo Hospitals, Karaikudi, Tamil Nadu, India |
| **Source URL** | https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease |
| **DOI** | 10.24432/C5G020 |
| **License** | CC BY 4.0 |
| **Expected Filename** | `chronic_kidney_disease_full.arff` (UCI) or `kidney_disease.csv` |
| **Expected External Directory** | `MEDINTEL_DATA_DIR/raw/kidney_disease/` |
| **Number of Rows** | 400 |
| **Number of Columns** | 25–26 (24 features + target, some versions include id) |
| **Target Column** | `classification` or `class` |
| **Target Encoding** | `ckd` = CKD (→ 1), `notckd` = Not CKD (→ 0) |

## Citation

Soundarapandian, P. & Rubini, L. (2015). Chronic Kidney Disease [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5G020

## Features

| # | Name | Full Name | Type |
|---|------|-----------|------|
| 1 | age | Age | Numeric |
| 2 | bp | Blood Pressure | Numeric |
| 3 | sg | Specific Gravity | Nominal |
| 4 | al | Albumin | Nominal |
| 5 | su | Sugar | Nominal |
| 6 | rbc | Red Blood Cells | Nominal |
| 7 | pc | Pus Cell | Nominal |
| 8 | pcc | Pus Cell Clumps | Nominal |
| 9 | ba | Bacteria | Nominal |
| 10 | bgr | Blood Glucose Random | Numeric |
| 11 | bu | Blood Urea | Numeric |
| 12 | sc | Serum Creatinine | Numeric |
| 13 | sod | Sodium | Numeric |
| 14 | pot | Potassium | Numeric |
| 15 | hemo | Hemoglobin | Numeric |
| 16 | pcv | Packed Cell Volume | Numeric |
| 17 | wc | White Blood Cell Count | Numeric |
| 18 | rc | Red Blood Cell Count | Numeric |
| 19 | htn | Hypertension | Nominal |
| 20 | dm | Diabetes Mellitus | Nominal |
| 21 | cad | Coronary Artery Disease | Nominal |
| 22 | appet | Appetite | Nominal |
| 23 | pe | Pedal Edema | Nominal |
| 24 | ane | Anemia | Nominal |

## Missing Values

Significant missing values across many columns. Encoded as `?`, NaN, or empty strings in various versions.

## Limitations

- Small sample (400 records)
- Single hospital in India
- Significant missing data requiring imputation
- Inconsistent text formatting (whitespace, tab characters)

## Planned Preprocessing

1. Strip whitespace from all text values
2. Normalize target to binary (ckd → 1, notckd → 0)
3. Normalize categorical values
4. Replace `?` with NaN
5. Convert numeric columns
6. Fill numeric NaN with median
7. Fill categorical NaN with mode
8. Drop `id` column if present
9. Remove exact duplicates
