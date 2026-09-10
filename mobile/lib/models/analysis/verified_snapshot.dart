import 'package:equatable/equatable.dart';
import '../reference/editable_measurement.dart';
import '../reference/patient_context.dart';

/// Immutable snapshot of user-verified clinical measurements and demographic context
/// captured at the exact moment of confirmation gate approval.
class VerifiedSnapshot extends Equatable {
  final String id;
  final DateTime timestamp;
  final List<EditableMeasurement> measurements;
  final PatientContext patientContext;
  final bool isVerified;

  VerifiedSnapshot({
    String? id,
    DateTime? timestamp,
    required List<EditableMeasurement> measurements,
    required this.patientContext,
    required this.isVerified,
  })  : id = id ?? 'snap_${DateTime.now().millisecondsSinceEpoch}',
        timestamp = timestamp ?? DateTime.now(),
        measurements = List<EditableMeasurement>.unmodifiable(measurements);

  /// Empty or unverified initial snapshot
  static final VerifiedSnapshot empty = VerifiedSnapshot(
    measurements: const [],
    patientContext: const PatientContext(),
    isVerified: false,
  );

  int get measurementCount => measurements.length;

  bool get hasMeasurements => measurements.isNotEmpty;

  @override
  List<Object?> get props => [id, timestamp, measurements, patientContext, isVerified];
}
