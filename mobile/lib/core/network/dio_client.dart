import 'package:dio/dio.dart';
import '../constants/api_constants.dart';
import '../errors/api_exception.dart';

/// Configured Dio HTTP client singleton for MedIntel AI.
///
/// NOTE: Does NOT globally force 'Content-Type: application/json' so that
/// multipart/form-data requests (e.g. document extraction) automatically
/// set the appropriate multipart boundary.
class DioClient {
  late final Dio dio;

  DioClient({String? baseUrl, Dio? customDio}) {
    if (customDio != null) {
      dio = customDio;
      return;
    }

    final effectiveBaseUrl = baseUrl ?? ApiConstants.baseUrl;

    dio = Dio(
      BaseOptions(
        baseUrl: effectiveBaseUrl,
        connectTimeout: ApiConstants.connectTimeout,
        receiveTimeout: ApiConstants.receiveTimeout,
        sendTimeout: ApiConstants.sendTimeout,
        headers: {
          'Accept': 'application/json',
        },
        responseType: ResponseType.json,
      ),
    );

    // Logging & Error Transformation Interceptor
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          // Sanitized request logging (never log full document bytes/PII)
          handler.next(options);
        },
        onResponse: (response, handler) {
          handler.next(response);
        },
        onError: (DioException e, handler) {
          final transformed = _mapDioException(e);
          handler.reject(
            DioException(
              requestOptions: e.requestOptions,
              response: e.response,
              type: e.type,
              error: transformed,
            ),
          );
        },
      ),
    );
  }

  static ApiException _mapDioException(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.connectionError) {
      return NetworkException(
        message: 'Connection failed: ${e.message ?? "Server unreachable"}',
        details: e.type.toString(),
      );
    }

    final response = e.response;
    if (response != null) {
      final statusCode = response.statusCode;
      final data = response.data;
      String message = 'An error occurred';
      String? errorType;

      if (data is Map<String, dynamic>) {
        message = data['detail']?.toString() ??
            data['message']?.toString() ??
            'Error: status $statusCode';
        errorType = data['error_type']?.toString();
      } else if (data is String) {
        message = data;
      }

      switch (statusCode) {
        case 400:
          if (message.contains('verification') || message.contains('VERIFICATION')) {
            return VerificationRequiredException(
              message: message,
              statusCode: 400,
              details: data,
            );
          }
          return ApiException(
            message: message,
            statusCode: 400,
            errorType: errorType ?? 'BAD_REQUEST',
            details: data,
          );
        case 422:
          return ValidationException(
            message: message,
            statusCode: 422,
            details: data,
          );
        case 503:
          return ServiceUnavailableException(
            message: message,
            statusCode: 503,
            details: data,
          );
        case 500:
        default:
          return ServerException(
            message: message,
            statusCode: statusCode ?? 500,
            details: data,
          );
      }
    }

    return ApiException(
      message: e.message ?? 'Unknown network error',
      errorType: 'UNKNOWN',
    );
  }
}
