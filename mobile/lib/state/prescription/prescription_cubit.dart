import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/prescription/prescription_model.dart';
import '../../services/api_service.dart';
import 'prescription_state.dart';

/// Cubit managing Prescription Explanation state (Objective 2).
class PrescriptionCubit extends Cubit<PrescriptionState> {
  final ApiService apiService;

  PrescriptionCubit({required this.apiService})
      : super(const PrescriptionInitial());

  /// Explain prescription using list of medicine names or lines.
  Future<void> explainPrescriptionMedicines(
    List<String> medicines, {
    String language = 'english',
  }) async {
    emit(const PrescriptionLoading(
      message: 'Extracting medicine details and dosage schedules...',
    ));
    try {
      final req = PrescriptionExplainRequest(
        medicines: medicines,
        language: language,
        isUserVerified: true,
      );
      final res = await apiService.explainPrescription(req);
      emit(PrescriptionSuccess(res, inputSource: 'medicines'));
    } catch (e) {
      emit(PrescriptionFailure(e.toString().replaceAll('Exception:', '').trim()));
    }
  }

  /// Explain prescription from raw multi-line prescription text.
  Future<void> explainPrescriptionText(
    String prescriptionText, {
    String language = 'english',
  }) async {
    emit(const PrescriptionLoading(
      message: 'Analyzing prescription text & translating instructions...',
    ));
    try {
      final req = PrescriptionExplainRequest(
        prescriptionText: prescriptionText,
        language: language,
        isUserVerified: true,
      );
      final res = await apiService.explainPrescription(req);
      emit(PrescriptionSuccess(res, inputSource: 'text'));
    } catch (e) {
      emit(PrescriptionFailure(e.toString().replaceAll('Exception:', '').trim()));
    }
  }

  /// Upload prescription photo or PDF, perform OCR/handwriting recognition, and explain.
  Future<void> uploadAndExplainPrescriptionFile(
    String filePath, {
    String language = 'english',
  }) async {
    emit(const PrescriptionLoading(
      message: 'Uploading prescription and deciphering handwriting...',
    ));
    try {
      final res = await apiService.uploadAndExplainPrescription(
        filePath,
        language: language,
      );
      emit(PrescriptionSuccess(res, inputSource: 'file'));
    } catch (e) {
      emit(PrescriptionFailure(e.toString().replaceAll('Exception:', '').trim()));
    }
  }

  /// Reset to initial state.
  void reset() {
    emit(const PrescriptionInitial());
  }
}
