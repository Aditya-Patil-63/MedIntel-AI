import 'package:equatable/equatable.dart';

/// Applied medical reference range summary.
class ReferenceRangeSummary extends Equatable {
  final String canonicalName;
  final String unit;
  final double? normalLow;
  final double? normalHigh;
  final double? criticalLow;
  final double? criticalHigh;
  final String source;
  final String? citation;
  final String referenceType;
  final String verificationStatus;

  const ReferenceRangeSummary({
    required this.canonicalName,
    required this.unit,
    this.normalLow,
    this.normalHigh,
    this.criticalLow,
    this.criticalHigh,
    required this.source,
    this.citation,
    this.referenceType = 'GENERAL_REFERENCE',
    this.verificationStatus = 'VERIFIED',
  });

  factory ReferenceRangeSummary.fromJson(Map<String, dynamic> json) {
    return ReferenceRangeSummary(
      canonicalName: json['canonical_name'] as String? ?? '',
      unit: json['unit'] as String? ?? '',
      normalLow: (json['normal_low'] as num?)?.toDouble(),
      normalHigh: (json['normal_high'] as num?)?.toDouble(),
      criticalLow: (json['critical_low'] as num?)?.toDouble(),
      criticalHigh: (json['critical_high'] as num?)?.toDouble(),
      source: json['source'] as String? ?? '',
      citation: json['citation'] as String?,
      referenceType: json['reference_type'] as String? ?? 'GENERAL_REFERENCE',
      verificationStatus: json['verification_status'] as String? ?? 'VERIFIED',
    );
  }

  Map<String, dynamic> toJson() => {
        'canonical_name': canonicalName,
        'unit': unit,
        if (normalLow != null) 'normal_low': normalLow,
        if (normalHigh != null) 'normal_high': normalHigh,
        if (criticalLow != null) 'critical_low': criticalLow,
        if (criticalHigh != null) 'critical_high': criticalHigh,
        'source': source,
        if (citation != null) 'citation': citation,
        'reference_type': referenceType,
        'verification_status': verificationStatus,
      };

  @override
  List<Object?> get props => [
        canonicalName,
        unit,
        normalLow,
        normalHigh,
        criticalLow,
        criticalHigh,
        source,
        citation,
        referenceType,
        verificationStatus,
      ];
}
