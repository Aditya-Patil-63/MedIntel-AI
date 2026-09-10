import 'package:equatable/equatable.dart';
import '../common/enums.dart';
import 'page_extraction.dart';

/// Overall document extraction outcome from POST /api/v1/extract.
class DocumentExtractionResult extends Equatable {
  final bool success;
  final String filename;
  final SourceType sourceType;
  final String extractor;
  final int totalPages;
  final List<PageExtraction> pages;
  final String fullText;
  final double confidence;
  final List<String> warnings;
  final List<String> errors;
  final String disclaimer;

  const DocumentExtractionResult({
    required this.success,
    required this.filename,
    required this.sourceType,
    required this.extractor,
    this.totalPages = 0,
    this.pages = const [],
    this.fullText = '',
    this.confidence = 1.0,
    this.warnings = const [],
    this.errors = const [],
    this.disclaimer =
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
  });

  factory DocumentExtractionResult.fromJson(Map<String, dynamic> json) {
    return DocumentExtractionResult(
      success: json['success'] as bool? ?? false,
      filename: json['filename'] as String? ?? '',
      sourceType: SourceType.fromString(json['source_type'] as String?),
      extractor: json['extractor'] as String? ?? '',
      totalPages: (json['total_pages'] as num?)?.toInt() ?? 0,
      pages: (json['pages'] as List<dynamic>?)
              ?.map((e) => PageExtraction.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      fullText: json['full_text'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
      warnings: (json['warnings'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      errors: (json['errors'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      disclaimer: json['disclaimer'] as String? ??
          'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
    );
  }

  Map<String, dynamic> toJson() => {
        'success': success,
        'filename': filename,
        'source_type': sourceType.value,
        'extractor': extractor,
        'total_pages': totalPages,
        'pages': pages.map((e) => e.toJson()).toList(),
        'full_text': fullText,
        'confidence': confidence,
        'warnings': warnings,
        'errors': errors,
        'disclaimer': disclaimer,
      };

  @override
  List<Object?> get props => [
        success,
        filename,
        sourceType,
        extractor,
        totalPages,
        pages,
        fullText,
        confidence,
        warnings,
        errors,
        disclaimer,
      ];
}
