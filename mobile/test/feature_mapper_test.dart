import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/analysis/verified_snapshot.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/ml_risk/risk_prediction_response.dart';
import 'package:medintel_mobile/models/reference/analysis_result.dart';
import 'package:medintel_mobile/models/reference/batch_analysis.dart';
import 'package:medintel_mobile/models/reference/editable_measurement.dart';
import 'package:medintel_mobile/models/reference/patient_context.dart';
import 'package:medintel_mobile/services/feature_mapper.dart';

void main() {
  group('FeatureMapper — Deterministic Mapping & Null Preservation', () {
    test('toBatchAnalysisRequest preserves measurements and forces is_user_verified=true', () {
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Glucose',
            testName: 'Fasting Blood Sugar',
            value: 110.0,
            unit: 'mg/dL',
          ),
          EditableMeasurement(
            id: '2',
            originalTestName: 'Hemoglobin',
            testName: 'Hemoglobin',
            value: 14.2,
            unit: 'g/dL',
          ),
        ],
        patientContext: const PatientContext(age: 45, sex: 'M'),
        isVerified: true,
      );

      final req = FeatureMapper.toBatchAnalysisRequest(snapshot);

      expect(req.reportId, isNull);
      expect(req.persist, false);
      expect(req.patientContext?.age, 45.0);
      expect(req.patientContext?.sex, 'M');
      expect(req.measurements.length, 2);
      expect(req.measurements[0].testName, 'Fasting Blood Sugar');
      expect(req.measurements[0].value, 110.0);
      expect(req.measurements[0].isUserVerified, true);
      expect(req.measurements[1].testName, 'Hemoglobin');
      expect(req.measurements[1].isUserVerified, true);
    });

    test('toDiabetesRiskRequest maps known aliases and preserves null for missing features', () {
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Glucose',
            testName: 'Blood Glucose',
            value: 125.0,
          ),
          EditableMeasurement(
            id: '2',
            originalTestName: 'BMI',
            testName: 'Body Mass Index',
            value: 28.5,
          ),
        ],
        patientContext: const PatientContext(age: 52, sex: 'F'),
        isVerified: true,
      );

      final req = FeatureMapper.toDiabetesRiskRequest(snapshot);

      expect(req.glucose, 125.0);
      expect(req.bmi, 28.5);
      expect(req.age, 52.0);
      // Strictly preserves null — NO client-side defaults or imputation
      expect(req.pregnancies, isNull);
      expect(req.bloodPressure, isNull);
      expect(req.skinThickness, isNull);
      expect(req.insulin, isNull);
      expect(req.diabetesPedigreeFunction, isNull);
      expect(req.isUserVerified, true);
    });

    test('toHeartDiseaseRiskRequest encodes sex (M=1.0, F=0.0) and preserves nulls', () {
      final snapshotMale = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Cholesterol',
            testName: 'Total Cholesterol',
            value: 220.0,
          ),
          EditableMeasurement(
            id: '2',
            originalTestName: 'Blood Pressure',
            testName: 'Resting Blood Pressure',
            value: 135.0,
          ),
        ],
        patientContext: const PatientContext(age: 60, sex: 'M'),
        isVerified: true,
      );

      final reqMale = FeatureMapper.toHeartDiseaseRiskRequest(snapshotMale);
      expect(reqMale.sex, 1.0);
      expect(reqMale.age, 60.0);
      expect(reqMale.chol, 220.0);
      expect(reqMale.trestbps, 135.0);
      expect(reqMale.thalach, isNull);
      expect(reqMale.oldpeak, isNull);
      expect(reqMale.cp, isNull);

      final snapshotFemale = VerifiedSnapshot(
        measurements: const [],
        patientContext: const PatientContext(age: 45, sex: 'F'),
        isVerified: true,
      );
      final reqFemale = FeatureMapper.toHeartDiseaseRiskRequest(snapshotFemale);
      expect(reqFemale.sex, 0.0);

      final snapshotUnspecified = VerifiedSnapshot(
        measurements: const [],
        patientContext: const PatientContext(age: 45, sex: null),
        isVerified: true,
      );
      final reqUnspecified = FeatureMapper.toHeartDiseaseRiskRequest(snapshotUnspecified);
      expect(reqUnspecified.sex, isNull);
    });

    test('toKidneyDiseaseRiskRequest maps CKD features and keeps missing features null', () {
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Creatinine',
            testName: 'Serum Creatinine',
            value: 1.4,
          ),
          EditableMeasurement(
            id: '2',
            originalTestName: 'Blood Urea',
            testName: 'Blood Urea',
            value: 45.0,
          ),
          EditableMeasurement(
            id: '3',
            originalTestName: 'Hemoglobin',
            testName: 'Hemoglobin',
            value: 11.2,
          ),
        ],
        patientContext: const PatientContext(age: 55),
        isVerified: true,
      );

      final req = FeatureMapper.toKidneyDiseaseRiskRequest(snapshot);
      expect(req.sc, 1.4);
      expect(req.bu, 45.0);
      expect(req.hemo, 11.2);
      expect(req.age, 55.0);
      expect(req.bp, isNull);
      expect(req.sg, isNull);
      expect(req.al, isNull);
      expect(req.sod, isNull);
      expect(req.pot, isNull);
      expect(req.isUserVerified, true);
    });

    test('toMLRiskSummaries filters out INSUFFICIENT_FEATURES or null probability', () {
      final mlResponses = [
        const RiskPredictionResponse(
          condition: 'diabetes',
          status: 'OK',
          riskProbability: 0.65,
          riskBand: RiskBand.moderate,
        ),
        const RiskPredictionResponse(
          condition: 'heart_disease',
          status: 'INSUFFICIENT_FEATURES',
          riskProbability: null,
          riskBand: null,
          missingFeatures: ['thalach', 'chol'],
        ),
        const RiskPredictionResponse(
          condition: 'kidney_disease',
          status: 'OK',
          riskProbability: 0.22,
          riskBand: RiskBand.low,
        ),
      ];

      final summaries = FeatureMapper.toMLRiskSummaries(mlResponses);

      // Only the 2 successful ones are included; INSUFFICIENT_FEATURES is excluded
      expect(summaries.length, 2);
      expect(summaries[0].condition, 'diabetes');
      expect(summaries[0].riskProbability, 0.65);
      expect(summaries[0].riskBand, RiskBand.moderate);
      expect(summaries[1].condition, 'kidney_disease');
      expect(summaries[1].riskProbability, 0.22);
      expect(summaries[1].riskBand, RiskBand.low);
    });

    test('toVerifiedAnalyteSummaries extracts evaluation fields for GenAI', () {
      const batchResp = BatchAnalysisResponse(
        totalSubmitted: 1,
        totalClassified: 1,
        results: [
          AnalysisResult(
            originalTestName: 'FBS',
            canonicalName: 'Fasting Blood Sugar',
            numericValue: 145.0,
            unit: 'mg/dL',
            classification: AnalyteClassification.high,
            analysisStatus: 'SUCCESS',
            warnings: ['Elevated fasting glucose'],
          ),
        ],
      );

      final summaries = FeatureMapper.toVerifiedAnalyteSummaries(batchResp);

      expect(summaries.length, 1);
      expect(summaries[0].testName, 'FBS');
      expect(summaries[0].canonicalName, 'Fasting Blood Sugar');
      expect(summaries[0].value, 145.0);
      expect(summaries[0].classification, AnalyteClassification.high);
      expect(summaries[0].warnings, contains('Elevated fasting glucose'));
    });
  });
}
