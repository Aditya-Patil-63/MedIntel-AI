import 'package:equatable/equatable.dart';

/// Patient context for reference range customization.
class PatientContext extends Equatable {
  final double? age;
  final String? sex;

  const PatientContext({this.age, this.sex});

  factory PatientContext.fromJson(Map<String, dynamic> json) {
    return PatientContext(
      age: (json['age'] as num?)?.toDouble(),
      sex: json['sex'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        if (age != null) 'age': age,
        if (sex != null) 'sex': sex,
      };

  @override
  List<Object?> get props => [age, sex];
}
