import 'package:equatable/equatable.dart';
import '../common/enums.dart';
import 'reference_range_summary.dart';

/// Structured analysis outcome for an individual measurement.
class AnalysisResult extends Equatable {
  final String originalTestName;
  final String? canonicalName;
  final double? numericValue;
  final String? originalValueText;
  final String? unit;
  final String? normalizedUnit;
  final AnalyteClassification? classification;
  final String analysisStatus;
  final ReferenceRangeSummary? referenceRange;
  final String? referenceSource;
  final bool isUserVerified;
  final int? persistedTestResultId;
  final List<String> warnings;
  final String disclaimer;

  const AnalysisResult({
    required this.originalTestName,
    this.canonicalName,
    this.numericValue,
    this.originalValueText,
    this.unit,
    this.normalizedUnit,
    this.classification,
    required this.analysisStatus,
    this.referenceRange,
    this.referenceSource,
    this.isUserVerified = false,
    this.persistedTestResultId,
    this.warnings = const [],
    this.disclaimer =
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
  });

  factory AnalysisResult.fromJson(Map<String, dynamic> json) {
    return AnalysisResult(
      originalTestName: json['original_test_name'] as String? ?? '',
      canonicalName: json['canonical_name'] as String?,
      numericValue: (json['numeric_value'] as num?)?.toDouble(),
      originalValueText: json['original_value_text'] as String?,
      unit: json['unit'] as String?,
      normalizedUnit: json['normalized_unit'] as String?,
      classification:
          AnalyteClassification.fromString(json['classification'] as String?),
      analysisStatus: json['analysis_status'] as String? ?? 'UNKNOWN',
      referenceRange: json['reference_range'] != null
          ? ReferenceRangeSummary.fromJson(
              json['reference_range'] as Map<String, dynamic>)
          : null,
      referenceSource: json['reference_source'] as String?,
      isUserVerified: json['is_user_verified'] as bool? ?? false,
      persistedTestResultId: (json['persisted_test_result_id'] as num?)?.toInt(),
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      disclaimer: json['disclaimer'] as String? ??
          'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
    );
  }

  Map<String, dynamic> toJson() => {
        'original_test_name': originalTestName,
        if (canonicalName != null) 'canonical_name': canonicalName,
        if (numericValue != null) 'numeric_value': numericValue,
        if (originalValueText != null)
          'original_value_text': originalValueText,
        if (unit != null) 'unit': unit,
        if (normalizedUnit != null) 'normalized_unit': normalizedUnit,
        if (classification != null) 'classification': classification!.value,
        'analysis_status': analysisStatus,
        if (referenceRange != null)
          'reference_range': referenceRange!.toJson(),
        if (referenceSource != null) 'reference_source': referenceSource,
        'is_user_verified': isUserVerified,
        if (persistedTestResultId != null)
          'persisted_test_result_id': persistedTestResultId,
        'warnings': warnings,
        'disclaimer': disclaimer,
      };

  @override
  List<Object?> get props => [
        originalTestName,
        canonicalName,
        numericValue,
        originalValueText,
        unit,
        normalizedUnit,
        classification,
        analysisStatus,
        referenceRange,
        referenceSource,
        isUserVerified,
        persistedTestResultId,
        warnings,
        disclaimer,
      ];
}
