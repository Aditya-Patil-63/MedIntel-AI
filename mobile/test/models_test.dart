import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/extraction/document_extraction_result.dart';
import 'package:medintel_mobile/models/extraction/page_extraction.dart';
import 'package:medintel_mobile/models/genai/genai_explain_request.dart';
import 'package:medintel_mobile/models/genai/genai_explain_response.dart';
import 'package:medintel_mobile/models/genai/genai_status_response.dart';
import 'package:medintel_mobile/models/ml_risk/diabetes_risk_request.dart';
import 'package:medintel_mobile/models/ml_risk/heart_disease_risk_request.dart';
import 'package:medintel_mobile/models/ml_risk/kidney_disease_risk_request.dart';
import 'package:medintel_mobile/models/ml_risk/ml_status_response.dart';
import 'package:medintel_mobile/models/ml_risk/risk_prediction_response.dart';
import 'package:medintel_mobile/models/reference/analysis_result.dart';
import 'package:medintel_mobile/models/reference/batch_analysis.dart';
import 'package:medintel_mobile/models/reference/measurement_input.dart';
import 'package:medintel_mobile/models/reference/parse_and_analyze.dart';
import 'package:medintel_mobile/models/reference/patient_context.dart';

void main() {
  group('Extraction Models', () {
    test('PageExtraction fromJson and toJson round-trip', () {
      final json = {
        'page_number': 1,
        'text': 'Hemoglobin 14.5 g/dL',
        'confidence': 0.95,
        'char_count': 22,
        'word_count': 3,
      };
      final model = PageExtraction.fromJson(json);
      expect(model.pageNumber, 1);
      expect(model.text, 'Hemoglobin 14.5 g/dL');
      expect(model.confidence, 0.95);
      expect(model.toJson(), json);
    });

    test('DocumentExtractionResult deserialization with pages and defaults', () {
      final json = {
        'success': true,
        'filename': 'cbc_report.pdf',
        'source_type': 'digital_pdf',
        'extractor': 'pdfplumber',
        'total_pages': 1,
        'pages': [
          {
            'page_number': 1,
            'text': 'WBC: 6.5',
            'confidence': 1.0,
            'char_count': 8,
            'word_count': 2,
          }
        ],
        'full_text': 'WBC: 6.5',
        'confidence': 1.0,
        'warnings': ['Minor noise'],
        'errors': [],
        'disclaimer':
            'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
      };
      final model = DocumentExtractionResult.fromJson(json);
      expect(model.success, true);
      expect(model.sourceType, SourceType.digitalPdf);
      expect(model.pages.length, 1);
      expect(model.warnings, contains('Minor noise'));
      expect(model.disclaimer, contains('not a medical diagnosis'));
    });
  });

  group('Reference Analysis Models', () {
    test('MeasurementInput handles verification status and context', () {
      final item = MeasurementInput(
        testName: 'FBS',
        value: 110.0,
        unit: 'mg/dL',
        isUserVerified: true,
        context: const PatientContext(age: 45.0, sex: 'M'),
      );
      final json = item.toJson();
      expect(json['test_name'], 'FBS');
      expect(json['value'], 110.0);
      expect(json['is_user_verified'], true);
      expect(json['context']['age'], 45.0);

      final deserialized = MeasurementInput.fromJson(json);
      expect(deserialized, equals(item));
    });

    test('AnalysisResult maps classification enum correctly', () {
      final json = {
        'original_test_name': 'Glucose Fasting',
        'canonical_name': 'Fasting Blood Glucose',
        'numeric_value': 140.0,
        'unit': 'mg/dL',
        'classification': 'HIGH',
        'analysis_status': 'SUCCESS',
        'reference_range': {
          'canonical_name': 'Fasting Blood Glucose',
          'unit': 'mg/dL',
          'normal_low': 70.0,
          'normal_high': 99.0,
          'critical_high': 300.0,
          'source': 'ADA 2024 Standards of Care',
          'reference_type': 'FASTING_REFERENCE',
          'verification_status': 'VERIFIED',
        },
        'is_user_verified': true,
        'warnings': [],
        'disclaimer':
            'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
      };

      final result = AnalysisResult.fromJson(json);
      expect(result.classification, AnalyteClassification.high);
      expect(result.referenceRange?.normalHigh, 99.0);
      expect(result.referenceRange?.source, contains('ADA'));
    });

    test('BatchAnalysisRequest and Response serialization', () {
      const response = BatchAnalysisResponse(
        success: true,
        totalSubmitted: 1,
        totalClassified: 1,
        results: [
          AnalysisResult(
            originalTestName: 'Hemoglobin',
            classification: AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
          ),
        ],
      );
      final json = response.toJson();
      expect(json['total_submitted'], 1);
      final parsed = BatchAnalysisResponse.fromJson(json);
      expect(parsed.results.first.classification, AnalyteClassification.normal);
    });

    test('ParseAndAnalyzeRequest and Response serialization', () {
      final req = const ParseAndAnalyzeRequest(
        text: 'Hemoglobin: 13.5 g/dL',
        isUserVerified: false,
      ).toJson();
      expect(req['text'], 'Hemoglobin: 13.5 g/dL');
      expect(req['is_user_verified'], false);
    });
  });

  group('ML Risk Models', () {
    test('DiabetesRiskRequest serialization preserves all 8 features', () {
      const req = DiabetesRiskRequest(
        pregnancies: 2,
        glucose: 130,
        bloodPressure: 78,
        skinThickness: 25,
        insulin: 105,
        bmi: 28.5,
        diabetesPedigreeFunction: 0.45,
        age: 38,
        isUserVerified: true,
      );
      final json = req.toJson();
      expect(json['Pregnancies'], 2.0);
      expect(json['Glucose'], 130.0);
      expect(json['BMI'], 28.5);
      expect(json['is_user_verified'], true);

      final fromJson = DiabetesRiskRequest.fromJson(json);
      expect(fromJson, equals(req));
    });

    test('HeartDiseaseRiskRequest serialization preserves Cleveland features', () {
      const req = HeartDiseaseRiskRequest(
        age: 55,
        sex: 1,
        cp: 2,
        trestbps: 140,
        chol: 240,
        fbs: 0,
        restecg: 1,
        thalach: 150,
        exang: 0,
        oldpeak: 1.5,
        slope: 2,
        ca: 0,
        thal: 3,
      );
      final json = req.toJson();
      expect(json['age'], 55.0);
      expect(json['sex'], 1.0);
      expect(json['chol'], 240.0);
    });

    test('KidneyDiseaseRiskRequest preserves numerical and categorical features', () {
      const req = KidneyDiseaseRiskRequest(
        age: 48,
        bp: 80,
        bgr: 120,
        bu: 36,
        sc: 1.2,
        rbc: 'normal',
        htn: 'yes',
        dm: 'no',
      );
      final json = req.toJson();
      expect(json['age'], 48.0);
      expect(json['rbc'], 'normal');
      expect(json['htn'], 'yes');
      expect(json['dm'], 'no');
    });

    test('RiskPredictionResponse deserialization maps riskBand correctly', () {
      final json = {
        'condition': 'diabetes',
        'status': 'OK',
        'risk_probability': 0.75,
        'risk_band': 'ELEVATED',
        'model_name': 'random_forest_v1',
        'model_version': '2026-09-09',
        'supplied_features_count': 8,
        'required_features_count': 8,
        'missing_features': [],
        'disclaimer': 'ML Risk Disclaimer',
      };
      final response = RiskPredictionResponse.fromJson(json);
      expect(response.riskBand, RiskBand.elevated);
      expect(response.riskProbability, 0.75);
      expect(response.condition, 'diabetes');
    });

    test('MLStatusResponse maps models dictionary correctly', () {
      final json = {
        'status': 'OK',
        'models': {
          'diabetes': {
            'available': true,
            'model_name': 'diabetes_rf',
            'integrity_verified': true,
          },
          'heart_disease': {
            'available': true,
            'model_name': 'heart_lr',
            'integrity_verified': true,
          },
        },
      };
      final status = MLStatusResponse.fromJson(json);
      expect(status.status, 'OK');
      expect(status.models['diabetes']?.available, true);
      expect(status.models['heart_disease']?.modelName, 'heart_lr');
    });
  });

  group('GenAI Explanation Models', () {
    test('GenAIExplainRequest serialization preserves safety fields', () {
      const request = GenAIExplainRequest(
        isUserVerified: true,
        patientAge: 52,
        patientSex: 'M',
        language: SupportedLanguage.hindi,
        detailLevel: DetailLevel.detailed,
        analytes: [
          VerifiedAnalyteSummary(
            testName: 'FBS',
            value: 126,
            unit: 'mg/dL',
            classification: AnalyteClassification.high,
          ),
        ],
        mlRisks: [
          MLRiskSummary(
            condition: 'diabetes',
            riskProbability: 0.62,
            riskBand: RiskBand.moderate,
          ),
        ],
      );

      final json = request.toJson();
      expect(json['is_user_verified'], true);
      expect(json['language'], 'hi');
      expect(json['detail_level'], 'detailed');
      expect(json['analytes'][0]['classification'], 'HIGH');
      expect(json['ml_risks'][0]['risk_band'], 'MODERATE');
    });

    test('GenAIExplainResponse deserializes full clinical explanation payload', () {
      final json = {
        'status': 'SUCCESS',
        'language': 'en',
        'model_provider': 'mock',
        'model_name': 'mock-v1',
        'explanation': {
          'summary': 'Your blood glucose is elevated.',
          'findings': [
            {
              'analyte_name': 'FBS',
              'observed_value': '126 mg/dL',
              'classification': 'HIGH',
              'plain_language_meaning': 'Indicates blood sugar level after fasting.',
            }
          ],
          'risk_explanations': [
            {
              'condition': 'diabetes',
              'model_probability': 0.62,
              'risk_band': 'MODERATE',
              'plain_language_explanation': 'Moderate probability indicator.',
            }
          ],
          'follow_up_guidance': ['Discuss testing HbA1c with doctor.'],
          'recommended_questions_for_doctor': ['Should I repeat this test?'],
        },
        'disclaimer': 'GenAI Educational Disclaimer',
        'generated_at': '2026-09-10T12:00:00Z',
      };

      final response = GenAIExplainResponse.fromJson(json);
      expect(response.status, GenAIStatus.success);
      expect(response.modelProvider, 'mock');
      expect(response.explanation?.findings.length, 1);
      expect(response.explanation?.findings.first.classification, 'HIGH');
      expect(response.explanation?.recommendedQuestionsForDoctor.first,
          contains('repeat this test'));
    });

    test('GenAIStatusResponse maps status fields', () {
      final json = {
        'status': 'OK',
        'provider': 'gemini',
        'model': 'gemini-3.8-flash',
        'available': true,
        'mode': 'cloud_api',
        'network_required': true,
      };
      final status = GenAIStatusResponse.fromJson(json);
      expect(status.provider, 'gemini');
      expect(status.model, 'gemini-3.8-flash');
      expect(status.available, true);
    });
  });
}
