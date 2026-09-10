import 'package:equatable/equatable.dart';
import 'analysis_result.dart';
import 'measurement_input.dart';
import 'patient_context.dart';

/// Request payload for POST /api/v1/reference/analyze.
class BatchAnalysisRequest extends Equatable {
  final List<MeasurementInput> measurements;
  final PatientContext? patientContext;
  final int? reportId;
  final bool persist;

  const BatchAnalysisRequest({
    required this.measurements,
    this.patientContext,
    this.reportId,
    this.persist = false,
  });

  Map<String, dynamic> toJson() => {
        'measurements': measurements.map((m) => m.toJson()).toList(),
        if (patientContext != null)
          'patient_context': patientContext!.toJson(),
        if (reportId != null) 'report_id': reportId,
        'persist': persist,
      };

  @override
  List<Object?> get props => [measurements, patientContext, reportId, persist];
}

/// Response payload for POST /api/v1/reference/analyze.
class BatchAnalysisResponse extends Equatable {
  final bool success;
  final int totalSubmitted;
  final int totalClassified;
  final int? reportId;
  final List<AnalysisResult> results;
  final String disclaimer;

  const BatchAnalysisResponse({
    this.success = true,
    required this.totalSubmitted,
    required this.totalClassified,
    this.reportId,
    required this.results,
    this.disclaimer =
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
  });

  factory BatchAnalysisResponse.fromJson(Map<String, dynamic> json) {
    return BatchAnalysisResponse(
      success: json['success'] as bool? ?? true,
      totalSubmitted: (json['total_submitted'] as num?)?.toInt() ?? 0,
      totalClassified: (json['total_classified'] as num?)?.toInt() ?? 0,
      reportId: (json['report_id'] as num?)?.toInt(),
      results: (json['results'] as List<dynamic>?)
              ?.map((e) => AnalysisResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      disclaimer: json['disclaimer'] as String? ??
          'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
    );
  }

  Map<String, dynamic> toJson() => {
        'success': success,
        'total_submitted': totalSubmitted,
        'total_classified': totalClassified,
        if (reportId != null) 'report_id': reportId,
        'results': results.map((r) => r.toJson()).toList(),
        'disclaimer': disclaimer,
      };

  @override
  List<Object?> get props => [
        success,
        totalSubmitted,
        totalClassified,
        reportId,
        results,
        disclaimer,
      ];
}
