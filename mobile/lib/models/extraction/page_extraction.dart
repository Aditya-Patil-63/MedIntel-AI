import 'package:equatable/equatable.dart';

/// Extracted text and metadata for a single page.
class PageExtraction extends Equatable {
  final int pageNumber;
  final String text;
  final double confidence;
  final int charCount;
  final int wordCount;

  const PageExtraction({
    required this.pageNumber,
    required this.text,
    this.confidence = 1.0,
    this.charCount = 0,
    this.wordCount = 0,
  });

  factory PageExtraction.fromJson(Map<String, dynamic> json) {
    return PageExtraction(
      pageNumber: (json['page_number'] as num?)?.toInt() ?? 1,
      text: json['text'] as String? ?? '',
      confidence: (json['confidence'] as num?)?.toDouble() ?? 1.0,
      charCount: (json['char_count'] as num?)?.toInt() ?? 0,
      wordCount: (json['word_count'] as num?)?.toInt() ?? 0,
    );
  }

  Map<String, dynamic> toJson() => {
        'page_number': pageNumber,
        'text': text,
        'confidence': confidence,
        'char_count': charCount,
        'word_count': wordCount,
      };

  @override
  List<Object?> get props => [pageNumber, text, confidence, charCount, wordCount];
}
