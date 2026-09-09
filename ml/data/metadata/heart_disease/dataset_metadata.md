# UCI Heart Disease (Cleveland) — Metadata

| Property | Value |
|----------|-------|
| **Dataset Name** | Heart Disease (Cleveland subset, processed) |
| **Source** | UCI Machine Learning Repository |
| **Source URL** | https://archive.ics.uci.edu/dataset/45/heart+disease |
| **DOI** | 10.24432/C52P4X |
| **License** | CC BY 4.0 |
| **Expected Filename** | `processed.cleveland.data` (UCI) or `heart.csv` |
| **Expected External Directory** | `MEDINTEL_DATA_DIR/raw/heart_disease/` |
| **Number of Rows** | 303 |
| **Number of Columns** | 14 (13 features + 1 target) |
| **Target Column** | `target` (originally `num`) |
| **Target Encoding (Original)** | 0–4 (0 = no disease, 1–4 = disease severity) |
| **Target Encoding (Binary)** | 0 = absence, 1 = presence |

## Citation

Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1988). Heart Disease [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X

## Features

| # | Name | Description | Type |
|---|------|-------------|------|
| 1 | age | Age in years | Integer |
| 2 | sex | Sex (1=male, 0=female) | Binary |
| 3 | cp | Chest pain type (1–4) | Categorical |
| 4 | trestbps | Resting blood pressure (mm Hg) | Integer |
| 5 | chol | Serum cholesterol (mg/dl) | Integer |
| 6 | fbs | Fasting blood sugar > 120 mg/dl | Binary |
| 7 | restecg | Resting ECG results (0,1,2) | Categorical |
| 8 | thalach | Max heart rate achieved | Integer |
| 9 | exang | Exercise-induced angina | Binary |
| 10 | oldpeak | ST depression (exercise vs rest) | Float |
| 11 | slope | Slope of peak exercise ST segment | Categorical |
| 12 | ca | Major vessels colored by fluoroscopy (0–3) | Integer |
| 13 | thal | Thalassemia (3=normal, 6=fixed, 7=reversible) | Categorical |

## Missing Values

`ca` and `thal` may contain missing values (encoded as `?` in original UCI file).

## Limitations

- Small sample (303 records)
- Collected in the 1980s
- Cleveland clinic patients only

## Planned Preprocessing

1. Handle `?` missing values
2. Normalize target to binary (0 vs 1)
3. Convert numeric types
4. Remove exact duplicates
