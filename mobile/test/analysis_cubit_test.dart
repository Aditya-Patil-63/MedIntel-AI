import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/core/errors/api_exception.dart';
import 'package:medintel_mobile/models/analysis/verified_snapshot.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/genai/genai_explain_request.dart';
import 'package:medintel_mobile/models/genai/genai_explain_response.dart';
import 'package:medintel_mobile/models/ml_risk/diabetes_risk_request.dart';
import 'package:medintel_mobile/models/ml_risk/heart_disease_risk_request.dart';
import 'package:medintel_mobile/models/ml_risk/kidney_disease_risk_request.dart';
import 'package:medintel_mobile/models/ml_risk/risk_prediction_response.dart';
import 'package:medintel_mobile/models/reference/analysis_result.dart';
import 'package:medintel_mobile/models/reference/batch_analysis.dart';
import 'package:medintel_mobile/models/reference/editable_measurement.dart';
import 'package:medintel_mobile/models/reference/patient_context.dart';
import 'package:medintel_mobile/repositories/medical_repository.dart';
import 'package:medintel_mobile/services/api_service.dart';
import 'package:medintel_mobile/state/analysis/analysis_cubit.dart';
import 'package:medintel_mobile/state/analysis/analysis_state.dart';

class MockAnalysisApiService implements ApiService {
  bool failGenAi = false;
  int genAiStatusCode = 503;
  int genAiCallCount = 0;
  SupportedLanguage lastLanguage = SupportedLanguage.english;

  @override
  Future<BatchAnalysisResponse> analyzeBatch(BatchAnalysisRequest request) async {
    return BatchAnalysisResponse(
      totalSubmitted: request.measurements.length,
      totalClassified: request.measurements.length,
      results: [
        for (final m in request.measurements)
          AnalysisResult(
            originalTestName: m.testName,
            canonicalName: m.testName,
            numericValue: m.value,
            unit: m.unit,
            classification: AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
          ),
      ],
    );
  }

  @override
  Future<RiskPredictionResponse> predictDiabetesRisk(DiabetesRiskRequest request) async {
    return const RiskPredictionResponse(
      condition: 'diabetes',
      status: 'OK',
      riskProbability: 0.28,
      riskBand: RiskBand.low,
    );
  }

  @override
  Future<RiskPredictionResponse> predictHeartRisk(HeartDiseaseRiskRequest request) async {
    return const RiskPredictionResponse(
      condition: 'heart_disease',
      status: 'INSUFFICIENT_FEATURES',
      riskProbability: null,
      riskBand: null,
      missingFeatures: ['chol', 'trestbps'],
    );
  }

  @override
  Future<RiskPredictionResponse> predictKidneyRisk(KidneyDiseaseRiskRequest request) async {
    return const RiskPredictionResponse(
      condition: 'kidney_disease',
      status: 'OK',
      riskProbability: 0.15,
      riskBand: RiskBand.low,
    );
  }

  @override
  Future<GenAIExplainResponse> explainFindings(GenAIExplainRequest request) async {
    genAiCallCount++;
    lastLanguage = request.language;

    if (failGenAi) {
      throw ApiException(
        statusCode: genAiStatusCode,
        message: 'AI service temporarily unavailable (HTTP $genAiStatusCode)',
      );
    }

    return GenAIExplainResponse(
      status: GenAIStatus.success,
      language: request.language,
      explanation: const GenAIExplanationPayload(
        summary: 'Patient laboratory values are largely within normal limits.',
        findings: [
          AnalyteExplanationItem(
            analyteName: 'Glucose',
            observedValue: '98.0 mg/dL',
            classification: 'NORMAL',
            plainLanguageMeaning: 'Blood sugar is healthy.',
          ),
        ],
        followUpGuidance: ['Routine annual followup'],
        recommendedQuestionsForDoctor: ['Routine annual followup'],
      ),
      modelProvider: 'gemini',
      generatedAt: '2026-09-10T12:00:00Z',
    );
  }

  // Stubs for unused methods
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  late MockAnalysisApiService mockApi;
  late MedicalRepository repository;
  late AnalysisCubit cubit;

  setUp(() {
    mockApi = MockAnalysisApiService();
    repository = MedicalRepository(apiService: mockApi);
    cubit = AnalysisCubit(repository: repository);
  });

  tearDown(() {
    cubit.close();
  });

  group('AnalysisCubit — Full Pipeline Execution', () {
    test('rejects unverified snapshot with client safeguard failure', () async {
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'FBS',
            testName: 'FBS',
            value: 95.0,
          ),
        ],
        patientContext: const PatientContext(),
        isVerified: false,
      );

      await cubit.runFullAnalysis(snapshot);

      expect(cubit.state.status, AnalysisStatus.failure);
      expect(cubit.state.generalError, contains('must be confirmed and verified'));
      expect(cubit.state.referenceAnalysis, isNull);
    });

    test('runs reference, ML, and GenAI in full analysis', () async {
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Glucose',
            testName: 'Blood Glucose',
            value: 98.0,
          ),
        ],
        patientContext: const PatientContext(age: 40, sex: 'M'),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);

      expect(cubit.state.status, AnalysisStatus.success);
      expect(cubit.state.referenceAnalysis, isNotNull);
      expect(cubit.state.referenceAnalysis!.results.length, 1);

      // Diabetes returned OK with probability
      expect(cubit.state.diabetesRisk!.status, 'OK');
      expect(cubit.state.diabetesRisk!.riskProbability, 0.28);

      // Heart returned INSUFFICIENT_FEATURES
      expect(cubit.state.heartRisk!.status, 'INSUFFICIENT_FEATURES');
      expect(cubit.state.heartRisk!.missingFeatures, contains('chol'));

      // Kidney returned OK
      expect(cubit.state.kidneyRisk!.status, 'OK');

      // GenAI succeeded
      expect(cubit.state.genAiExplanation, isNotNull);
      expect(cubit.state.genAiExplanation!.explanation?.summary, contains('largely within normal limits'));
      expect(cubit.state.genAiError, isNull);
    });

    test('degrades gracefully when GenAI encounters HTTP 503 while preserving reference and ML results', () async {
      mockApi.failGenAi = true;
      mockApi.genAiStatusCode = 503;

      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Glucose',
            testName: 'Blood Glucose',
            value: 98.0,
          ),
        ],
        patientContext: const PatientContext(age: 40, sex: 'M'),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);

      // Overall status is still success because reference and ML succeeded
      expect(cubit.state.status, AnalysisStatus.success);
      expect(cubit.state.referenceAnalysis, isNotNull);
      expect(cubit.state.diabetesRisk, isNotNull);
      // GenAI failed gracefully
      expect(cubit.state.genAiExplanation, isNull);
      expect(cubit.state.genAiError, contains('unavailable'));

      // Retry GenAI after service recovers
      mockApi.failGenAi = false;
      await cubit.retryGenAI();

      expect(cubit.state.genAiExplanation, isNotNull);
      expect(cubit.state.genAiError, isNull);
    });

    test('changeLanguage re-invokes only GenAI without re-running reference or ML analysis', () async {
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Glucose',
            testName: 'Blood Glucose',
            value: 98.0,
          ),
        ],
        patientContext: const PatientContext(age: 40, sex: 'M'),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);
      expect(mockApi.genAiCallCount, 1);
      expect(mockApi.lastLanguage, SupportedLanguage.english);

      // Switch language to Hindi
      await cubit.changeLanguage(SupportedLanguage.hindi);

      expect(mockApi.genAiCallCount, 2);
      expect(mockApi.lastLanguage, SupportedLanguage.hindi);
      expect(cubit.state.selectedLanguage, SupportedLanguage.hindi);
      // Reference and ML results remain intact
      expect(cubit.state.referenceAnalysis, isNotNull);
      expect(cubit.state.diabetesRisk, isNotNull);
    });

    test('invalidate resets state to initial', () async {
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'Glucose',
            testName: 'Blood Glucose',
            value: 98.0,
          ),
        ],
        patientContext: const PatientContext(age: 40, sex: 'M'),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);
      expect(cubit.state.hasResults, true);

      cubit.invalidate();
      expect(cubit.state.status, AnalysisStatus.initial);
      expect(cubit.state.hasResults, false);
      expect(cubit.state.snapshot, isNull);
    });
  });
}
