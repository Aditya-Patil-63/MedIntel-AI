import 'package:equatable/equatable.dart';
import '../common/enums.dart';

/// ML risk prediction response for a single disease condition.
class RiskPredictionResponse extends Equatable {
  final String condition;
  final String status;
  final double? riskProbability;
  final RiskBand? riskBand;
  final String? modelName;
  final String? modelVersion;
  final int suppliedFeaturesCount;
  final int requiredFeaturesCount;
  final List<String> missingFeatures;
  final String disclaimer;
  final int? persistedPredictionId;

  const RiskPredictionResponse({
    required this.condition,
    required this.status,
    this.riskProbability,
    this.riskBand,
    this.modelName,
    this.modelVersion,
    this.suppliedFeaturesCount = 0,
    this.requiredFeaturesCount = 0,
    this.missingFeatures = const [],
    this.disclaimer =
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
    this.persistedPredictionId,
  });

  factory RiskPredictionResponse.fromJson(Map<String, dynamic> json) {
    return RiskPredictionResponse(
      condition: json['condition'] as String? ?? '',
      status: json['status'] as String? ?? '',
      riskProbability: (json['risk_probability'] as num?)?.toDouble(),
      riskBand: RiskBand.fromString(json['risk_band'] as String?),
      modelName: json['model_name'] as String?,
      modelVersion: json['model_version'] as String?,
      suppliedFeaturesCount:
          (json['supplied_features_count'] as num?)?.toInt() ?? 0,
      requiredFeaturesCount:
          (json['required_features_count'] as num?)?.toInt() ?? 0,
      missingFeatures: (json['missing_features'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      disclaimer: json['disclaimer'] as String? ??
          'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
      persistedPredictionId:
          (json['persisted_prediction_id'] as num?)?.toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
        'condition': condition,
        'status': status,
        if (riskProbability != null) 'risk_probability': riskProbability,
        if (riskBand != null) 'risk_band': riskBand!.value,
        if (modelName != null) 'model_name': modelName,
        if (modelVersion != null) 'model_version': modelVersion,
        'supplied_features_count': suppliedFeaturesCount,
        'required_features_count': requiredFeaturesCount,
        'missing_features': missingFeatures,
        'disclaimer': disclaimer,
        if (persistedPredictionId != null)
          'persisted_prediction_id': persistedPredictionId,
      };

  @override
  List<Object?> get props => [
        condition,
        status,
        riskProbability,
        riskBand,
        modelName,
        modelVersion,
        suppliedFeaturesCount,
        requiredFeaturesCount,
        missingFeatures,
        disclaimer,
        persistedPredictionId,
      ];
}
