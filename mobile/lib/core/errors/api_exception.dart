import 'package:equatable/equatable.dart';

/// Structured API Exception hierarchy for MedIntel Mobile.
class ApiException extends Equatable implements Exception {
  final String message;
  final int? statusCode;
  final String? errorType;
  final dynamic details;

  const ApiException({
    required this.message,
    this.statusCode,
    this.errorType,
    this.details,
  });

  @override
  String toString() =>
      'ApiException(status: $statusCode, errorType: $errorType, message: $message)';

  @override
  List<Object?> get props => [message, statusCode, errorType, details];
}

class NetworkException extends ApiException {
  const NetworkException({
    super.message = 'Unable to connect to the MedIntel server. Check your network or API base URL.',
    super.statusCode,
    super.errorType = 'NETWORK_ERROR',
    super.details,
  });
}

class ValidationException extends ApiException {
  const ValidationException({
    required super.message,
    super.statusCode = 422,
    super.errorType = 'VALIDATION_ERROR',
    super.details,
  });
}

class ServerException extends ApiException {
  const ServerException({
    required super.message,
    super.statusCode = 500,
    super.errorType = 'SERVER_ERROR',
    super.details,
  });
}

class ServiceUnavailableException extends ApiException {
  const ServiceUnavailableException({
    required super.message,
    super.statusCode = 503,
    super.errorType = 'SERVICE_UNAVAILABLE',
    super.details,
  });
}

class VerificationRequiredException extends ApiException {
  const VerificationRequiredException({
    super.message = 'Extracted values must be verified before clinical analysis or risk prediction.',
    super.statusCode = 400,
    super.errorType = 'VERIFICATION_REQUIRED',
    super.details,
  });
}
