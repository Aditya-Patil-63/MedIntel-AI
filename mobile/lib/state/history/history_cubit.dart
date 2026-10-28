import 'dart:developer' as developer;
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/history/analysis_history_item.dart';
import '../../models/history/prescription_history_item.dart';
import '../../models/history/unified_history_item.dart';
import '../../services/api_service.dart';
import 'history_state.dart';

/// User-scoped history cubit managing medical reports and prescription history.
///
/// Integrates with the FastAPI backend database endpoints when authenticated,
/// ensuring each user's reports and prescriptions are stored and fetched strictly
/// from that individual user's database records. Falls back safely to in-memory caching.
class HistoryCubit extends Cubit<HistoryState> {
  final ApiService? apiService;
  final List<AnalysisHistoryItem> _records = [];
  final List<PrescriptionHistoryItem> _prescriptions = [];

  HistoryCubit({this.apiService}) : super(const HistoryInitial());

  /// Returns an unmodifiable snapshot of the currently stored medical reports.
  List<AnalysisHistoryItem> get currentRecords =>
      List<AnalysisHistoryItem>.unmodifiable(_records);

  /// Returns an unmodifiable snapshot of the currently stored prescriptions.
  List<PrescriptionHistoryItem> get currentPrescriptions =>
      List<PrescriptionHistoryItem>.unmodifiable(_prescriptions);

  /// Returns an unmodifiable list of unified history entries.
  List<UnifiedHistoryItem> get currentAllItems {
    final list = <UnifiedHistoryItem>[
      ..._records.map((r) => UnifiedHistoryItem.fromReport(r)),
      ..._prescriptions.map((p) => UnifiedHistoryItem.fromPrescription(p)),
    ];
    list.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return List<UnifiedHistoryItem>.unmodifiable(list);
  }

  /// Loads history records (both reports & prescriptions) for the currently authenticated user.
  /// Fetches from user's backend database table if authenticated, falling back to local cache.
  Future<void> loadHistory() async {
    emit(const HistoryLoading());

    final api = apiService;
    if (api != null && api.currentAuthToken != null) {
      try {
        final results = await Future.wait([
          api.fetchUserReports().catchError((e) {
            developer.log('Failed to fetch remote reports: $e');
            return <AnalysisHistoryItem>[];
          }),
          api.fetchUserPrescriptions().catchError((e) {
            developer.log('Failed to fetch remote prescriptions: $e');
            return <PrescriptionHistoryItem>[];
          }),
        ]);

        final remoteReports = results[0] as List<AnalysisHistoryItem>;
        final remotePrescriptions = results[1] as List<PrescriptionHistoryItem>;

        if (remoteReports.isNotEmpty || _records.isEmpty) {
          _records.clear();
          _records.addAll(remoteReports);
        }
        if (remotePrescriptions.isNotEmpty || _prescriptions.isEmpty) {
          _prescriptions.clear();
          _prescriptions.addAll(remotePrescriptions);
        }

        emit(HistoryLoaded(
          List.unmodifiable(_records),
          prescriptions: List.unmodifiable(_prescriptions),
        ));
        return;
      } catch (e) {
        developer.log('Failed to fetch remote history, using local cache: $e');
      }
    }

    emit(HistoryLoaded(
      List.unmodifiable(_records),
      prescriptions: List.unmodifiable(_prescriptions),
    ));
  }

  /// Adds a completed, immutable analysis snapshot to history and persists to user's DB.
  Future<void> addRecord(AnalysisHistoryItem item) async {
    if (item.id.trim().isEmpty) {
      emit(const HistoryError('Cannot save history item with empty identifier.'));
      return;
    }

    // Deduplicate: remove any pre-existing record with identical ID or identical content
    _records.removeWhere((r) =>
        r.id == item.id ||
        (r.documentName == item.documentName &&
            r.referenceResults == item.referenceResults));

    // Insert at index 0 (newest records appear first)
    _records.insert(0, item);
    emit(HistoryLoaded(
      List.unmodifiable(_records),
      prescriptions: List.unmodifiable(_prescriptions),
    ));

    // Persist to the authenticated user's database table on the backend
    final api = apiService;
    if (api != null && api.currentAuthToken != null) {
      try {
        await api.saveUserReport(item);
      } catch (e) {
        developer.log('Failed to sync report to backend: $e');
      }
    }
  }

  /// Adds a viewed/analyzed prescription to history and persists to user's DB.
  Future<void> addPrescription(PrescriptionHistoryItem item) async {
    if (item.id.trim().isEmpty) {
      emit(const HistoryError('Cannot save prescription with empty identifier.'));
      return;
    }

    // Deduplicate: remove any pre-existing record with identical ID or same medicine list
    _prescriptions.removeWhere((p) =>
        p.id == item.id ||
        (p.documentName == item.documentName && p.medicines == item.medicines));

    // Insert at index 0 (newest records appear first)
    _prescriptions.insert(0, item);
    emit(HistoryLoaded(
      List.unmodifiable(_records),
      prescriptions: List.unmodifiable(_prescriptions),
    ));

    // Persist to the authenticated user's database table on the backend
    final api = apiService;
    if (api != null && api.currentAuthToken != null) {
      try {
        await api.saveUserPrescription(item);
      } catch (e) {
        developer.log('Failed to sync prescription to backend: $e');
      }
    }
  }

  /// Updates last viewed timestamp for a reopened item.
  Future<void> touchItem(String id) async {
    final repIdx = _records.indexWhere((r) => r.id == id);
    if (repIdx != -1) {
      final old = _records[repIdx];
      final updated = AnalysisHistoryItem(
        id: old.id,
        createdAt: old.createdAt,
        updatedAt: DateTime.now(),
        documentName: old.documentName,
        verifiedMeasurementCount: old.verifiedMeasurementCount,
        patientAge: old.patientAge,
        patientSex: old.patientSex,
        referenceResults: old.referenceResults,
        totalClassified: old.totalClassified,
        diabetesRisk: old.diabetesRisk,
        heartRisk: old.heartRisk,
        kidneyRisk: old.kidneyRisk,
        genAiExplanation: old.genAiExplanation,
        selectedLanguage: old.selectedLanguage,
        disclaimer: old.disclaimer,
      );
      _records.removeAt(repIdx);
      _records.insert(0, updated);
      emit(HistoryLoaded(
        List.unmodifiable(_records),
        prescriptions: List.unmodifiable(_prescriptions),
      ));
      final api = apiService;
      if (api != null && api.currentAuthToken != null) {
        try {
          await api.saveUserReport(updated);
        } catch (_) {}
      }
      return;
    }

    final rxIdx = _prescriptions.indexWhere((p) => p.id == id);
    if (rxIdx != -1) {
      final old = _prescriptions[rxIdx];
      final updated = PrescriptionHistoryItem(
        id: old.id,
        createdAt: old.createdAt,
        updatedAt: DateTime.now(),
        title: old.title,
        documentName: old.documentName,
        doctorName: old.doctorName,
        hospitalName: old.hospitalName,
        medicines: old.medicines,
        doctorNotes: old.doctorNotes,
        generalGuidance: old.generalGuidance,
        questionsForDoctor: old.questionsForDoctor,
        language: old.language,
        disclaimer: old.disclaimer,
        imageReference: old.imageReference,
      );
      _prescriptions.removeAt(rxIdx);
      _prescriptions.insert(0, updated);
      emit(HistoryLoaded(
        List.unmodifiable(_records),
        prescriptions: List.unmodifiable(_prescriptions),
      ));
      final api = apiService;
      if (api != null && api.currentAuthToken != null) {
        try {
          await api.saveUserPrescription(updated);
        } catch (_) {}
      }
    }
  }

  /// Deletes a report both locally and from the user's database table.
  Future<void> deleteRecord(String id) async {
    _records.removeWhere((r) => r.id == id);
    emit(HistoryLoaded(
      List.unmodifiable(_records),
      prescriptions: List.unmodifiable(_prescriptions),
    ));

    final api = apiService;
    if (api != null && api.currentAuthToken != null) {
      try {
        await api.deleteUserReport(id);
      } catch (e) {
        developer.log('Failed to delete report from backend: $e');
      }
    }
  }

  /// Deletes a prescription both locally and from the user's database table.
  Future<void> deletePrescription(String id) async {
    _prescriptions.removeWhere((p) => p.id == id);
    emit(HistoryLoaded(
      List.unmodifiable(_records),
      prescriptions: List.unmodifiable(_prescriptions),
    ));

    final api = apiService;
    if (api != null && api.currentAuthToken != null) {
      try {
        await api.deleteUserPrescription(id);
      } catch (e) {
        developer.log('Failed to delete prescription from backend: $e');
      }
    }
  }

  /// Clears all stored in-memory history records (e.g. upon user logout).
  void clearHistory() {
    _records.clear();
    _prescriptions.clear();
    emit(HistoryLoaded(const [], prescriptions: const []));
  }

  /// Retrieves an immutable report record by its unique ID.
  AnalysisHistoryItem? getRecordById(String id) {
    try {
      return _records.firstWhere((r) => r.id == id);
    } catch (_) {
      return null;
    }
  }

  /// Retrieves an immutable prescription record by its unique ID.
  PrescriptionHistoryItem? getPrescriptionById(String id) {
    try {
      return _prescriptions.firstWhere((p) => p.id == id);
    } catch (_) {
      return null;
    }
  }
}

