import 'dart:io';
import 'package:dio/dio.dart';
import '../core/constants/api_constants.dart';
import '../core/errors/api_exception.dart';
import '../core/network/dio_client.dart';
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
import '../models/reference/parse_and_analyze.dart';

/// Abstract API service contract for MedIntel AI FastAPI backend.
abstract class ApiService {
  /// 1. Health check
  Future<Map<String, dynamic>> getHealth();

  /// 2. Document & OCR text extraction (multipart upload)
  Future<DocumentExtractionResult> extractDocument(
    String filePath, {
    String? engine,
  });

  /// 3. Parse and analyze unstructured text
  Future<ParseAndAnalyzeResponse> parseAndAnalyze(
    ParseAndAnalyzeRequest request,
  );

  /// 4. Batch reference analysis on structured measurements
  Future<BatchAnalysisResponse> analyzeBatch(
    BatchAnalysisRequest request,
  );

  /// 5. ML service and models health status
  Future<MLStatusResponse> getMLStatus();

  /// 6. Diabetes risk prediction
  Future<RiskPredictionResponse> predictDiabetesRisk(
    DiabetesRiskRequest request,
  );

  /// 7. Heart disease risk prediction
  Future<RiskPredictionResponse> predictHeartRisk(
    HeartDiseaseRiskRequest request,
  );

  /// 8. Kidney disease risk prediction
  Future<RiskPredictionResponse> predictKidneyRisk(
    KidneyDiseaseRiskRequest request,
  );

  /// 9. GenAI subsystem health status
  Future<GenAIStatusResponse> getGenAIStatus();

  /// 10. GenAI structured patient explanation
  Future<GenAIExplainResponse> explainFindings(
    GenAIExplainRequest request,
  );
}

/// Concrete Dio implementation of ApiService.
class ApiServiceImpl implements ApiService {
  final Dio _dio;

  ApiServiceImpl({DioClient? dioClient, Dio? dio})
      : _dio = dio ?? (dioClient ?? DioClient()).dio;

  @override
  Future<Map<String, dynamic>> getHealth() async {
    try {
      final response = await _dio.get(ApiConstants.health);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<DocumentExtractionResult> extractDocument(
    String filePath, {
    String? engine,
  }) async {
    try {
      final file = File(filePath);
      final filename = file.uri.pathSegments.isNotEmpty
          ? file.uri.pathSegments.last
          : 'document.pdf';

      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(
          filePath,
          filename: filename,
        ),
      });

      final queryParams = <String, dynamic>{};
      if (engine != null && engine.isNotEmpty) {
        queryParams['engine'] = engine;
      }

      // Dio automatically sets multipart/form-data with proper boundary
      final response = await _dio.post(
        ApiConstants.extract,
        data: formData,
        queryParameters: queryParams.isNotEmpty ? queryParams : null,
      );

      return DocumentExtractionResult.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<ParseAndAnalyzeResponse> parseAndAnalyze(
    ParseAndAnalyzeRequest request,
  ) async {
    try {
      final response = await _dio.post(
        ApiConstants.referenceParseAndAnalyze,
        data: request.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return ParseAndAnalyzeResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<BatchAnalysisResponse> analyzeBatch(
    BatchAnalysisRequest request,
  ) async {
    try {
      final response = await _dio.post(
        ApiConstants.referenceAnalyze,
        data: request.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return BatchAnalysisResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<MLStatusResponse> getMLStatus() async {
    try {
      final response = await _dio.get(ApiConstants.mlStatus);
      return MLStatusResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<RiskPredictionResponse> predictDiabetesRisk(
    DiabetesRiskRequest request,
  ) async {
    try {
      final response = await _dio.post(
        ApiConstants.mlDiabetesRisk,
        data: request.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return RiskPredictionResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<RiskPredictionResponse> predictHeartRisk(
    HeartDiseaseRiskRequest request,
  ) async {
    try {
      final response = await _dio.post(
        ApiConstants.mlHeartRisk,
        data: request.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return RiskPredictionResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<RiskPredictionResponse> predictKidneyRisk(
    KidneyDiseaseRiskRequest request,
  ) async {
    try {
      final response = await _dio.post(
        ApiConstants.mlKidneyRisk,
        data: request.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return RiskPredictionResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<GenAIStatusResponse> getGenAIStatus() async {
    try {
      final response = await _dio.get(ApiConstants.genaiStatus);
      return GenAIStatusResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<GenAIExplainResponse> explainFindings(
    GenAIExplainRequest request,
  ) async {
    try {
      final response = await _dio.post(
        ApiConstants.genaiExplain,
        data: request.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return GenAIExplainResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  ApiException _unwrapException(DioException e) {
    if (e.error is ApiException) {
      return e.error as ApiException;
    }
    return ApiException(
      message: e.message ?? 'Unknown API error',
      statusCode: e.response?.statusCode,
    );
  }
}
