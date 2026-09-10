/// Document source classification.
enum SourceType {
  digitalPdf('digital_pdf'),
  scannedPdf('scanned_pdf'),
  image('image'),
  unknown('unknown');

  final String value;
  const SourceType(this.value);

  static SourceType fromString(String? val) {
    return SourceType.values.firstWhere(
      (e) => e.value == val,
      orElse: () => SourceType.unknown,
    );
  }
}

/// OCR engine used for document processing.
enum OCREngineType {
  tesseract('tesseract'),
  easyocr('easyocr'),
  pdfplumber('pdfplumber'),
  none('none');

  final String value;
  const OCREngineType(this.value);

  static OCREngineType fromString(String? val) {
    return OCREngineType.values.firstWhere(
      (e) => e.value == val,
      orElse: () => OCREngineType.none,
    );
  }
}

/// Deterministic clinical classification from Phase 6.
enum AnalyteClassification {
  low('LOW'),
  normal('NORMAL'),
  high('HIGH'),
  critical('CRITICAL');

  final String value;
  const AnalyteClassification(this.value);

  static AnalyteClassification? fromString(String? val) {
    if (val == null) return null;
    return AnalyteClassification.values.firstWhere(
      (e) => e.value == val.toUpperCase(),
      orElse: () => AnalyteClassification.normal,
    );
  }
}

/// Educational disease risk band from Phase 7.
enum RiskBand {
  low('LOW'),
  moderate('MODERATE'),
  elevated('ELEVATED');

  final String value;
  const RiskBand(this.value);

  static RiskBand? fromString(String? val) {
    if (val == null) return null;
    return RiskBand.values.firstWhere(
      (e) => e.value == val.toUpperCase(),
      orElse: () => RiskBand.low,
    );
  }
}

/// Multilingual explanation languages.
enum SupportedLanguage {
  english('en'),
  hindi('hi'),
  marathi('mr'),
  gujarati('gu');

  final String code;
  const SupportedLanguage(this.code);

  static SupportedLanguage fromCode(String? code) {
    return SupportedLanguage.values.firstWhere(
      (e) => e.code == code,
      orElse: () => SupportedLanguage.english,
    );
  }
}

/// Explanation complexity level.
enum DetailLevel {
  simple('simple'),
  detailed('detailed');

  final String value;
  const DetailLevel(this.value);

  static DetailLevel fromString(String? val) {
    return DetailLevel.values.firstWhere(
      (e) => e.value == val,
      orElse: () => DetailLevel.simple,
    );
  }
}

/// GenAI operational status.
enum GenAIStatus {
  success('SUCCESS'),
  verificationRequired('VERIFICATION_REQUIRED'),
  providerError('PROVIDER_ERROR'),
  invalidInput('INVALID_INPUT'),
  unsupportedLanguage('UNSUPPORTED_LANGUAGE');

  final String value;
  const GenAIStatus(this.value);

  static GenAIStatus fromString(String? val) {
    return GenAIStatus.values.firstWhere(
      (e) => e.value == val,
      orElse: () => GenAIStatus.providerError,
    );
  }
}
