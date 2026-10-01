# MedIntel AI — End-User Manual & Application Guide

> **Intelligent Medical Report Analyzer Using Machine Learning and Generative AI**  
> Comprehensive user guide for patients, caregivers, and health workers.

---

## 1. Welcome to MedIntel AI

MedIntel AI is an easy-to-use mobile application designed to help you understand your medical lab reports and doctor prescriptions. It reads your reports, extracts your lab values, explains what they mean in plain language, calculates disease risk indicators, and provides explanations in your preferred language (**English, Hindi, Marathi, or Gujarati**).

> [!IMPORTANT]
> **Safety Notice & Disclaimer**:  
> MedIntel AI is an educational and informational tool. **It does NOT provide medical diagnoses or prescribe medications.** Always consult a qualified physician or healthcare provider regarding any health condition or before making medical decisions.

---

## 2. Key Features at a Glance

- 📄 **Multi-Format Ingestion**: Upload native PDF reports or snap photos of printed reports and handwritten prescriptions.
- ✏️ **User Verification Safety Gate**: You always review, correct, or approve test values before any analysis is run.
- 📊 **Clear Reference Range Results**: See whether your test values fall within Normal, Low, High, or Critical ranges based on official medical standards (ADA, WHO, Mayo Clinic).
- 🎯 **Statistical Risk Indicators**: View risk screening scores for Diabetes, Heart Disease, and Kidney Disease.
- 🗣️ **Plain-Language Explanations**: Understand complex medical terms in simple, jargon-free language.
- 🌐 **Multilingual Support**: Read summaries and questions for your doctor in English, Hindi (हिंदी), Marathi (मराठी), or Gujarati (ગુજરાતી).
- 🕒 **Report History & Export**: Access previously analyzed reports anytime and export them for your doctor visits.

---

## 3. Step-by-Step User Workflow

### Step 1: Uploading or Capturing a Report

1. Open the MedIntel AI app on your mobile device.
2. On the **Home Screen**, choose your preferred upload method:
   - **Take Photo**: Uses your device camera to photograph a printed lab report or handwritten prescription. Make sure lighting is even and text is in focus.
   - **Upload Image**: Choose a JPEG or PNG photo of a medical report from your gallery.
   - **Upload PDF**: Select a digital PDF lab report from your phone's file storage (up to 10 MB).
3. Tap **Upload & Extract**. The app will extract all recognized test names and numerical values.

```
   ┌─────────────────────────────────────────────────────────┐
   │                   MedIntel AI Upload                    │
   ├─────────────────────────────────────────────────────────┤
   │                                                         │
   │   [ 📷 Camera ]      [ 🖼️ Gallery ]      [ 📄 PDF ]      │
   │                                                         │
   │   File Selected: adult_routine_panel.pdf (142 KB)       │
   │                                                         │
   │                 [ EXTRACT REPORT DATA ]                 │
   └─────────────────────────────────────────────────────────┘
```

---

### Step 2: The User Verification Gate (Confirming Your Data)

MedIntel AI will never analyze your data without your confirmation. After extraction, you will be taken to the **Verification Screen**:

1. Review each extracted test name, measured value, and unit of measurement.
2. If any value was misread (for example, if "12.0" was read as "120"):
   - Tap the **Edit (pencil)** icon next to that test.
   - Type in the correct value from your physical report.
   - Tap **Save**.
3. If an extra test was detected by mistake, tap the **Delete (trash)** icon to remove it.
4. If a test from your paper report is missing, tap **+ Add Test** at the bottom to enter it manually.
5. Once all values match your original physical document, tap **Confirm & Analyze**.

> [!TIP]
> Always double-check decimal points and units (e.g. `mg/dL` vs `g/dL`) during verification to ensure maximum analysis accuracy.

---

### Step 3: Reading Your Lab Results (Reference Ranges)

Once verified, the app evaluates your results against authoritative clinical standards:

| Status Badge | Meaning | Recommended Action |
|:---:|---|---|
| 🟢 **NORMAL** | Value falls within standard healthy reference limits. | Maintain healthy lifestyle habits; continue routine checkups. |
| 🟡 **HIGH** | Value is higher than typical healthy reference limits. | Discuss with your doctor at your next scheduled appointment. |
| 🟡 **LOW** | Value is lower than typical healthy reference limits. | Discuss with your doctor at your next scheduled appointment. |
| 🔴 **CRITICAL ALERT** | Value is dangerously out of range and may require immediate care. | **Contact your healthcare provider or seek urgent medical attention promptly.** |

---

### Step 4: Understanding Disease Risk Indicators

Below your lab values, MedIntel AI displays statistical risk screening indicators for three chronic conditions:
- **Diabetes Risk**
- **Heart Disease Risk**
- **Chronic Kidney Disease Risk**

#### How to Interpret Risk Scores:
- **Low Risk (Green)**: Your values do not show significant patterns associated with elevated risk in medical datasets.
- **Moderate Risk (Yellow)**: Some markers (such as borderline glucose, blood pressure, or cholesterol) indicate a need for preventive lifestyle discussion.
- **Elevated / High Risk (Red)**: Multiple markers suggest elevated risk. This is **NOT a diagnosis**, but an indicator to seek clinical screening.

---

### Step 5: Reading Your Plain-Language Summary

The Generative AI service creates an easy-to-read educational summary that breaks down:
1. **Summary Overview**: What the overall lab panel reflects about your general metabolic and organ function.
2. **What Each Test Does**: Explanations of complex terms (e.g., explaining that *Creatinine* is a natural waste product filtered by healthy kidneys).
3. **Questions to Ask Your Doctor**: A personalized list of recommended questions you can take to your physician appointment.
4. **General Lifestyle Pointers**: Balanced nutrition, hydration, and exercise reminders.

---

### Step 6: Changing the Explanation Language

You can read your health summary in any of 4 languages at any time:
1. Tap the **Language Dropdown** at the top right of the Results Screen.
2. Select:
   - **English**
   - **हिंदी (Hindi)**
   - **मराठी (Marathi)**
   - **ગુજરાતી (Gujarati)**
3. The summary and doctor questions will update in real time while keeping all medical numbers and units strictly identical.

---

### Step 7: Viewing History & Exporting Reports

1. From the Home Screen or Bottom Navigation Bar, tap **History**.
2. Tap on any past report to view the full verified values, reference analysis, risk scores, and summary.
3. Tap **Export / Print Summary** to generate a clean, printable PDF report to share with your family or physician.

---

## 4. Emergency Protocols: Critical Values Notice

If any test in your report triggers a red **CRITICAL ALERT** badge:
- **Do NOT panic.**
- **Do NOT self-medicate or alter your prescriptions.**
- **Contact a doctor, clinic, or emergency medical service immediately.**

Extreme values such as very low potassium (< 2.8 mEq/L), severe anemia (Hemoglobin < 7 g/dL), or extreme blood glucose (> 400 mg/dL) require prompt clinical evaluation.

---

## 5. Frequently Asked Questions (FAQ)

### Q1: Is MedIntel AI a substitute for my doctor?
**No.** MedIntel AI is designed to help you become an informed patient so you can have better, more productive discussions with your doctor. It cannot diagnose illnesses or prescribe medicines.

### Q2: What if the app misreads my handwritten prescription?
Handwriting can vary greatly in legibility. This is why MedIntel AI requires the **User Verification Gate**. You must always confirm the extracted text and numbers against the original prescription before analysis.

### Q3: Is my medical data kept private?
Yes. MedIntel AI does not sell or share your data. Processing is performed locally or within secure server containers with strict data boundary protections.

### Q4: Why does a risk model show "Insufficient Information"?
If your lab report only includes blood sugar, the Heart Disease and Kidney Disease models will safely decline to guess rather than making up numbers. They only calculate a risk score when all required biomarkers are present.

### Q5: Can I use MedIntel AI offline?
Yes! The reference range engine and local mock explanation service function completely offline without internet connectivity.
