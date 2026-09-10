import 'package:equatable/equatable.dart';
import '../common/enums.dart';

/// Pre-evaluated deterministic laboratory finding fed to GenAI.
class VerifiedAnalyteSummary extends Equatable {
  final String testName;
  final String? canonicalName;
  final String? displayName;
  final double? value;
  final String? unit;
  final AnalyteClassification? classification;
  final double? referenceLow;
  final double? referenceHigh;
  final String? referenceSource;
  final String? analysisStatus;
  final List<String> warnings;

  const VerifiedAnalyteSummary({
    required this.testName,
    this.canonicalName,
    this.displayName,
    this.value,
    this.unit,
    this.classification,
    this.referenceLow,
    this.referenceHigh,
    this.referenceSource,
    this.analysisStatus,
    this.warnings = const [],
  });

  factory VerifiedAnalyteSummary.fromJson(Map<String, dynamic> json) {
    return VerifiedAnalyteSummary(
      testName: json['test_name'] as String? ?? '',
      canonicalName: json['canonical_name'] as String?,
      displayName: json['display_name'] as String?,
      value: (json['value'] as num?)?.toDouble(),
      unit: json['unit'] as String?,
      classification:
          AnalyteClassification.fromString(json['classification'] as String?),
      referenceLow: (json['reference_low'] as num?)?.toDouble(),
      referenceHigh: (json['reference_high'] as num?)?.toDouble(),
      referenceSource: json['reference_source'] as String?,
      analysisStatus: json['analysis_status'] as String?,
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
    );
  }

  Map<String, dynamic> toJson() => {
        'test_name': testName,
        if (canonicalName != null) 'canonical_name': canonicalName,
        if (displayName != null) 'display_name': displayName,
        if (value != null) 'value': value,
        if (unit != null) 'unit': unit,
        if (classification != null) 'classification': classification!.value,
        if (referenceLow != null) 'reference_low': referenceLow,
        if (referenceHigh != null) 'reference_high': referenceHigh,
        if (referenceSource != null) 'reference_source': referenceSource,
        if (analysisStatus != null) 'analysis_status': analysisStatus,
        'warnings': warnings,
      };

  @override
  List<Object?> get props => [
        testName,
        canonicalName,
        displayName,
        value,
        unit,
        classification,
        referenceLow,
        referenceHigh,
        referenceSource,
        analysisStatus,
        warnings,
      ];
}

/// Pre-computed disease risk estimation fed to GenAI.
class MLRiskSummary extends Equatable {
  final String condition;
  final double riskProbability;
  final RiskBand riskBand;
  final String? modelName;
  final String? modelVersion;
  final String status;

  const MLRiskSummary({
    required this.condition,
    required this.riskProbability,
    required this.riskBand,
    this.modelName,
    this.modelVersion,
    this.status = 'OK',
  });

  factory MLRiskSummary.fromJson(Map<String, dynamic> json) {
    return MLRiskSummary(
      condition: json['condition'] as String? ?? '',
      riskProbability:
          (json['risk_probability'] as num?)?.toDouble() ?? 0.0,
      riskBand: RiskBand.fromString(json['risk_band'] as String?) ??
          RiskBand.low,
      modelName: json['model_name'] as String?,
      modelVersion: json['model_version'] as String?,
      status: json['status'] as String? ?? 'OK',
    );
  }

  Map<String, dynamic> toJson() => {
        'condition': condition,
        'risk_probability': riskProbability,
        'risk_band': riskBand.value,
        if (modelName != null) 'model_name': modelName,
        if (modelVersion != null) 'model_version': modelVersion,
        'status': status,
      };

  @override
  List<Object?> get props =>
      [condition, riskProbability, riskBand, modelName, modelVersion, status];
}

/// Structured request payload for POST /api/v1/genai/explain.
class GenAIExplainRequest extends Equatable {
  final int? reportId;
  final bool persist;
  final bool isUserVerified;
  final double? patientAge;
  final String? patientSex;
  final List<VerifiedAnalyteSummary> analytes;
  final List<MLRiskSummary> mlRisks;
  final SupportedLanguage language;
  final DetailLevel detailLevel;

  const GenAIExplainRequest({
    this.reportId,
    this.persist = false,
    required this.isUserVerified,
    this.patientAge,
    this.patientSex,
    this.analytes = const [],
    this.mlRisks = const [],
    this.language = SupportedLanguage.english,
    this.detailLevel = DetailLevel.simple,
  });

  Map<String, dynamic> toJson() => {
        if (reportId != null) 'report_id': reportId,
        'persist': persist,
        'is_user_verified': isUserVerified,
        if (patientAge != null) 'patient_age': patientAge,
        if (patientSex != null) 'patient_sex': patientSex,
        'analytes': analytes.map((a) => a.toJson()).toList(),
        'ml_risks': mlRisks.map((r) => r.toJson()).toList(),
        'language': language.code,
        'detail_level': detailLevel.value,
      };

  @override
  List<Object?> get props => [
        reportId,
        persist,
        isUserVerified,
        patientAge,
        patientSex,
        analytes,
        mlRisks,
        language,
        detailLevel,
      ];
}
