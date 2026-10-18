/// API Constants and Endpoint Routes for MedIntel AI Backend.
class ApiConstants {
  ApiConstants._();

  /// Connection presets for development environments:
  /// - usbDeviceUrl: Used for physical Android phones via USB cable with `adb reverse tcp:8000 tcp:8000`
  /// - emulatorUrl: Used for Android Studio Virtual Devices (AVD)
  /// - wifiLanUrl: Used for physical phones over the local Wi-Fi network
  static const String usbDeviceUrl = 'http://127.0.0.1:8000';
  static const String emulatorUrl = 'http://10.0.2.2:8000';
  static const String wifiLanUrl = 'http://10.62.199.105:8000';

  /// Base URL configurable via --dart-define=API_BASE_URL=http://...
  /// Default: 'http://10.62.199.105:8000' for physical phone over Wi-Fi LAN (no USB/ADB reverse dependency).
  static const String baseUrl = String.fromEnvironment(
    'API_BASE_URL',
    defaultValue: wifiLanUrl,
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

  // User Authentication & Reports
  static const String authRegister = '/api/v1/auth/register';
  static const String authLogin = '/api/v1/auth/login';
  static const String authMe = '/api/v1/auth/me';
  static const String reports = '/api/v1/reports';
}
