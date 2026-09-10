import 'package:equatable/equatable.dart';

/// Features for heart disease risk prediction (Cleveland benchmark).
class HeartDiseaseRiskRequest extends Equatable {
  final double? age;
  final double? sex;
  final double? cp;
  final double? trestbps;
  final double? chol;
  final double? fbs;
  final double? restecg;
  final double? thalach;
  final double? exang;
  final double? oldpeak;
  final double? slope;
  final double? ca;
  final double? thal;
  final bool isUserVerified;
  final int? reportId;

  const HeartDiseaseRiskRequest({
    this.age,
    this.sex,
    this.cp,
    this.trestbps,
    this.chol,
    this.fbs,
    this.restecg,
    this.thalach,
    this.exang,
    this.oldpeak,
    this.slope,
    this.ca,
    this.thal,
    this.isUserVerified = true,
    this.reportId,
  });

  factory HeartDiseaseRiskRequest.fromJson(Map<String, dynamic> json) {
    return HeartDiseaseRiskRequest(
      age: (json['age'] as num?)?.toDouble(),
      sex: (json['sex'] as num?)?.toDouble(),
      cp: (json['cp'] as num?)?.toDouble(),
      trestbps: (json['trestbps'] as num?)?.toDouble(),
      chol: (json['chol'] as num?)?.toDouble(),
      fbs: (json['fbs'] as num?)?.toDouble(),
      restecg: (json['restecg'] as num?)?.toDouble(),
      thalach: (json['thalach'] as num?)?.toDouble(),
      exang: (json['exang'] as num?)?.toDouble(),
      oldpeak: (json['oldpeak'] as num?)?.toDouble(),
      slope: (json['slope'] as num?)?.toDouble(),
      ca: (json['ca'] as num?)?.toDouble(),
      thal: (json['thal'] as num?)?.toDouble(),
      isUserVerified: json['is_user_verified'] as bool? ?? true,
      reportId: (json['report_id'] as num?)?.toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
        if (age != null) 'age': age,
        if (sex != null) 'sex': sex,
        if (cp != null) 'cp': cp,
        if (trestbps != null) 'trestbps': trestbps,
        if (chol != null) 'chol': chol,
        if (fbs != null) 'fbs': fbs,
        if (restecg != null) 'restecg': restecg,
        if (thalach != null) 'thalach': thalach,
        if (exang != null) 'exang': exang,
        if (oldpeak != null) 'oldpeak': oldpeak,
        if (slope != null) 'slope': slope,
        if (ca != null) 'ca': ca,
        if (thal != null) 'thal': thal,
        'is_user_verified': isUserVerified,
        if (reportId != null) 'report_id': reportId,
      };

  @override
  List<Object?> get props => [
        age,
        sex,
        cp,
        trestbps,
        chol,
        fbs,
        restecg,
        thalach,
        exang,
        oldpeak,
        slope,
        ca,
        thal,
        isUserVerified,
        reportId,
      ];
}
