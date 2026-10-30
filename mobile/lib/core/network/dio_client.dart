import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import '../constants/api_constants.dart';
import '../errors/api_exception.dart';
import 'server_url_storage.dart';

/// Configured Dio HTTP client singleton for MedIntel AI.
///
/// NOTE: Does NOT globally force 'Content-Type: application/json' so that
/// multipart/form-data requests (e.g. document extraction) automatically
/// set the appropriate multipart boundary.
class DioClient {
  static String? _configuredBaseUrl;
  static bool _hasSuccessfulRequest = false;

  /// Globally active base URL for HTTP requests.
  static String get activeBaseUrl {
    if (_configuredBaseUrl != null && _configuredBaseUrl!.isNotEmpty) {
      return _configuredBaseUrl!;
    }
    final saved = ServerUrlStorage.getSavedUrlSync();
    if (saved != null && saved.isNotEmpty) {
      _configuredBaseUrl = saved;
      return saved;
    }
    return ApiConstants.baseUrl;
  }

  /// Sets the active base URL for new and existing instances.
  static void setActiveBaseUrl(String url) {
    _configuredBaseUrl = url.trim();
  }

  /// Whether at least one request has succeeded (used to manage cold-start timeouts).
  static bool get hasSuccessfulRequest => _hasSuccessfulRequest;

  /// Resets cold-start request state (useful for tests).
  static void resetRequestState() {
    _hasSuccessfulRequest = false;
  }

  late final Dio dio;

  DioClient({String? baseUrl, Dio? customDio}) {
    if (customDio != null) {
      dio = customDio;
      return;
    }

    final effectiveBaseUrl = baseUrl ?? activeBaseUrl;

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

    // Logging & Error Transformation Interceptor with automatic connection-timeout retry
    dio.interceptors.add(
      InterceptorsWrapper(
        onRequest: (options, handler) {
          // Sanitized request logging (never log full document bytes/PII)
          handler.next(options);
        },
        onResponse: (response, handler) {
          if (!_hasSuccessfulRequest) {
            _hasSuccessfulRequest = true;
            // Switch to normal operational timeouts for subsequent requests in release mode
            if (kReleaseMode) {
              dio.options.connectTimeout = ApiConstants.normalConnectTimeout;
              dio.options.receiveTimeout = ApiConstants.normalReceiveTimeout;
            }
          }
          handler.next(response);
        },
        onError: (DioException e, handler) async {
          final isConnectionTimeout =
              e.type == DioExceptionType.connectionTimeout ||
              e.type == DioExceptionType.connectionError;

          final hasRetried = e.requestOptions.extra['has_retried'] == true;

          // Free tier Render server sleeps when idle (cold start can take 50+ seconds).
          // Attempt exactly 1 automatic retry on connection timeout with generous cold-start timeout.
          if (isConnectionTimeout && !hasRetried) {
            e.requestOptions.extra['has_retried'] = true;
            e.requestOptions.connectTimeout = ApiConstants.coldStartTimeout;
            e.requestOptions.receiveTimeout = ApiConstants.coldStartTimeout;
            try {
              final response = await dio.fetch(e.requestOptions);
              if (!_hasSuccessfulRequest) {
                _hasSuccessfulRequest = true;
                if (kReleaseMode) {
                  dio.options.connectTimeout = ApiConstants.normalConnectTimeout;
                  dio.options.receiveTimeout = ApiConstants.normalReceiveTimeout;
                }
              }
              return handler.resolve(response);
            } on DioException catch (retryErr) {
              final transformed = _mapDioException(retryErr);
              return handler.reject(
                DioException(
                  requestOptions: retryErr.requestOptions,
                  response: retryErr.response,
                  type: retryErr.type,
                  error: transformed,
                ),
              );
            } catch (err) {
              return handler.reject(
                DioException(
                  requestOptions: e.requestOptions,
                  type: e.type,
                  error: ApiException(message: err.toString()),
                ),
              );
            }
          }

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

  /// Updates the base URL on the active Dio instance.
  void updateBaseUrl(String newUrl) {
    final sanitized = newUrl.trim();
    dio.options.baseUrl = sanitized;
    _configuredBaseUrl = sanitized;
  }

  static ApiException _mapDioException(DioException e) {
    if (e.type == DioExceptionType.connectionTimeout ||
        e.type == DioExceptionType.receiveTimeout ||
        e.type == DioExceptionType.sendTimeout ||
        e.type == DioExceptionType.connectionError) {
      final currentUrl = e.requestOptions.baseUrl;
      return NetworkException(
        message:
            'Unable to connect to MedIntel AI server ($currentUrl). '
            'The cloud server may still be waking up from idle sleep (can take up to a minute). '
            'Please tap Retry to try again.',
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
