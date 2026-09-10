import 'package:equatable/equatable.dart';
import 'analysis_result.dart';
import 'patient_context.dart';

/// Request payload for POST /api/v1/reference/parse-and-analyze.
class ParseAndAnalyzeRequest extends Equatable {
  final String text;
  final PatientContext? patientContext;
  final int? reportId;
  final bool persist;
  final bool isUserVerified;
  final bool includeUnrecognized;

  const ParseAndAnalyzeRequest({
    required this.text,
    this.patientContext,
    this.reportId,
    this.persist = false,
    this.isUserVerified = false,
    this.includeUnrecognized = false,
  });

  Map<String, dynamic> toJson() => {
        'text': text,
        if (patientContext != null)
          'patient_context': patientContext!.toJson(),
        if (reportId != null) 'report_id': reportId,
        'persist': persist,
        'is_user_verified': isUserVerified,
        'include_unrecognized': includeUnrecognized,
      };

  @override
  List<Object?> get props => [
        text,
        patientContext,
        reportId,
        persist,
        isUserVerified,
        includeUnrecognized,
      ];
}

/// Item in ParseAndAnalyzeResponse.
class ParsedAndAnalyzedItem extends Equatable {
  final String parsedLine;
  final String? parsedAnalyte;
  final String? canonicalName;
  final String parserStatus;
  final String? extractedReferenceRange;
  final double extractionConfidence;
  final AnalysisResult? analysis;

  const ParsedAndAnalyzedItem({
    required this.parsedLine,
    this.parsedAnalyte,
    this.canonicalName,
    required this.parserStatus,
    this.extractedReferenceRange,
    required this.extractionConfidence,
    this.analysis,
  });

  factory ParsedAndAnalyzedItem.fromJson(Map<String, dynamic> json) {
    return ParsedAndAnalyzedItem(
      parsedLine: json['parsed_line'] as String? ?? '',
      parsedAnalyte: json['parsed_analyte'] as String?,
      canonicalName: json['canonical_name'] as String?,
      parserStatus: json['parser_status'] as String? ?? '',
      extractedReferenceRange: json['extracted_reference_range'] as String?,
      extractionConfidence:
          (json['extraction_confidence'] as num?)?.toDouble() ?? 0.0,
      analysis: json['analysis'] != null
          ? AnalysisResult.fromJson(json['analysis'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'parsed_line': parsedLine,
        if (parsedAnalyte != null) 'parsed_analyte': parsedAnalyte,
        if (canonicalName != null) 'canonical_name': canonicalName,
        'parser_status': parserStatus,
        if (extractedReferenceRange != null)
          'extracted_reference_range': extractedReferenceRange,
        'extraction_confidence': extractionConfidence,
        if (analysis != null) 'analysis': analysis!.toJson(),
      };

  @override
  List<Object?> get props => [
        parsedLine,
        parsedAnalyte,
        canonicalName,
        parserStatus,
        extractedReferenceRange,
        extractionConfidence,
        analysis,
      ];
}

/// Response payload for POST /api/v1/reference/parse-and-analyze.
class ParseAndAnalyzeResponse extends Equatable {
  final bool success;
  final int totalLinesParsed;
  final int totalMeasurementsAnalyzed;
  final int? reportId;
  final List<ParsedAndAnalyzedItem> items;
  final String disclaimer;

  const ParseAndAnalyzeResponse({
    this.success = true,
    required this.totalLinesParsed,
    required this.totalMeasurementsAnalyzed,
    this.reportId,
    required this.items,
    this.disclaimer =
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
  });

  factory ParseAndAnalyzeResponse.fromJson(Map<String, dynamic> json) {
    return ParseAndAnalyzeResponse(
      success: json['success'] as bool? ?? true,
      totalLinesParsed: (json['total_lines_parsed'] as num?)?.toInt() ?? 0,
      totalMeasurementsAnalyzed:
          (json['total_measurements_analyzed'] as num?)?.toInt() ?? 0,
      reportId: (json['report_id'] as num?)?.toInt(),
      items: (json['items'] as List<dynamic>?)
              ?.map(
                  (e) => ParsedAndAnalyzedItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      disclaimer: json['disclaimer'] as String? ??
          'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
    );
  }

  Map<String, dynamic> toJson() => {
        'success': success,
        'total_lines_parsed': totalLinesParsed,
        'total_measurements_analyzed': totalMeasurementsAnalyzed,
        if (reportId != null) 'report_id': reportId,
        'items': items.map((e) => e.toJson()).toList(),
        'disclaimer': disclaimer,
      };

  @override
  List<Object?> get props => [
        success,
        totalLinesParsed,
        totalMeasurementsAnalyzed,
        reportId,
        items,
        disclaimer,
      ];
}
