import 'package:equatable/equatable.dart';

/// Service status for GenAI from GET /api/v1/genai/status.
class GenAIStatusResponse extends Equatable {
  final String status;
  final String provider;
  final String model;
  final bool available;
  final String mode;
  final bool networkRequired;

  const GenAIStatusResponse({
    required this.status,
    required this.provider,
    required this.model,
    required this.available,
    required this.mode,
    required this.networkRequired,
  });

  factory GenAIStatusResponse.fromJson(Map<String, dynamic> json) {
    return GenAIStatusResponse(
      status: json['status'] as String? ?? 'UNKNOWN',
      provider: json['provider'] as String? ?? '',
      model: json['model'] as String? ?? '',
      available: json['available'] as bool? ?? false,
      mode: json['mode'] as String? ?? '',
      networkRequired: json['network_required'] as bool? ?? false,
    );
  }

  Map<String, dynamic> toJson() => {
        'status': status,
        'provider': provider,
        'model': model,
        'available': available,
        'mode': mode,
        'network_required': networkRequired,
      };

  @override
  List<Object?> get props =>
      [status, provider, model, available, mode, networkRequired];
}
