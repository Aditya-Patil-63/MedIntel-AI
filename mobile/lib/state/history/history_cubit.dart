import 'dart:developer' as developer;
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/history/analysis_history_item.dart';
import '../../services/api_service.dart';
import 'history_state.dart';

/// User-scoped history cubit managing medical report analyses.
///
/// Integrates with the FastAPI backend database endpoints when authenticated,
/// ensuring each user's reports are stored and fetched strictly from that
/// individual user's database records. Falls back safely to in-memory caching.
class HistoryCubit extends Cubit<HistoryState> {
  final ApiService? apiService;
  final List<AnalysisHistoryItem> _records = [];

  HistoryCubit({this.apiService}) : super(const HistoryInitial());

  /// Returns an unmodifiable snapshot of the currently stored history records.
  List<AnalysisHistoryItem> get currentRecords =>
      List<AnalysisHistoryItem>.unmodifiable(_records);

  /// Loads history records for the currently authenticated user.
  /// Fetches from user's backend database table if authenticated, falling back to local cache.
  Future<void> loadHistory() async {
    emit(const HistoryLoading());

    final api = apiService;
    if (api != null && api.currentAuthToken != null) {
      try {
        final remoteReports = await api.fetchUserReports();
        _records.clear();
        _records.addAll(remoteReports);
        emit(HistoryLoaded(List.unmodifiable(_records)));
        return;
      } catch (e) {
        developer.log('Failed to fetch remote reports, using local cache: $e');
      }
    }

    emit(HistoryLoaded(List.unmodifiable(_records)));
  }

  /// Adds a completed, immutable analysis snapshot to history and persists to user's DB.
  Future<void> addRecord(AnalysisHistoryItem item) async {
    if (item.id.trim().isEmpty) {
      emit(const HistoryError('Cannot save history item with empty identifier.'));
      return;
    }

    // Deduplicate: remove any pre-existing record with identical ID
    _records.removeWhere((r) => r.id == item.id);

    // Insert at index 0 (newest records appear first)
    _records.insert(0, item);
    emit(HistoryLoaded(List.unmodifiable(_records)));

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

  /// Deletes a report both locally and from the user's database table.
  Future<void> deleteRecord(String id) async {
    _records.removeWhere((r) => r.id == id);
    emit(HistoryLoaded(List.unmodifiable(_records)));

    final api = apiService;
    if (api != null && api.currentAuthToken != null) {
      try {
        await api.deleteUserReport(id);
      } catch (e) {
        developer.log('Failed to delete report from backend: $e');
      }
    }
  }

  /// Clears all stored in-memory history records (e.g. upon user logout).
  void clearHistory() {
    _records.clear();
    emit(HistoryLoaded(const []));
  }

  /// Retrieves an immutable record by its unique ID.
  AnalysisHistoryItem? getRecordById(String id) {
    try {
      return _records.firstWhere((r) => r.id == id);
    } catch (_) {
      return null;
    }
  }
}
