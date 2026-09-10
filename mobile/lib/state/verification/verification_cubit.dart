import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/reference/editable_measurement.dart';
import '../../models/reference/parse_and_analyze.dart';
import '../../models/reference/patient_context.dart';
import '../../services/api_service.dart';
import 'verification_state.dart';

/// Orchestrates parsing of extracted text and human-in-the-loop verification.
class VerificationCubit extends Cubit<VerificationState> {
  final ApiService apiService;

  VerificationCubit({required this.apiService})
      : super(const VerificationState());

  /// Sends extracted document text to POST /api/v1/reference/parse-and-analyze.
  /// All parsed items enter with is_user_verified = false (UNVERIFIED).
  Future<void> parseExtractedText(
    String text, {
    PatientContext? patientContext,
  }) async {
    if (text.trim().isEmpty) {
      emit(state.copyWith(
        errorMessage: 'Extracted text is empty. Nothing to parse.',
        isParsing: false,
      ));
      return;
    }

    emit(state.copyWith(
      isParsing: true,
      isVerified: false,
      errorMessage: null,
      statusMessage: 'Parsing medical measurements with FastAPI backend...',
    ));

    try {
      final effectiveContext = patientContext ?? state.patientContext;

      final response = await apiService.parseAndAnalyze(
        ParseAndAnalyzeRequest(
          text: text,
          isUserVerified: false, // Mandatory: backend verification safety gate
          patientContext: effectiveContext.age != null || effectiveContext.sex != null
              ? effectiveContext
              : null,
        ),
      );

      final List<EditableMeasurement> parsedList = [];
      int counter = 0;

      for (final item in response.items) {
        // Skip items that have no recognized analyte and no parsed line
        final analyteName = item.analysis?.originalTestName ??
            item.parsedAnalyte ??
            item.canonicalName;

        if (analyteName != null && analyteName.isNotEmpty) {
          final dynamic val = item.analysis?.numericValue ??
              item.analysis?.originalValueText;
          final String? unit =
              item.analysis?.normalizedUnit ?? item.analysis?.unit;

          parsedList.add(
            EditableMeasurement.fromParsedItem(
              id: 'item_${DateTime.now().millisecondsSinceEpoch}_${counter++}',
              testName: analyteName,
              value: val,
              unit: unit,
              parserStatus: item.parserStatus,
              extractedReferenceRange: item.extractedReferenceRange,
              extractionConfidence: item.extractionConfidence,
            ),
          );
        }
      }

      emit(state.copyWith(
        measurements: parsedList,
        patientContext: effectiveContext,
        isParsing: false,
        isVerified: false,
        statusMessage: parsedList.isEmpty
            ? 'No lab tests were automatically recognized. You can add measurements manually.'
            : 'Parsed ${parsedList.length} measurements. Please verify all values below.',
        errorMessage: null,
      ));
    } catch (e) {
      emit(state.copyWith(
        isParsing: false,
        isVerified: false,
        errorMessage: 'Parsing error: ${e.toString().replaceFirst("ApiException: ", "")}',
      ));
    }
  }

  /// Updates an individual measurement.
  /// Any edit marks the item as CORRECTED and resets verification state (requires re-confirmation).
  void updateMeasurement(
    String id, {
    required String testName,
    required dynamic value,
    String? unit,
  }) {
    final index = state.measurements.indexWhere((m) => m.id == id);
    if (index == -1) return;

    final current = state.measurements[index];
    final updated = current.copyWith(
      testName: testName.trim(),
      value: value,
      unit: unit?.trim(),
      status: VerificationItemStatus.corrected,
    );

    final list = List<EditableMeasurement>.from(state.measurements);
    list[index] = updated;

    emit(state.copyWith(
      measurements: list,
      isVerified: false, // Invalidate confirmation on modification
      errorMessage: null,
      statusMessage: 'Measurement updated. Please re-confirm verification.',
    ));
  }

  /// Adds a manually input measurement.
  /// Automatically resets verification state.
  void addMeasurement({
    required String testName,
    required dynamic value,
    String? unit,
  }) {
    final newItem = EditableMeasurement(
      id: 'manual_${DateTime.now().millisecondsSinceEpoch}',
      testName: testName.trim(),
      value: value,
      unit: unit?.trim(),
      status: VerificationItemStatus.corrected,
      origin: MeasurementOrigin.manual,
      originalTestName: testName.trim(),
      originalValue: value,
      originalUnit: unit?.trim(),
    );

    final list = List<EditableMeasurement>.from(state.measurements)..add(newItem);

    emit(state.copyWith(
      measurements: list,
      isVerified: false, // Invalidate confirmation
      errorMessage: null,
      statusMessage: 'Added measurement: ${newItem.testName}. Confirm verification when ready.',
    ));
  }

  /// Removes an erroneous measurement.
  /// Automatically resets verification state.
  void removeMeasurement(String id) {
    final list = state.measurements.where((m) => m.id != id).toList();

    emit(state.copyWith(
      measurements: list,
      isVerified: false, // Invalidate confirmation
      errorMessage: null,
      statusMessage: 'Measurement removed.',
    ));
  }

  /// Updates patient context (Age / Sex).
  void updatePatientContext(PatientContext context) {
    emit(state.copyWith(
      patientContext: context,
      isVerified: false, // Invalidate confirmation if context changes
    ));
  }

  /// Explicit user confirmation gate.
  /// Validates all fields, marks unedited items as CONFIRMED, edited as CORRECTED,
  /// and transitions to isVerified = true.
  bool confirmVerification() {
    if (state.measurements.isEmpty) {
      emit(state.copyWith(
        errorMessage: 'No measurements available to confirm. Add at least one test.',
      ));
      return false;
    }

    // Validation: testName and value must not be empty/null
    for (final item in state.measurements) {
      if (item.testName.trim().isEmpty) {
        emit(state.copyWith(
          errorMessage: 'Measurement test name cannot be empty.',
        ));
        return false;
      }
      if (item.value == null || item.value.toString().trim().isEmpty) {
        emit(state.copyWith(
          errorMessage: 'Value missing for "${item.testName}". Please edit or remove it.',
        ));
        return false;
      }
    }

    // Validation for patient context if provided
    final age = state.patientContext.age;
    if (age != null && (age < 0 || age > 130)) {
      emit(state.copyWith(
        errorMessage: 'Patient age must be between 0 and 130 years.',
      ));
      return false;
    }

    // Transition all unverified items to confirmed; preserve corrected items
    final confirmedList = state.measurements.map((item) {
      if (item.status == VerificationItemStatus.unverified) {
        return item.copyWith(status: VerificationItemStatus.confirmed);
      }
      return item;
    }).toList();

    emit(state.copyWith(
      measurements: confirmedList,
      isVerified: true,
      errorMessage: null,
      statusMessage: 'All ${confirmedList.length} measurements confirmed and verified.',
    ));
    return true;
  }

  void reset() => emit(const VerificationState());
}
