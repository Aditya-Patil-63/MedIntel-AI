import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/reference/measurement_input.dart';
import 'verification_state.dart';

/// Manages user review and mandatory confirmation of extracted measurements.
class VerificationCubit extends Cubit<VerificationState> {
  VerificationCubit() : super(const VerificationState());

  void loadMeasurements(List<MeasurementInput> items) {
    emit(state.copyWith(
      measurements: items,
      isVerified: false,
      errorMessage: null,
    ));
  }

  void updateMeasurement(int index, MeasurementInput updated) {
    if (index < 0 || index >= state.measurements.length) return;
    final list = List<MeasurementInput>.from(state.measurements);
    list[index] = updated;
    emit(state.copyWith(
      measurements: list,
      isVerified: false, // Invalidate verification on edit
    ));
  }

  void confirmVerification() {
    if (state.measurements.isEmpty) {
      emit(state.copyWith(
        errorMessage: 'No measurements available to verify.',
      ));
      return;
    }
    final verifiedList = state.measurements
        .map((m) => m.copyWith(isUserVerified: true))
        .toList();
    emit(state.copyWith(
      measurements: verifiedList,
      isVerified: true,
      errorMessage: null,
    ));
  }

  void reset() => emit(const VerificationState());
}
