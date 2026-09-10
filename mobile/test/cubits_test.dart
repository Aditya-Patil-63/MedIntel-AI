import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/core/errors/api_exception.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/extraction/document_extraction_result.dart';
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
import 'package:medintel_mobile/repositories/medical_repository.dart';
import 'package:medintel_mobile/services/api_service.dart';
import 'package:medintel_mobile/state/analysis/analysis_cubit.dart';
import 'package:medintel_mobile/state/analysis/analysis_state.dart';
import 'package:medintel_mobile/state/document/document_cubit.dart';
import 'package:medintel_mobile/state/document/document_state.dart';
import 'package:medintel_mobile/state/verification/verification_cubit.dart';

/// Fake ApiService for testing Cubits without real network.
class FakeApiService implements ApiService {
  bool shouldFail = false;

  @override
  Future<Map<String, dynamic>> getHealth() async {
    return {'status': 'ok'};
  }

  @override
  Future<DocumentExtractionResult> extractDocument(
    String filePath, {
    String? engine,
  }) async {
    if (shouldFail) throw const ApiException(message: 'Extraction failed');
    return const DocumentExtractionResult(
      success: true,
      filename: 'sample.pdf',
      sourceType: SourceType.digitalPdf,
      extractor: 'pdfplumber',
      fullText: 'Glucose: 105 mg/dL',
    );
  }

  @override
  Future<BatchAnalysisResponse> analyzeBatch(
    BatchAnalysisRequest request,
  ) async {
    if (shouldFail) throw const ApiException(message: 'Analysis failed');
    return const BatchAnalysisResponse(
      success: true,
      totalSubmitted: 1,
      totalClassified: 1,
      results: [
        AnalysisResult(
          originalTestName: 'Glucose',
          classification: AnalyteClassification.normal,
          analysisStatus: 'SUCCESS',
        ),
      ],
    );
  }

  @override
  Future<GenAIExplainResponse> explainFindings(
    GenAIExplainRequest request,
  ) async {
    return const GenAIExplainResponse(
      status: GenAIStatus.success,
      modelProvider: 'mock',
      generatedAt: '2026-09-10T12:00:00Z',
    );
  }

  @override
  Future<GenAIStatusResponse> getGenAIStatus() async {
    return const GenAIStatusResponse(
      status: 'OK',
      provider: 'mock',
      model: 'mock-v1',
      available: true,
      mode: 'offline_mock',
      networkRequired: false,
    );
  }

  @override
  Future<MLStatusResponse> getMLStatus() async {
    return const MLStatusResponse(status: 'OK', models: {});
  }

  @override
  Future<ParseAndAnalyzeResponse> parseAndAnalyze(
    ParseAndAnalyzeRequest request,
  ) async {
    return const ParseAndAnalyzeResponse(
      success: true,
      totalLinesParsed: 0,
      totalMeasurementsAnalyzed: 0,
      items: [],
    );
  }

  @override
  Future<RiskPredictionResponse> predictDiabetesRisk(
    DiabetesRiskRequest request,
  ) async {
    return const RiskPredictionResponse(
      condition: 'diabetes',
      status: 'OK',
    );
  }

  @override
  Future<RiskPredictionResponse> predictHeartRisk(
    HeartDiseaseRiskRequest request,
  ) async {
    return const RiskPredictionResponse(
      condition: 'heart_disease',
      status: 'OK',
    );
  }

  @override
  Future<RiskPredictionResponse> predictKidneyRisk(
    KidneyDiseaseRiskRequest request,
  ) async {
    return const RiskPredictionResponse(
      condition: 'kidney_disease',
      status: 'OK',
    );
  }
}

void main() {
  late FakeApiService fakeApi;
  late MedicalRepository repository;

  setUp(() {
    fakeApi = FakeApiService();
    repository = MedicalRepository(apiService: fakeApi);
  });

  group('DocumentCubit', () {
    test('extractDocument emits loading then extracted on success', () async {
      final cubit = DocumentCubit(apiService: fakeApi);
      expect(cubit.state, const DocumentInitial());

      final future = cubit.extractDocument('test_doc.pdf');
      expect(cubit.state, isA<DocumentLoading>());

      await future;
      expect(cubit.state, isA<DocumentExtracted>());
      final extracted = cubit.state as DocumentExtracted;
      expect(extracted.result.filename, 'sample.pdf');
    });

    test('extractDocument emits error when api fails', () async {
      fakeApi.shouldFail = true;
      final cubit = DocumentCubit(apiService: fakeApi);

      await cubit.extractDocument('bad_doc.pdf');
      expect(cubit.state, isA<DocumentError>());
    });
  });

  group('VerificationCubit & Mandatory Verification Gate', () {
    test('loads measurements unverified, allows edit, and confirms verification', () {
      final cubit = VerificationCubit();
      expect(cubit.state.isVerified, false);

      // 1. Load unverified items
      cubit.loadMeasurements([
        const MeasurementInput(testName: 'Hemoglobin', value: 13.5),
        const MeasurementInput(testName: 'FBS', value: 100.0),
      ]);
      expect(cubit.state.measurements.length, 2);
      expect(cubit.state.isVerified, false);

      // 2. User modifies an item -> invalidates verification
      cubit.updateMeasurement(
        1,
        const MeasurementInput(testName: 'FBS', value: 105.0),
      );
      expect(cubit.state.measurements[1].value, 105.0);
      expect(cubit.state.isVerified, false);

      // 3. User explicitly confirms verification
      cubit.confirmVerification();
      expect(cubit.state.isVerified, true);
      expect(cubit.state.measurements.every((m) => m.isUserVerified), true);
    });
  });

  group('AnalysisCubit Safety Verification Safeguard', () {
    test('blocks analysis and emits error when isUserVerified is false', () async {
      final cubit = AnalysisCubit(repository: repository);

      await cubit.runReferenceAnalysis(
        measurements: [const MeasurementInput(testName: 'FBS', value: 100.0)],
        isUserVerified: false, // Unverified!
      );

      expect(cubit.state, isA<AnalysisError>());
      final err = cubit.state as AnalysisError;
      expect(err.message, contains('must be verified before analysis'));
    });

    test('proceeds to analysis and emits success when isUserVerified is true', () async {
      final cubit = AnalysisCubit(repository: repository);

      await cubit.runReferenceAnalysis(
        measurements: [const MeasurementInput(testName: 'FBS', value: 100.0)],
        isUserVerified: true, // Verified!
      );

      expect(cubit.state, isA<AnalysisSuccess>());
      final success = cubit.state as AnalysisSuccess;
      expect(success.referenceAnalysis?.totalClassified, 1);
    });
  });
}
