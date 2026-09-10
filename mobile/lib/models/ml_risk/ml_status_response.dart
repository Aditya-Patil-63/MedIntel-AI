import 'package:equatable/equatable.dart';

/// Status details for an individual disease ML model.
class ModelStatusInfo extends Equatable {
  final bool available;
  final String? modelName;
  final String? modelType;
  final bool integrityVerified;
  final String? version;

  const ModelStatusInfo({
    required this.available,
    this.modelName,
    this.modelType,
    required this.integrityVerified,
    this.version,
  });

  factory ModelStatusInfo.fromJson(Map<String, dynamic> json) {
    return ModelStatusInfo(
      available: json['available'] as bool? ?? false,
      modelName: json['model_name'] as String?,
      modelType: json['model_type'] as String?,
      integrityVerified: json['integrity_verified'] as bool? ?? false,
      version: json['version'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'available': available,
        if (modelName != null) 'model_name': modelName,
        if (modelType != null) 'model_type': modelType,
        'integrity_verified': integrityVerified,
        if (version != null) 'version': version,
      };

  @override
  List<Object?> get props =>
      [available, modelName, modelType, integrityVerified, version];
}

/// Overall ML service status from GET /api/v1/ml/status.
class MLStatusResponse extends Equatable {
  final String status;
  final Map<String, ModelStatusInfo> models;

  const MLStatusResponse({
    required this.status,
    required this.models,
  });

  factory MLStatusResponse.fromJson(Map<String, dynamic> json) {
    final rawModels = json['models'] as Map<String, dynamic>? ?? {};
    final parsedModels = rawModels.map(
      (key, value) => MapEntry(
        key,
        ModelStatusInfo.fromJson(value as Map<String, dynamic>),
      ),
    );
    return MLStatusResponse(
      status: json['status'] as String? ?? 'UNKNOWN',
      models: parsedModels,
    );
  }

  Map<String, dynamic> toJson() => {
        'status': status,
        'models': models.map((k, v) => MapEntry(k, v.toJson())),
      };

  @override
  List<Object?> get props => [status, models];
}
