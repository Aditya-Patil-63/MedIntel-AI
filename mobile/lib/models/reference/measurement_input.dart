import 'package:equatable/equatable.dart';
import 'patient_context.dart';

/// Individual medical measurement submitted for reference analysis.
class MeasurementInput extends Equatable {
  final String testName;
  final dynamic value;
  final String? unit;
  final String? testValueText;
  final bool isUserVerified;
  final PatientContext? context;

  const MeasurementInput({
    required this.testName,
    this.value,
    this.unit,
    this.testValueText,
    this.isUserVerified = false,
    this.context,
  });

  factory MeasurementInput.fromJson(Map<String, dynamic> json) {
    return MeasurementInput(
      testName: json['test_name'] as String? ?? '',
      value: json['value'],
      unit: json['unit'] as String?,
      testValueText: json['test_value_text'] as String?,
      isUserVerified: json['is_user_verified'] as bool? ?? false,
      context: json['context'] != null
          ? PatientContext.fromJson(json['context'] as Map<String, dynamic>)
          : null,
    );
  }

  Map<String, dynamic> toJson() => {
        'test_name': testName,
        if (value != null) 'value': value,
        if (unit != null) 'unit': unit,
        if (testValueText != null) 'test_value_text': testValueText,
        'is_user_verified': isUserVerified,
        if (context != null) 'context': context!.toJson(),
      };

  MeasurementInput copyWith({
    String? testName,
    dynamic value,
    String? unit,
    String? testValueText,
    bool? isUserVerified,
    PatientContext? context,
  }) {
    return MeasurementInput(
      testName: testName ?? this.testName,
      value: value ?? this.value,
      unit: unit ?? this.unit,
      testValueText: testValueText ?? this.testValueText,
      isUserVerified: isUserVerified ?? this.isUserVerified,
      context: context ?? this.context,
    );
  }

  @override
  List<Object?> get props =>
      [testName, value, unit, testValueText, isUserVerified, context];
}
