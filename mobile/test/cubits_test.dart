import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/core/errors/api_exception.dart';
import 'package:medintel_mobile/models/analysis/verified_snapshot.dart';
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
import 'package:medintel_mobile/models/reference/editable_measurement.dart';
import 'package:medintel_mobile/models/reference/parse_and_analyze.dart';
import 'package:medintel_mobile/models/reference/patient_context.dart';
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
  ParseAndAnalyzeResponse? parseResponse;

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
      filename: 'sample_report.pdf',
      sourceType: SourceType.digitalPdf,
      extractor: 'pdfplumber',
      fullText: 'Fasting Blood Glucose: 126 mg/dL\nHemoglobin: 14.2 g/dL',
      totalPages: 1,
      confidence: 0.98,
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
    if (shouldFail) throw const ApiException(message: 'Parsing failed');
    if (parseResponse != null) return parseResponse!;

    return const ParseAndAnalyzeResponse(
      success: true,
      totalLinesParsed: 2,
      totalMeasurementsAnalyzed: 2,
      items: [
        ParsedAndAnalyzedItem(
          parsedLine: 'Fasting Blood Glucose: 126 mg/dL',
          parsedAnalyte: 'Fasting Blood Glucose',
          canonicalName: 'Fasting Blood Glucose',
          parserStatus: 'SUCCESS',
          extractedReferenceRange: '70 - 99 mg/dL',
          extractionConfidence: 0.95,
          analysis: AnalysisResult(
            originalTestName: 'Fasting Blood Glucose',
            canonicalName: 'Fasting Blood Glucose',
            numericValue: 126.0,
            unit: 'mg/dL',
            classification: AnalyteClassification.high,
            analysisStatus: 'SUCCESS',
          ),
        ),
        ParsedAndAnalyzedItem(
          parsedLine: 'Hemoglobin: 14.2 g/dL',
          parsedAnalyte: 'Hemoglobin',
          canonicalName: 'Hemoglobin',
          parserStatus: 'SUCCESS',
          extractedReferenceRange: '13.8 - 17.2 g/dL',
          extractionConfidence: 0.99,
          analysis: AnalysisResult(
            originalTestName: 'Hemoglobin',
            canonicalName: 'Hemoglobin',
            numericValue: 14.2,
            unit: 'g/dL',
            classification: AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
          ),
        ),
      ],
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

  group('DocumentCubit — File Validation & Lifecycle', () {
    late DocumentCubit cubit;

    setUp(() {
      cubit = DocumentCubit(apiService: fakeApi);
    });

    test('validates supported file extensions (.pdf, .png, .jpg, .jpeg)', () {
      expect(cubit.validateFileAttributes('report.pdf', 1024), isNull);
      expect(cubit.validateFileAttributes('scan.png', 2048), isNull);
      expect(cubit.validateFileAttributes('photo.jpg', 4096), isNull);
      expect(cubit.validateFileAttributes('photo.jpeg', 4096), isNull);

      // Unsupported
      expect(cubit.validateFileAttributes('report.txt', 1024),
          contains('Unsupported file format'));
      expect(cubit.validateFileAttributes('data.docx', 1024),
          contains('Unsupported file format'));
      expect(cubit.validateFileAttributes('archive.zip', 1024),
          contains('Unsupported file format'));
      expect(cubit.validateFileAttributes('noextension', 1024),
          contains('File has no extension'));
    });

    test('rejects files exceeding 10 MB limit', () {
      const tenMb = 10 * 1024 * 1024;
      expect(cubit.validateFileAttributes('large.pdf', tenMb), isNull);
      expect(cubit.validateFileAttributes('oversized.pdf', tenMb + 1),
          contains('exceeds the 10 MB limit'));
      expect(cubit.validateFileAttributes('huge.png', 15 * 1024 * 1024),
          contains('exceeds the 10 MB limit'));
    });

    test('rejects 0 byte empty files', () {
      expect(cubit.validateFileAttributes('empty.pdf', 0),
          contains('Selected file is empty'));
    });

    test('uploadAndExtract transitions to DocumentExtracting then DocumentExtracted', () async {
      expect(cubit.state, const DocumentInitial());

      final future = cubit.uploadAndExtract('path/to/report.pdf');
      expect(cubit.state, isA<DocumentExtracting>());

      await future;
      expect(cubit.state, isA<DocumentExtracted>());
      final extracted = cubit.state as DocumentExtracted;
      expect(extracted.result.filename, 'sample_report.pdf');
      expect(extracted.result.totalPages, 1);
      expect(extracted.result.confidence, 0.98);
    });

    test('uploadAndExtract emits DocumentError on failure and supports retry', () async {
      fakeApi.shouldFail = true;

      await cubit.uploadAndExtract('path/to/broken.pdf');
      expect(cubit.state, isA<DocumentError>());
      final errorState = cubit.state as DocumentError;
      expect(errorState.message, contains('Extraction failed'));
      expect(errorState.lastFilePath, 'path/to/broken.pdf');

      // Recover and retry
      fakeApi.shouldFail = false;
      await cubit.retryLastExtraction();
      expect(cubit.state, isA<DocumentExtracted>());
    });
  });

  group('VerificationCubit — Ingestion, Editing & Verification Gate', () {
    late VerificationCubit cubit;

    setUp(() {
      cubit = VerificationCubit(apiService: fakeApi);
    });

    test('parseExtractedText sends text and initializes all items as UNVERIFIED', () async {
      expect(cubit.state.measurements, isEmpty);
      expect(cubit.state.isVerified, false);

      await cubit.parseExtractedText(
        'Fasting Blood Glucose: 126 mg/dL\nHemoglobin: 14.2 g/dL',
        patientContext: const PatientContext(age: 50, sex: 'M'),
      );

      expect(cubit.state.isParsing, false);
      expect(cubit.state.isVerified, false); // Mandatory gate: must NOT be verified yet
      expect(cubit.state.measurements.length, 2);

      // Verify each item enters unverified
      for (final item in cubit.state.measurements) {
        expect(item.status, VerificationItemStatus.unverified);
        expect(item.isUserVerified, false);
      }
      expect(cubit.state.unverifiedCount, 2);
      expect(cubit.state.patientContext.age, 50.0);
    });

    test('editing a measurement marks it CORRECTED and resets confirmation', () async {
      await cubit.parseExtractedText('Fasting Blood Glucose: 126 mg/dL');
      final firstId = cubit.state.measurements.first.id;

      // First confirm
      final confirmed = cubit.confirmVerification();
      expect(confirmed, true);
      expect(cubit.state.isVerified, true);

      // User modifies value -> MUST invalidate verification!
      cubit.updateMeasurement(
        firstId,
        testName: 'Fasting Blood Glucose',
        value: 128.0,
        unit: 'mg/dL',
      );

      expect(cubit.state.isVerified, false); // Verification invalidated!
      final updated = cubit.state.measurements.first;
      expect(updated.value, 128.0);
      expect(updated.status, VerificationItemStatus.corrected);
      expect(cubit.state.correctedCount, 1);
    });

    test('adding a measurement resets verification and marks item CORRECTED/manual', () {
      cubit.addMeasurement(
        testName: 'HbA1c',
        value: 6.8,
        unit: '%',
      );

      expect(cubit.state.measurements.length, 1);
      final item = cubit.state.measurements.first;
      expect(item.testName, 'HbA1c');
      expect(item.value, 6.8);
      expect(item.unit, '%');
      expect(item.status, VerificationItemStatus.corrected);
      expect(item.origin, MeasurementOrigin.manual);
      expect(cubit.state.isVerified, false);
    });

    test('removing a measurement resets verification', () async {
      await cubit.parseExtractedText('Test: 10');
      cubit.confirmVerification();
      expect(cubit.state.isVerified, true);
      expect(cubit.state.measurements.length, 2);

      final id = cubit.state.measurements.first.id;
      cubit.removeMeasurement(id);

      expect(cubit.state.measurements.length, 1);
      expect(cubit.state.isVerified, false);
    });

    test('confirmVerification validates non-empty values and transitions unverified items to CONFIRMED', () async {
      await cubit.parseExtractedText('Test: 10');
      expect(cubit.state.measurements.first.status, VerificationItemStatus.unverified);

      final success = cubit.confirmVerification();
      expect(success, true);
      expect(cubit.state.isVerified, true);
      expect(cubit.state.measurements.first.status, VerificationItemStatus.confirmed);
      expect(cubit.state.confirmedCount, 2);
    });

    test('confirmVerification rejects empty test name or null value', () {
      cubit.addMeasurement(testName: ' ', value: 10.0);
      final success1 = cubit.confirmVerification();
      expect(success1, false);
      expect(cubit.state.errorMessage, contains('cannot be empty'));

      cubit.reset();
      cubit.addMeasurement(testName: 'Valid Name', value: '');
      final success2 = cubit.confirmVerification();
      expect(success2, false);
      expect(cubit.state.errorMessage, contains('Value missing'));
    });

    test('confirmVerification rejects invalid patient age > 130', () {
      cubit.addMeasurement(testName: 'Valid Name', value: 10.0);
      cubit.updatePatientContext(const PatientContext(age: 150));

      final success = cubit.confirmVerification();
      expect(success, false);
      expect(cubit.state.errorMessage, contains('between 0 and 130'));
    });
  });

  group('AnalysisCubit — Safety Safeguard', () {
    test('blocks analysis when isUserVerified is false', () async {
      final cubit = AnalysisCubit(repository: repository);
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'FBS',
            testName: 'FBS',
            value: 100.0,
          ),
        ],
        patientContext: const PatientContext(),
        isVerified: false,
      );

      await cubit.runFullAnalysis(snapshot);

      expect(cubit.state.status, AnalysisStatus.failure);
      expect(cubit.state.generalError, contains('must be confirmed and verified'));
    });

    test('proceeds to analysis when isUserVerified is true', () async {
      final cubit = AnalysisCubit(repository: repository);
      final snapshot = VerifiedSnapshot(
        measurements: const [
          EditableMeasurement(
            id: '1',
            originalTestName: 'FBS',
            testName: 'FBS',
            value: 100.0,
          ),
        ],
        patientContext: const PatientContext(),
        isVerified: true,
      );

      await cubit.runFullAnalysis(snapshot);

      expect(cubit.state.status, AnalysisStatus.success);
      expect(cubit.state.referenceAnalysis, isNotNull);
    });
  });
}
