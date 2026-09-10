import '../core/errors/api_exception.dart';
import '../models/extraction/document_extraction_result.dart';
import '../models/genai/genai_explain_request.dart';
import '../models/genai/genai_explain_response.dart';
import '../models/genai/genai_status_response.dart';
import '../models/ml_risk/diabetes_risk_request.dart';
import '../models/ml_risk/heart_disease_risk_request.dart';
import '../models/ml_risk/kidney_disease_risk_request.dart';
import '../models/ml_risk/ml_status_response.dart';
import '../models/ml_risk/risk_prediction_response.dart';
import '../models/reference/batch_analysis.dart';
import '../models/reference/measurement_input.dart';
import '../models/reference/parse_and_analyze.dart';
import '../services/api_service.dart';

/// Repository orchestrating medical operations and enforcing client safeguards.
class MedicalRepository {
  final ApiService apiService;

  MedicalRepository({required this.apiService});

  Future<Map<String, dynamic>> checkBackendHealth() =>
      apiService.getHealth();

  Future<DocumentExtractionResult> extractDocument(
    String filePath, {
    String? engine,
  }) =>
      apiService.extractDocument(filePath, engine: engine);

  /// Client-side UX safeguard: asserts isUserVerified before submitting batch.
  /// Backend remains authoritative.
  Future<BatchAnalysisResponse> analyzeMeasurements({
    required List<MeasurementInput> measurements,
    required bool isUserVerified,
  }) async {
    if (!isUserVerified) {
      throw const VerificationRequiredException(
        message: 'Measurements must be confirmed by the user before analysis.',
      );
    }
    return apiService.analyzeBatch(
      BatchAnalysisRequest(
        measurements: measurements
            .map((m) => m.copyWith(isUserVerified: true))
            .toList(),
      ),
    );
  }

  Future<ParseAndAnalyzeResponse> parseAndAnalyzeText({
    required String text,
    required bool isUserVerified,
  }) =>
      apiService.parseAndAnalyze(
        ParseAndAnalyzeRequest(
          text: text,
          isUserVerified: isUserVerified,
        ),
      );

  Future<MLStatusResponse> getMLStatus() => apiService.getMLStatus();

  Future<RiskPredictionResponse> predictDiabetes({
    required DiabetesRiskRequest request,
  }) {
    if (!request.isUserVerified) {
      throw const VerificationRequiredException(
        message: 'Diabetes features must be verified by the user before ML prediction.',
      );
    }
    return apiService.predictDiabetesRisk(request);
  }

  Future<RiskPredictionResponse> predictHeartDisease({
    required HeartDiseaseRiskRequest request,
  }) {
    if (!request.isUserVerified) {
      throw const VerificationRequiredException(
        message: 'Heart disease features must be verified by the user before ML prediction.',
      );
    }
    return apiService.predictHeartRisk(request);
  }

  Future<RiskPredictionResponse> predictKidneyDisease({
    required KidneyDiseaseRiskRequest request,
  }) {
    if (!request.isUserVerified) {
      throw const VerificationRequiredException(
        message: 'Kidney disease features must be verified by the user before ML prediction.',
      );
    }
    return apiService.predictKidneyRisk(request);
  }

  Future<GenAIStatusResponse> getGenAIStatus() =>
      apiService.getGenAIStatus();

  Future<GenAIExplainResponse> generateExplanation({
    required GenAIExplainRequest request,
  }) {
    if (!request.isUserVerified) {
      throw const VerificationRequiredException(
        message: 'Verified findings required before generating GenAI explanations.',
      );
    }
    return apiService.explainFindings(request);
  }
}
