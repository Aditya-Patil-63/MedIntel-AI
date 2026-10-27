import 'package:equatable/equatable.dart';

/// Extracted patient demographic and report administrative details.
/// If any value is missing from the report, it strictly defaults to 'Not Available'.
class PatientDetails extends Equatable {
  final String name;
  final double? age;
  final String ageDisplay;
  final String gender;
  final String date;
  final String labName;

  const PatientDetails({
    this.name = 'Not Available',
    this.age,
    this.ageDisplay = 'Not Available',
    this.gender = 'Not Available',
    this.date = 'Not Available',
    this.labName = 'Not Available',
  });

  factory PatientDetails.fromJson(Map<String, dynamic>? json) {
    if (json == null) return const PatientDetails();
    return PatientDetails(
      name: json['name'] as String? ?? 'Not Available',
      age: (json['age'] as num?)?.toDouble(),
      ageDisplay: json['age_display'] as String? ??
          ((json['age'] != null) ? '${json['age']} Y' : 'Not Available'),
      gender: json['gender'] as String? ?? 'Not Available',
      date: json['date'] as String? ?? 'Not Available',
      labName: json['lab_name'] as String? ?? 'Not Available',
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        if (age != null) 'age': age,
        'age_display': ageDisplay,
        'gender': gender,
        'date': date,
        'lab_name': labName,
      };

  String get effectiveAgeDisplay {
    if (ageDisplay != 'Not Available' && ageDisplay.isNotEmpty) return ageDisplay;
    if (age != null) return '${age!.toInt()} Y';
    return 'Not Available';
  }

  String get summaryText {
    final parts = <String>[];
    if (name != 'Not Available') parts.add(name);
    if (effectiveAgeDisplay != 'Not Available') parts.add(effectiveAgeDisplay);
    if (gender != 'Not Available') parts.add(gender);
    if (parts.isEmpty) return 'Not Available';
    return parts.join(', ');
  }

  @override
  List<Object?> get props => [name, age, ageDisplay, gender, date, labName];
}
