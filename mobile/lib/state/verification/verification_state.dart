import 'package:equatable/equatable.dart';
import '../../models/reference/editable_measurement.dart';
import '../../models/reference/patient_context.dart';

/// State of the human-in-the-loop medical verification gate.
class VerificationState extends Equatable {
  final List<EditableMeasurement> measurements;
  final PatientContext patientContext;
  final bool isVerified;
  final bool isParsing;
  final String? statusMessage;
  final String? errorMessage;

  const VerificationState({
    this.measurements = const [],
    this.patientContext = const PatientContext(),
    this.isVerified = false,
    this.isParsing = false,
    this.statusMessage,
    this.errorMessage,
  });

  int get unverifiedCount => measurements
      .where((m) => m.status == VerificationItemStatus.unverified)
      .length;

  int get confirmedCount => measurements
      .where((m) => m.status == VerificationItemStatus.confirmed)
      .length;

  int get correctedCount => measurements
      .where((m) => m.status == VerificationItemStatus.corrected)
      .length;

  bool get hasItems => measurements.isNotEmpty;

  VerificationState copyWith({
    List<EditableMeasurement>? measurements,
    PatientContext? patientContext,
    bool? isVerified,
    bool? isParsing,
    String? statusMessage,
    String? errorMessage,
  }) {
    return VerificationState(
      measurements: measurements ?? this.measurements,
      patientContext: patientContext ?? this.patientContext,
      isVerified: isVerified ?? this.isVerified,
      isParsing: isParsing ?? this.isParsing,
      statusMessage: statusMessage,
      errorMessage: errorMessage,
    );
  }

  @override
  List<Object?> get props => [
        measurements,
        patientContext,
        isVerified,
        isParsing,
        statusMessage,
        errorMessage,
      ];
}
