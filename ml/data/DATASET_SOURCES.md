# MedIntel AI — Dataset Sources

> Phase 3: Data Collection & Preparation
>
> These exact three datasets will be used for the subsequent ML Model Development phase.

---

## 1. Pima Indians Diabetes Database

| Property | Value |
|----------|-------|
| **Dataset Name** | Pima Indians Diabetes Database |
| **Source Organization** | National Institute of Diabetes and Digestive and Kidney Diseases (NIDDK) |
| **Verified Accessible Sources** | Kaggle / OpenML (Dataset ID: 37) |
| **Kaggle URL** | https://www.kaggle.com/datasets/uciml/pima-indians-diabetes-database |
| **OpenML URL** | https://www.openml.org/d/37 |
| **DOI** | Not verified from available sources / not assigned |
| **License** | Public Domain / CC0 / Open Data |
| **Number of Records** | 768 |
| **Number of Features** | 8 predictor features + 1 target |
| **Target Column** | `Outcome` |
| **Target Encoding** | 0 = No diabetes, 1 = Diabetes |
| **Missing Values** | No explicit missing values, but physiologically implausible zeros exist in Glucose, BloodPressure, SkinThickness, Insulin, and BMI columns |

> **Important Disambiguation regarding UCI Dataset ID 529:**  
> UCI dataset ID 529 corresponds to "Early Stage Diabetes Risk Prediction Dataset", which is a distinct dataset with 520 instances based on symptom questionnaires (Polyuria, Polydipsia, etc.). It is NOT the Pima Indians Diabetes Database. MedIntel AI strictly uses the classic **Pima Indians Diabetes Database** from NIDDK, which contains diagnostic physiological measurements.

### Features

| # | Feature Name | Description | Type |
|---|-------------|-------------|------|
| 1 | Pregnancies | Number of times pregnant | Integer |
| 2 | Glucose | Plasma glucose concentration (2h oral glucose tolerance test) | Integer |
| 3 | BloodPressure | Diastolic blood pressure (mm Hg) | Integer |
| 4 | SkinThickness | Triceps skin fold thickness (mm) | Integer |
| 5 | Insulin | 2-hour serum insulin (mu U/ml) | Integer |
| 6 | BMI | Body mass index (weight in kg / height in m²) | Float |
| 7 | DiabetesPedigreeFunction | Diabetes pedigree function (family history score) | Float |
| 8 | Age | Age in years | Integer |

### Citation

Smith, J.W., Everhart, J.E., Dickson, W.C., Knowler, W.C., & Johannes, R.S. (1988). Using the ADAP Learning Algorithm to Forecast the Onset of Diabetes Mellitus. In *Proceedings of the Symposium on Computer Applications and Medical Care* (pp. 261–265). IEEE Computer Society Press.

### Known Limitations

- **Demographic limitation**: All subjects are females of Pima Indian heritage, at least 21 years old, from the Phoenix, Arizona area. Results may not generalize to other populations.
- **Implausible zeros**: Glucose, BloodPressure, SkinThickness, Insulin, and BMI contain zero values that are physiologically impossible and likely represent missing data.
- **Small sample size**: Only 768 records.
- **Single ethnicity**: Not representative of diverse populations.

### Suitability for This Project

This is the most widely used dataset for diabetes risk prediction in academic ML projects. It provides a clean binary classification task with well-understood features. Its limitations (demographic bias, implausible zeros) are well-documented and can be addressed during preprocessing.

---

## 2. UCI Heart Disease Dataset (Cleveland)

| Property | Value |
|----------|-------|
| **Dataset Name** | Heart Disease (Cleveland subset, processed) |
| **Source Organization** | UCI Machine Learning Repository |
| **Original Contributors** | Hungarian Institute of Cardiology (Andras Janosi, M.D.), University Hospital Zurich (William Steinbrunn, M.D.), University Hospital Basel (Matthias Pfisterer, M.D.), V.A. Medical Center Long Beach (Robert Detrano, M.D., Ph.D.) |
| **UCI URL** | https://archive.ics.uci.edu/dataset/45/heart+disease |
| **DOI** | 10.24432/C52P4X |
| **License** | CC BY 4.0 (as listed on UCI ML Repository) |
| **Number of Records** | 303 (Cleveland subset) |
| **Number of Features** | 13 predictor features + 1 target |
| **Target Column** | `num` (often renamed to `target`) |
| **Target Encoding (Original)** | Integer 0–4 (0 = no heart disease, 1–4 = presence with increasing severity) |
| **Target Encoding (Binary)** | 0 = absence, 1 = presence (values 1–4 mapped to 1) |
| **Missing Values** | `ca` and `thal` columns contain some missing values (encoded as `?` in the raw file) |

### Features

| # | Feature Name | Description | Type |
|---|-------------|-------------|------|
| 1 | age | Age in years | Integer |
| 2 | sex | Sex (1 = male, 0 = female) | Binary |
| 3 | cp | Chest pain type (1–4) | Categorical |
| 4 | trestbps | Resting blood pressure (mm Hg on admission) | Integer |
| 5 | chol | Serum cholesterol (mg/dl) | Integer |
| 6 | fbs | Fasting blood sugar > 120 mg/dl (1 = true, 0 = false) | Binary |
| 7 | restecg | Resting electrocardiographic results (0, 1, 2) | Categorical |
| 8 | thalach | Maximum heart rate achieved | Integer |
| 9 | exang | Exercise-induced angina (1 = yes, 0 = no) | Binary |
| 10 | oldpeak | ST depression induced by exercise relative to rest | Float |
| 11 | slope | Slope of peak exercise ST segment (1–3) | Categorical |
| 12 | ca | Number of major vessels colored by fluoroscopy (0–3) | Integer |
| 13 | thal | Thalassemia (3 = normal, 6 = fixed defect, 7 = reversible defect) | Categorical |

### Citation

Janosi, A., Steinbrunn, W., Pfisterer, M., & Detrano, R. (1988). Heart Disease [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C52P4X

Detrano, R., Janosi, A., Steinbrunn, W., Pfisterer, M., Schmid, J., Sandhu, S., Guppy, K., Lee, S., & Froelicher, V. (1989). International application of a new probability algorithm for the diagnosis of coronary artery disease. *American Journal of Cardiology*, 64(5), 304–310.

### Known Limitations

- **Small sample size**: Only 303 records in the Cleveland subset.
- **Missing values**: `ca` and `thal` columns have missing values.
- **Data age**: Collected in the 1980s; medical practices and diagnostics have evolved.
- **Geographic limitation**: Cleveland clinic patients; may not generalize universally.

### Suitability for This Project

The Cleveland processed dataset is the standard benchmark for heart disease prediction in ML. The binary classification task (presence vs. absence) is well-established. It has 13 clinically meaningful features and extensive academic literature for comparison.

---

## 3. UCI Chronic Kidney Disease Dataset

| Property | Value |
|----------|-------|
| **Dataset Name** | Chronic Kidney Disease |
| **Source Organization** | UCI Machine Learning Repository |
| **Original Contributors** | Dr. P. Soundarapandian, M.D., D.M. (Senior Consultant Nephrologist), Apollo Hospitals, Managiri, Madurai Main Road, Karaikudi, Tamil Nadu, India |
| **UCI URL** | https://archive.ics.uci.edu/dataset/336/chronic+kidney+disease |
| **DOI** | 10.24432/C5G020 |
| **License** | CC BY 4.0 (as listed on UCI ML Repository) |
| **Number of Records** | 400 |
| **Number of Features** | 24 predictor features + 1 target |
| **Target Column** | `class` |
| **Target Encoding** | `ckd` = Chronic Kidney Disease, `notckd` = Not CKD |
| **Missing Values** | Significant — many features have missing values across many rows |

### Features

| # | Feature Name | Full Name | Type |
|---|-------------|-----------|------|
| 1 | age | Age | Numeric |
| 2 | bp | Blood Pressure (mm/Hg) | Numeric |
| 3 | sg | Specific Gravity | Nominal (1.005, 1.010, 1.015, 1.020, 1.025) |
| 4 | al | Albumin | Nominal (0, 1, 2, 3, 4, 5) |
| 5 | su | Sugar | Nominal (0, 1, 2, 3, 4, 5) |
| 6 | rbc | Red Blood Cells | Nominal (normal, abnormal) |
| 7 | pc | Pus Cell | Nominal (normal, abnormal) |
| 8 | pcc | Pus Cell Clumps | Nominal (present, notpresent) |
| 9 | ba | Bacteria | Nominal (present, notpresent) |
| 10 | bgr | Blood Glucose Random (mgs/dl) | Numeric |
| 11 | bu | Blood Urea (mgs/dl) | Numeric |
| 12 | sc | Serum Creatinine (mgs/dl) | Numeric |
| 13 | sod | Sodium (mEq/L) | Numeric |
| 14 | pot | Potassium (mEq/L) | Numeric |
| 15 | hemo | Hemoglobin (gms) | Numeric |
| 16 | pcv | Packed Cell Volume | Numeric |
| 17 | wc | White Blood Cell Count (cells/cumm) | Numeric |
| 18 | rc | Red Blood Cell Count (millions/cmm) | Numeric |
| 19 | htn | Hypertension | Nominal (yes, no) |
| 20 | dm | Diabetes Mellitus | Nominal (yes, no) |
| 21 | cad | Coronary Artery Disease | Nominal (yes, no) |
| 22 | appet | Appetite | Nominal (good, poor) |
| 23 | pe | Pedal Edema | Nominal (yes, no) |
| 24 | ane | Anemia | Nominal (yes, no) |

### Citation

Soundarapandian, P. & Rubini, L. (2015). Chronic Kidney Disease [Dataset]. UCI Machine Learning Repository. https://doi.org/10.24432/C5G020

### Known Limitations

- **Small sample size**: Only 400 records.
- **Significant missing data**: Many features have substantial numbers of missing values.
- **Data quality**: Some textual values have inconsistent formatting (e.g., leading/trailing whitespace, tab characters, inconsistent yes/no encoding).
- **Geographic limitation**: Single hospital in Tamil Nadu, India.
- **Imbalanced classes**: Approximately 250 CKD vs 150 not-CKD.

### Suitability for This Project

This is the standard dataset for chronic kidney disease prediction in ML literature. It provides a realistic mix of numeric and categorical clinical features. The significant missing values and data quality issues make it an excellent test of real-world data preparation skills.

---

## Summary

| Dataset | Records | Features | Target | Source | DOI |
|---------|---------|----------|--------|--------|-----|
| Pima Indians Diabetes | 768 | 8 | Outcome (0/1) | NIDDK (Kaggle / OpenML) | Not assigned / N/A |
| Heart Disease (Cleveland) | 303 | 13 | num → binary (0/1) | UCI | 10.24432/C52P4X |
| Chronic Kidney Disease | 400 | 24 | class (ckd/notckd) | UCI | 10.24432/C5G020 |

**These exact three datasets will be used for the subsequent ML Model Development phase.**
