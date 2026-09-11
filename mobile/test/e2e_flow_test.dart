import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/app.dart';
import 'package:medintel_mobile/models/analysis/verified_snapshot.dart';
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
import 'package:medintel_mobile/models/reference/editable_measurement.dart';
import 'package:medintel_mobile/models/reference/parse_and_analyze.dart';
import 'package:medintel_mobile/models/reference/patient_context.dart';
import 'package:medintel_mobile/models/reference/reference_range_summary.dart';
import 'package:medintel_mobile/repositories/medical_repository.dart';
import 'package:medintel_mobile/screens/history/history_detail_screen.dart';
import 'package:medintel_mobile/screens/history/history_screen.dart';
import 'package:medintel_mobile/screens/home/home_screen.dart';
import 'package:medintel_mobile/screens/results/results_screen.dart';
import 'package:medintel_mobile/screens/upload/upload_screen.dart';
import 'package:medintel_mobile/screens/verification/verification_screen.dart';
import 'package:medintel_mobile/services/api_service.dart';
import 'package:medintel_mobile/state/analysis/analysis_cubit.dart';
import 'package:medintel_mobile/state/analysis/analysis_state.dart';
import 'package:medintel_mobile/state/history/history_cubit.dart';
import 'package:medintel_mobile/state/history/history_state.dart';
import 'package:medintel_mobile/state/verification/verification_cubit.dart';

class FakeE2EApiService implements ApiService {
  bool failGenAi = false;
  bool failHeart = false;

  @override
  Future<Map<String, dynamic>> getHealth() async => {'status': 'ok'};

  @override
  Future<MLStatusResponse> getMLStatus() async => const MLStatusResponse(
        status: 'OK',
        models: {
          'diabetes': ModelStatusInfo(available: true, integrityVerified: true),
          'heart': ModelStatusInfo(available: true, integrityVerified: true),
          'kidney': ModelStatusInfo(available: true, integrityVerified: true),
        },
      );

  @override
  Future<GenAIStatusResponse> getGenAIStatus() async =>
      const GenAIStatusResponse(
        status: 'OK',
        available: true,
        provider: 'gemini',
        mode: 'cloud',
        model: 'gemini-1.5-pro',
        networkRequired: true,
      );

  @override
  Future<DocumentExtractionResult> extractDocument(String filePath,
      {String? engine}) async {
    return const DocumentExtractionResult(
      success: true,
      filename: 'report.pdf',
      extractor: 'tesseract',
      sourceType: SourceType.image,
      pages: [
        PageExtraction(
          pageNumber: 1,
          text: 'Glucose Fasting 110 mg/dL\nHemoglobin 14.2 g/dL',
        ),
      ],
      disclaimer: 'Educational non-diagnostic disclaimer',
    );
  }

  @override
  Future<ParseAndAnalyzeResponse> parseAndAnalyze(
      ParseAndAnalyzeRequest request) async {
    return const ParseAndAnalyzeResponse(
      totalLinesParsed: 2,
      totalMeasurementsAnalyzed: 2,
      items: [
        ParsedAndAnalyzedItem(
          parsedLine: 'Glucose Fasting 110 mg/dL',
          parsedAnalyte: 'Glucose Fasting',
          parserStatus: 'SUCCESS',
          extractionConfidence: 0.95,
          analysis: AnalysisResult(
            originalTestName: 'Glucose Fasting',
            canonicalName: 'Glucose Fasting',
            numericValue: 110.0,
            unit: 'mg/dL',
            classification: AnalyteClassification.high,
            analysisStatus: 'SUCCESS',
            referenceRange: ReferenceRangeSummary(
              canonicalName: 'Glucose Fasting',
              unit: 'mg/dL',
              normalLow: 70.0,
              normalHigh: 99.0,
              source: 'Verified Medical Sources',
            ),
          ),
        ),
        ParsedAndAnalyzedItem(
          parsedLine: 'Hemoglobin 14.2 g/dL',
          parsedAnalyte: 'Hemoglobin',
          parserStatus: 'SUCCESS',
          extractionConfidence: 0.95,
          analysis: AnalysisResult(
            originalTestName: 'Hemoglobin',
            canonicalName: 'Hemoglobin',
            numericValue: 14.2,
            unit: 'g/dL',
            classification: AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
            referenceRange: ReferenceRangeSummary(
              canonicalName: 'Hemoglobin',
              unit: 'g/dL',
              normalLow: 13.0,
              normalHigh: 17.0,
              source: 'Verified Medical Sources',
            ),
          ),
        ),
      ],
    );
  }

  @override
  Future<BatchAnalysisResponse> analyzeBatch(
      BatchAnalysisRequest request) async {
    return BatchAnalysisResponse(
      totalSubmitted: request.measurements.length,
      totalClassified: request.measurements.length,
      results: [
        for (final m in request.measurements)
          AnalysisResult(
            originalTestName: m.testName,
            canonicalName: m.testName,
            numericValue: (m.value as num?)?.toDouble(),
            unit: m.unit,
            classification: m.testName.toLowerCase().contains('glucose')
                ? AnalyteClassification.high
                : AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
            referenceRange: ReferenceRangeSummary(
              canonicalName: m.testName,
              unit: m.unit ?? '',
              normalLow: 70.0,
              normalHigh: 120.0,
              source: 'Verified Medical Sources',
            ),
          ),
      ],
    );
  }

  @override
  Future<RiskPredictionResponse> predictDiabetesRisk(
      DiabetesRiskRequest request) async {
    return const RiskPredictionResponse(
      condition: 'diabetes',
      status: 'OK',
      riskProbability: 0.38,
      riskBand: RiskBand.moderate,
      modelName: 'RandomForest',
    );
  }

  @override
  Future<RiskPredictionResponse> predictHeartRisk(
      HeartDiseaseRiskRequest request) async {
    if (failHeart) {
      throw Exception('Heart model service unavailable');
    }
    return const RiskPredictionResponse(
      condition: 'heart_disease',
      status: 'INSUFFICIENT_FEATURES',
      missingFeatures: ['chol', 'trestbps', 'oldpeak'],
    );
  }

  @override
  Future<RiskPredictionResponse> predictKidneyRisk(
      KidneyDiseaseRiskRequest request) async {
    return const RiskPredictionResponse(
      condition: 'kidney_disease',
      status: 'OK',
      riskProbability: 0.15,
      riskBand: RiskBand.low,
      modelName: 'LogisticRegression',
    );
  }

  @override
  Future<GenAIExplainResponse> explainFindings(
      GenAIExplainRequest request) async {
    if (failGenAi) {
      throw Exception('GenAI rate limit exceeded (HTTP 429)');
    }
    return GenAIExplainResponse(
      status: GenAIStatus.success,
      modelProvider: 'gemini',
      generatedAt: '2026-09-11T10:00:00Z',
      language: request.language,
      explanation: const GenAIExplanationPayload(
        summary: 'Your fasting glucose is slightly above standard reference limits.',
        followUpGuidance: ['Discuss your fasting blood sugar with a primary care doctor.'],
        recommendedQuestionsForDoctor: ['Should I monitor my blood glucose regularly?'],
      ),
    );
  }

  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  group('Phase 9 End-to-End Workflow & Integration Tests', () {
    late FakeE2EApiService fakeApi;

    setUp(() {
      fakeApi = FakeE2EApiService();
    });

    testWidgets('Full End-to-End Workflow: Ingestion → Verification → Analysis → History → Start New Analysis',
        (WidgetTester tester) async {
      await tester.pumpWidget(
        MedIntelApp(apiService: fakeApi),
      );
      await tester.pumpAndSettle();

      // 1. Home Screen Verification
      expect(find.byType(HomeScreen), findsOneWidget);
      expect(find.text('MedIntel AI'), findsOneWidget);
      expect(find.text('Upload Report'), findsOneWidget);

      // 2. Navigate to Upload Screen
      await tester.tap(find.text('Upload Report'));
      await tester.pumpAndSettle();
      expect(find.byType(UploadScreen), findsOneWidget);

      // 3. Populate VerificationCubit via parseExtractedText
      final verCubit = BlocProvider.of<VerificationCubit>(tester.element(find.byType(UploadScreen)));
      await verCubit.parseExtractedText(
        'Glucose Fasting 110 mg/dL\nHemoglobin 14.2 g/dL',
        patientContext: const PatientContext(age: 48, sex: 'M'),
      );
      await tester.pumpAndSettle();

      // 4. Navigate back to Home and open Verification Screen
      Navigator.of(tester.element(find.byType(UploadScreen))).pop();
      await tester.pumpAndSettle();
      await tester.tap(find.text('User Verification Gate'));
      await tester.pumpAndSettle();
      expect(find.byType(VerificationScreen), findsOneWidget);

      // 5. Verification Review UI
      expect(find.text('User Verification Gate'), findsOneWidget);
      expect(find.text('Glucose Fasting'), findsOneWidget);
      expect(find.text('Hemoglobin'), findsOneWidget);
      expect(find.text('Confirm & Analyze'), findsOneWidget);

      // 6. Confirm Verification and Proceed to Results
      await tester.tap(find.text('Confirm & Analyze'));
      await tester.pumpAndSettle();

      // 7. Results Screen Dashboard Rendered
      expect(find.byType(ResultsScreen), findsOneWidget);
      expect(find.text('Analysis & Risk Assessment'), findsOneWidget);
      expect(find.text('Statistical Disease Risk Indicators'), findsOneWidget);
      expect(find.text('Save to History'), findsOneWidget);
      expect(find.text('Start New Analysis'), findsOneWidget);

      // 8. Save to Local Session History
      await tester.ensureVisible(find.text('Save to History'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Save to History'));
      await tester.pumpAndSettle();

      expect(find.text('Saved to History'), findsOneWidget);
      expect(find.text('Analysis saved to local session history.'), findsOneWidget);

      // 9. Navigate back to Home and Open Report History
      Navigator.of(tester.element(find.byType(ResultsScreen))).popUntil((r) => r.isFirst);
      await tester.pumpAndSettle();
      expect(find.byType(HomeScreen), findsOneWidget);
      await tester.tap(find.text('Report History'));
      await tester.pumpAndSettle();
      expect(find.byType(HistoryScreen), findsOneWidget);

      // 10. History Screen displays the saved report card
      expect(find.text('2 Verified Measurements • Age: 48y • Sex: M'), findsOneWidget);
      expect(find.text('View Snapshot'), findsOneWidget);

      // 11. Tap History Card to inspect read-only HistoryDetailScreen
      await tester.tap(find.text('View Snapshot'));
      await tester.pumpAndSettle();
      expect(find.byType(HistoryDetailScreen), findsOneWidget);
      expect(find.text('Historical Analysis'), findsOneWidget);
      expect(find.textContaining('Historical Snapshot (Read-Only)'), findsOneWidget);

      // Pop back to Home Screen
      Navigator.of(tester.element(find.byType(HistoryDetailScreen))).pop();
      await tester.pumpAndSettle();
      Navigator.of(tester.element(find.byType(HistoryScreen))).pop();
      await tester.pumpAndSettle();

      // 12. Open ResultsScreen again and test "Start New Analysis"
      await tester.tap(find.text('Analysis & ML Risk'));
      await tester.pumpAndSettle();
      expect(find.byType(ResultsScreen), findsOneWidget);

      await tester.ensureVisible(find.text('Start New Analysis'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Start New Analysis'));
      await tester.pumpAndSettle();

      // 13. Verified returned to Home with clean slate
      expect(find.byType(HomeScreen), findsOneWidget);
      final currentVerState = BlocProvider.of<VerificationCubit>(tester.element(find.byType(HomeScreen))).state;
      expect(currentVerState.measurements, isEmpty);
      expect(currentVerState.isVerified, isFalse);

      // 14. History remains completely intact after resetting active analysis
      final historyState = BlocProvider.of<HistoryCubit>(tester.element(find.byType(HomeScreen))).state;
      expect(historyState, isA<HistoryLoaded>());
      expect((historyState as HistoryLoaded).records.length, equals(1));
    });

    test('Safety Safeguard: Unverified snapshot cannot execute analysis', () async {
      final repo = MedicalRepository(apiService: fakeApi);
      final cubit = AnalysisCubit(repository: repo);

      final unverifiedSnapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: 'm1',
            originalTestName: 'Glucose',
            testName: 'Glucose',
            value: 100,
            status: VerificationItemStatus.unverified,
          ),
        ],
        patientContext: const PatientContext(age: 35, sex: 'F'),
        isVerified: false,
      );

      await cubit.runFullAnalysis(unverifiedSnapshot);

      expect(cubit.state.status, equals(AnalysisStatus.failure));
      expect(cubit.state.generalError, contains('Client Safeguard'));
      expect(cubit.state.referenceAnalysis, isNull);

      await cubit.close();
    });

    test('Safety Safeguard: Missing model features are not fabricated or imputed', () async {
      final repo = MedicalRepository(apiService: fakeApi);
      final cubit = AnalysisCubit(repository: repo);

      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: 'm1',
            originalTestName: 'Glucose',
            testName: 'Glucose',
            value: 100,
            status: VerificationItemStatus.confirmed,
          ),
        ],
        patientContext: const PatientContext(age: 35, sex: 'F'),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);

      // Heart model received no chest pain or blood pressure features -> INSUFFICIENT_FEATURES
      expect(cubit.state.heartRisk?.status, equals('INSUFFICIENT_FEATURES'));
      expect(cubit.state.heartRisk?.riskProbability, isNull);
      expect(cubit.state.heartRisk?.riskBand, isNull);
      expect(cubit.state.heartRisk?.missingFeatures, isNotEmpty);

      await cubit.close();
    });

    test('Resilience: Partial ML failure preserves successful ML results and reference findings', () async {
      fakeApi.failHeart = true;
      final repo = MedicalRepository(apiService: fakeApi);
      final cubit = AnalysisCubit(repository: repo);

      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: 'm1',
            originalTestName: 'Glucose',
            testName: 'Glucose',
            value: 100,
            status: VerificationItemStatus.confirmed,
          ),
        ],
        patientContext: const PatientContext(age: 35, sex: 'F'),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);

      // Reference analysis and Diabetes/Kidney ML succeeded despite Heart failure
      expect(cubit.state.referenceAnalysis, isNotNull);
      expect(cubit.state.diabetesRisk?.status, equals('OK'));
      expect(cubit.state.kidneyRisk?.status, equals('OK'));
      expect(cubit.state.heartError, contains('Heart model service unavailable'));

      await cubit.close();
    });

    test('Resilience: GenAI HTTP 429/503 preserves reference and ML results and allows retry', () async {
      fakeApi.failGenAi = true;
      final repo = MedicalRepository(apiService: fakeApi);
      final cubit = AnalysisCubit(repository: repo);

      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: 'm1',
            originalTestName: 'Glucose',
            testName: 'Glucose',
            value: 100,
            status: VerificationItemStatus.confirmed,
          ),
        ],
        patientContext: const PatientContext(age: 35, sex: 'F'),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);

      // Reference and ML are preserved
      expect(cubit.state.referenceAnalysis, isNotNull);
      expect(cubit.state.diabetesRisk?.status, equals('OK'));
      expect(cubit.state.genAiExplanation, isNull);
      expect(cubit.state.genAiError, contains('rate limit'));

      // Recovery: retry after service restores
      fakeApi.failGenAi = false;
      await cubit.retryGenAI();

      expect(cubit.state.genAiExplanation, isNotNull);
      expect(cubit.state.genAiError, isNull);

      await cubit.close();
    });
  });
}
