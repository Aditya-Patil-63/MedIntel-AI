/// API Constants and Endpoint Routes for MedIntel AI Backend.
class ApiConstants {
  ApiConstants._();

  /// Base URL configurable via --dart-define=API_BASE_URL=http://...
  /// Default: Android Emulator loopback to host FastAPI server.
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: 'http://10.0.2.2:8000',
  );

  // Timeouts
  static const Duration connectTimeout = Duration(seconds: 15);
  static const Duration receiveTimeout = Duration(seconds: 45);
  static const Duration sendTimeout = Duration(seconds: 30);

  // Endpoints
  static const String health = '/health';
  static const String extract = '/api/v1/extract';
  static const String referenceParseAndAnalyze =
      '/api/v1/reference/parse-and-analyze';
  static const String referenceAnalyze = '/api/v1/reference/analyze';
  static const String mlStatus = '/api/v1/ml/status';
  static const String mlDiabetesRisk = '/api/v1/ml/diabetes-risk';
  static const String mlHeartRisk = '/api/v1/ml/heart-risk';
  static const String mlKidneyRisk = '/api/v1/ml/kidney-risk';
  static const String genaiStatus = '/api/v1/genai/status';
  static const String genaiExplain = '/api/v1/genai/explain';
}
