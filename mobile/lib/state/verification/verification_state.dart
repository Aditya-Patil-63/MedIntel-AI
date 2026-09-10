import 'package:equatable/equatable.dart';
import '../../models/reference/measurement_input.dart';

class VerificationState extends Equatable {
  final List<MeasurementInput> measurements;
  final bool isVerified;
  final String? errorMessage;

  const VerificationState({
    this.measurements = const [],
    this.isVerified = false,
    this.errorMessage,
  });

  VerificationState copyWith({
    List<MeasurementInput>? measurements,
    bool? isVerified,
    String? errorMessage,
  }) {
    return VerificationState(
      measurements: measurements ?? this.measurements,
      isVerified: isVerified ?? this.isVerified,
      errorMessage: errorMessage,
    );
  }

  @override
  List<Object?> get props => [measurements, isVerified, errorMessage];
}
