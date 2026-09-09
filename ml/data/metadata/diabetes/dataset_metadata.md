# Pima Indians Diabetes Database — Metadata

| Property | Value |
|----------|-------|
| **Dataset Name** | Pima Indians Diabetes Database |
| **Original Source** | National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK) |
| **Verified Source URL** | https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database |
| **Alternative Source** | OpenML (Dataset ID: 37, https://www.openml.org/d/37) |
| **DOI** | Not verified from available sources / not assigned |
| **License** | Public Domain / CC0 / Open Data |
| **Expected Filename** | `dataset_37_diabetes.arff` (OpenML) or `diabetes.csv` (Kaggle) |
| **Expected External Directory** | `MEDINTEL_DATA_DIR/raw/diabetes/` |
| **Number of Rows** | 768 |
| **Number of Columns** | 9 (8 features + 1 target) |
| **Target Column** | `Outcome` |
| **Target Encoding** | 0 = No diabetes, 1 = Diabetes |

> **Note on UCI Dataset ID 529:**  
> UCI dataset 529 is "Early Stage Diabetes Risk Prediction" (symptom survey data), NOT the Pima Indians Diabetes Database. MedIntel AI strictly uses the classic Pima dataset from NIDDK.

## Citation

Smith, J.W., Everhart, J.E., Dickson, W.C., Knowler, W.C., & Johannes, R.S. (1988). Using the ADAP Learning Algorithm to Forecast the Onset of Diabetes Mellitus. In *Proceedings of the Symposium on Computer Applications and Medical Care* (pp. 261–265).

## Features

| # | Name | Type |
|---|------|------|
| 1 | Pregnancies | Integer |
| 2 | Glucose | Integer |
| 3 | BloodPressure | Integer |
| 4 | SkinThickness | Integer |
| 5 | Insulin | Integer |
| 6 | BMI | Float |
| 7 | DiabetesPedigreeFunction | Float |
| 8 | Age | Integer |

## Missing Values

No explicit NaN values, but physiologically implausible zeros exist in Glucose, BloodPressure, SkinThickness, Insulin, and BMI.

## Limitations

- All subjects are females of Pima Indian heritage, ≥21 years old
- From the Phoenix, Arizona area only
- Small sample (768 records)
- Not representative of diverse populations

## Planned Preprocessing

1. Replace implausible zeros with NaN
2. Fill NaN with column median
3. Validate target encoding
4. Remove exact duplicates
