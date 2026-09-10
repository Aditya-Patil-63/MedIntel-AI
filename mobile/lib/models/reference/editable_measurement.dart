import 'package:equatable/equatable.dart';
import 'measurement_input.dart';

/// Verification status for an individual clinical measurement.
enum VerificationItemStatus {
  /// Extracted or parsed from report, not yet reviewed/confirmed by user.
  unverified('UNVERIFIED'),

  /// User reviewed and accepted without modifying the extracted value.
  confirmed('CONFIRMED'),

  /// User reviewed and modified test name, value, or unit.
  corrected('CORRECTED');

  final String label;
  const VerificationItemStatus(this.label);
}

/// Indicates whether measurement was extracted via OCR/parser or manually added.
enum MeasurementOrigin {
  extracted,
  manual,
}

/// Editable representation of a clinical measurement in the verification UI.
class EditableMeasurement extends Equatable {
  final String id;
  final String testName;
  final dynamic value;
  final String? unit;
  final String? parserStatus;
  final String? extractedReferenceRange;
  final double extractionConfidence;
  final VerificationItemStatus status;
  final MeasurementOrigin origin;
  final String originalTestName;
  final dynamic originalValue;
  final String? originalUnit;

  const EditableMeasurement({
    required this.id,
    required this.testName,
    this.value,
    this.unit,
    this.parserStatus,
    this.extractedReferenceRange,
    this.extractionConfidence = 1.0,
    this.status = VerificationItemStatus.unverified,
    this.origin = MeasurementOrigin.extracted,
    required this.originalTestName,
    this.originalValue,
    this.originalUnit,
  });

  /// Factory constructing from raw parser output (always unverified).
  factory EditableMeasurement.fromParsedItem({
    required String id,
    required String testName,
    dynamic value,
    String? unit,
    String? parserStatus,
    String? extractedReferenceRange,
    double extractionConfidence = 1.0,
  }) {
    return EditableMeasurement(
      id: id,
      testName: testName,
      value: value,
      unit: unit,
      parserStatus: parserStatus,
      extractedReferenceRange: extractedReferenceRange,
      extractionConfidence: extractionConfidence,
      status: VerificationItemStatus.unverified,
      origin: MeasurementOrigin.extracted,
      originalTestName: testName,
      originalValue: value,
      originalUnit: unit,
    );
  }

  /// True if user altered name, value, or unit compared to original extraction.
  bool get isEdited {
    return testName != originalTestName ||
        value != originalValue ||
        unit != originalUnit;
  }

  /// Whether measurement is verified (confirmed or corrected).
  bool get isUserVerified => status != VerificationItemStatus.unverified;

  /// Converts to backend MeasurementInput schema.
  MeasurementInput toMeasurementInput({bool? forceVerified}) {
    return MeasurementInput(
      testName: testName,
      value: value,
      unit: unit,
      isUserVerified: forceVerified ?? (status != VerificationItemStatus.unverified),
    );
  }

  EditableMeasurement copyWith({
    String? id,
    String? testName,
    dynamic value,
    String? unit,
    String? parserStatus,
    String? extractedReferenceRange,
    double? extractionConfidence,
    VerificationItemStatus? status,
    MeasurementOrigin? origin,
    String? originalTestName,
    dynamic originalValue,
    String? originalUnit,
  }) {
    return EditableMeasurement(
      id: id ?? this.id,
      testName: testName ?? this.testName,
      value: value ?? this.value,
      unit: unit ?? this.unit,
      parserStatus: parserStatus ?? this.parserStatus,
      extractedReferenceRange:
          extractedReferenceRange ?? this.extractedReferenceRange,
      extractionConfidence:
          extractionConfidence ?? this.extractionConfidence,
      status: status ?? this.status,
      origin: origin ?? this.origin,
      originalTestName: originalTestName ?? this.originalTestName,
      originalValue: originalValue ?? this.originalValue,
      originalUnit: originalUnit ?? this.originalUnit,
    );
  }

  @override
  List<Object?> get props => [
        id,
        testName,
        value,
        unit,
        parserStatus,
        extractedReferenceRange,
        extractionConfidence,
        status,
        origin,
        originalTestName,
        originalValue,
        originalUnit,
      ];
}
