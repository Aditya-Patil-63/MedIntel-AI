import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/reference/measurement_input.dart';
import '../../repositories/medical_repository.dart';
import 'analysis_state.dart';

class AnalysisCubit extends Cubit<AnalysisState> {
  final MedicalRepository repository;

  AnalysisCubit({required this.repository})
      : super(const AnalysisInitial());

  /// Runs deterministic reference analysis.
  /// Enforces client-side verification safeguard (backend remains authoritative).
  Future<void> runReferenceAnalysis({
    required List<MeasurementInput> measurements,
    required bool isUserVerified,
  }) async {
    if (!isUserVerified) {
      emit(const AnalysisError(
        'Client Safeguard: Extracted measurements must be verified before analysis.',
      ));
      return;
    }

    emit(const AnalysisLoading('Running reference range analysis...'));
    try {
      final result = await repository.analyzeMeasurements(
        measurements: measurements,
        isUserVerified: isUserVerified,
      );
      emit(AnalysisSuccess(referenceAnalysis: result));
    } catch (e) {
      emit(AnalysisError(e.toString()));
    }
  }

  void reset() => emit(const AnalysisInitial());
}
