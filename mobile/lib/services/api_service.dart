import 'dart:io';
import 'package:dio/dio.dart';
import '../core/constants/api_constants.dart';
import '../core/errors/api_exception.dart';
import '../core/network/dio_client.dart';
import '../models/extraction/document_extraction_result.dart';
import '../models/genai/genai_explain_request.dart';
import '../models/genai/genai_explain_response.dart';
import '../models/genai/genai_status_response.dart';
import '../models/auth/user_model.dart';
import '../models/history/analysis_history_item.dart';
import '../models/ml_risk/diabetes_risk_request.dart';
import '../models/ml_risk/heart_disease_risk_request.dart';
import '../models/ml_risk/kidney_disease_risk_request.dart';
import '../models/ml_risk/ml_status_response.dart';
import '../models/ml_risk/risk_prediction_response.dart';
import '../models/reference/batch_analysis.dart';
import '../models/reference/parse_and_analyze.dart';
import '../models/prescription/prescription_model.dart';

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

  /// 11. User Registration
  Future<UserModel> register({
    required String name,
    required String email,
    required String password,
    String? languagePreference,
  });

  /// 12. User Login
  Future<UserModel> login({
    required String email,
    required String password,
  });

  /// 13. Get current profile
  Future<UserModel?> getProfile();

  /// 14. Set active bearer auth token
  void setAuthToken(String? token);

  /// 15. Get current auth token
  String? get currentAuthToken;

  /// 16. Fetch all reports for authenticated user
  Future<List<AnalysisHistoryItem>> fetchUserReports();

  /// 17. Save a report for authenticated user
  Future<AnalysisHistoryItem> saveUserReport(AnalysisHistoryItem report);

  /// 18. Delete a report for authenticated user
  Future<void> deleteUserReport(String reportId);

  /// 19. Current backend base URL
  String get baseUrl;

  /// 20. Update active backend base URL
  void updateBaseUrl(String newUrl);

  /// 21. Explain prescription text or medications (Objective 2)
  Future<PrescriptionExplainResponse> explainPrescription(
    PrescriptionExplainRequest request,
  );

  /// 22. Upload prescription image or PDF and explain (Objective 2)
  Future<PrescriptionExplainResponse> uploadAndExplainPrescription(
    String filePath, {
    String language = 'english',
  });
}

/// Concrete Dio implementation of ApiService.
class ApiServiceImpl implements ApiService {
  final Dio _dio;

  ApiServiceImpl({DioClient? dioClient, Dio? dio})
      : _dio = dio ?? (dioClient ?? DioClient()).dio;

  @override
  String get baseUrl => _dio.options.baseUrl;

  @override
  void updateBaseUrl(String newUrl) {
    final sanitized = newUrl.trim();
    _dio.options.baseUrl = sanitized;
    DioClient.setActiveBaseUrl(sanitized);
  }

  @override
  Future<Map<String, dynamic>> getHealth() async {
    try {
      final response = await _dio.get(ApiConstants.health);
      return response.data as Map<String, dynamic>;
    } on DioException catch (e) {
      final unwrapped = _unwrapException(e);
      if (unwrapped is NetworkException) {
        final currentBase = _dio.options.baseUrl;
        final candidates = [
          ApiConstants.usbDeviceUrl,
          ApiConstants.emulatorUrl,
          ApiConstants.wifiLanUrl,
        ];
        for (final alt in candidates) {
          if (alt == currentBase) continue;
          try {
            updateBaseUrl(alt);
            final altResp = await _dio.get(ApiConstants.health);
            return altResp.data as Map<String, dynamic>;
          } catch (_) {}
        }
        updateBaseUrl(currentBase);
      }
      throw unwrapped;
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
      final unwrapped = _unwrapException(e);
      if (unwrapped is NetworkException) {
        final currentBase = _dio.options.baseUrl;
        final altBase = currentBase == ApiConstants.usbDeviceUrl
            ? ApiConstants.wifiLanUrl
            : (currentBase == ApiConstants.wifiLanUrl
                ? ApiConstants.usbDeviceUrl
                : null);
        if (altBase != null && altBase != currentBase) {
          try {
            updateBaseUrl(altBase);
            return await extractDocument(filePath, engine: engine);
          } catch (_) {
            updateBaseUrl(currentBase);
          }
        }
      }
      throw unwrapped;
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

  String? _authToken;

  @override
  String? get currentAuthToken => _authToken;

  @override
  void setAuthToken(String? token) {
    _authToken = token;
    if (token != null && token.isNotEmpty) {
      _dio.options.headers['Authorization'] = 'Bearer $token';
    } else {
      _dio.options.headers.remove('Authorization');
    }
  }

  @override
  Future<UserModel> register({
    required String name,
    required String email,
    required String password,
    String? languagePreference,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.authRegister,
        data: {
          'name': name.trim(),
          'email': email.trim().toLowerCase(),
          'password': password,
          'language_preference': languagePreference ?? 'english',
        },
        options: Options(contentType: 'application/json'),
      );
      final user = UserModel.fromJson(response.data as Map<String, dynamic>);
      setAuthToken(user.token);
      return user;
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<UserModel> login({
    required String email,
    required String password,
  }) async {
    try {
      final response = await _dio.post(
        ApiConstants.authLogin,
        data: {
          'email': email.trim().toLowerCase(),
          'password': password,
        },
        options: Options(contentType: 'application/json'),
      );
      final user = UserModel.fromJson(response.data as Map<String, dynamic>);
      setAuthToken(user.token);
      return user;
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<UserModel?> getProfile() async {
    try {
      final response = await _dio.get(ApiConstants.authMe);
      return UserModel.fromJson(response.data as Map<String, dynamic>, token: _authToken);
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<List<AnalysisHistoryItem>> fetchUserReports() async {
    try {
      final response = await _dio.get(ApiConstants.reports);
      final list = response.data as List<dynamic>;
      return list
          .map((item) => AnalysisHistoryItem.fromJson(item as Map<String, dynamic>))
          .toList();
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<AnalysisHistoryItem> saveUserReport(AnalysisHistoryItem report) async {
    try {
      final response = await _dio.post(
        ApiConstants.reports,
        data: report.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return AnalysisHistoryItem.fromJson(response.data as Map<String, dynamic>);
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<void> deleteUserReport(String reportId) async {
    try {
      await _dio.delete('${ApiConstants.reports}/$reportId');
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<PrescriptionExplainResponse> explainPrescription(
    PrescriptionExplainRequest request,
  ) async {
    try {
      final response = await _dio.post(
        ApiConstants.prescriptionExplain,
        data: request.toJson(),
        options: Options(contentType: 'application/json'),
      );
      return PrescriptionExplainResponse.fromJson(
        response.data as Map<String, dynamic>,
      );
    } on DioException catch (e) {
      throw _unwrapException(e);
    }
  }

  @override
  Future<PrescriptionExplainResponse> uploadAndExplainPrescription(
    String filePath, {
    String language = 'english',
  }) async {
    try {
      final file = File(filePath);
      final filename = file.uri.pathSegments.isNotEmpty
          ? file.uri.pathSegments.last
          : 'prescription.jpg';
      final formData = FormData.fromMap({
        'file': await MultipartFile.fromFile(filePath, filename: filename),
        'language': language,
      });

      final response = await _dio.post(
        ApiConstants.prescriptionExtractAndExplain,
        data: formData,
        options: Options(contentType: 'multipart/form-data'),
      );
      return PrescriptionExplainResponse.fromJson(
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
    String message = e.message ?? 'Unknown API error';
    if (e.response?.data is Map<String, dynamic>) {
      final data = e.response!.data as Map<String, dynamic>;
      if (data.containsKey('detail') && data['detail'] != null) {
        message = data['detail'].toString();
      }
    }
    return ApiException(
      message: message,
      statusCode: e.response?.statusCode,
    );
  }
}
