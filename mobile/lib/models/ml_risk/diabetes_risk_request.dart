import 'package:equatable/equatable.dart';

/// Features for diabetes risk prediction (Pima Indians benchmark).
class DiabetesRiskRequest extends Equatable {
  final double? pregnancies;
  final double? glucose;
  final double? bloodPressure;
  final double? skinThickness;
  final double? insulin;
  final double? bmi;
  final double? diabetesPedigreeFunction;
  final double? age;
  final bool isUserVerified;
  final int? reportId;

  const DiabetesRiskRequest({
    this.pregnancies,
    this.glucose,
    this.bloodPressure,
    this.skinThickness,
    this.insulin,
    this.bmi,
    this.diabetesPedigreeFunction,
    this.age,
    this.isUserVerified = true,
    this.reportId,
  });

  factory DiabetesRiskRequest.fromJson(Map<String, dynamic> json) {
    return DiabetesRiskRequest(
      pregnancies: (json['Pregnancies'] as num?)?.toDouble(),
      glucose: (json['Glucose'] as num?)?.toDouble(),
      bloodPressure: (json['BloodPressure'] as num?)?.toDouble(),
      skinThickness: (json['SkinThickness'] as num?)?.toDouble(),
      insulin: (json['Insulin'] as num?)?.toDouble(),
      bmi: (json['BMI'] as num?)?.toDouble(),
      diabetesPedigreeFunction:
          (json['DiabetesPedigreeFunction'] as num?)?.toDouble(),
      age: (json['Age'] as num?)?.toDouble(),
      isUserVerified: json['is_user_verified'] as bool? ?? true,
      reportId: (json['report_id'] as num?)?.toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
        if (pregnancies != null) 'Pregnancies': pregnancies,
        if (glucose != null) 'Glucose': glucose,
        if (bloodPressure != null) 'BloodPressure': bloodPressure,
        if (skinThickness != null) 'SkinThickness': skinThickness,
        if (insulin != null) 'Insulin': insulin,
        if (bmi != null) 'BMI': bmi,
        if (diabetesPedigreeFunction != null)
          'DiabetesPedigreeFunction': diabetesPedigreeFunction,
        if (age != null) 'Age': age,
        'is_user_verified': isUserVerified,
        if (reportId != null) 'report_id': reportId,
      };

  @override
  List<Object?> get props => [
        pregnancies,
        glucose,
        bloodPressure,
        skinThickness,
        insulin,
        bmi,
        diabetesPedigreeFunction,
        age,
        isUserVerified,
        reportId,
      ];
}
