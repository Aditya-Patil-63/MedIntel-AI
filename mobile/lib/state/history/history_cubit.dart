import 'package:flutter_bloc/flutter_bloc.dart';
import '../../models/history/analysis_history_item.dart';
import 'history_state.dart';

/// In-memory session history cubit managing completed medical report analyses.
///
/// NOTE: Because the FastAPI backend does not provide history-read or authentication
/// endpoints, history is managed locally within the mobile client as in-memory session records.
/// Records are maintained for the active app session and remain strictly decoupled from
/// live analysis state.
class HistoryCubit extends Cubit<HistoryState> {
  final List<AnalysisHistoryItem> _records = [];

  HistoryCubit() : super(const HistoryInitial());

  /// Returns an unmodifiable snapshot of the currently stored history records.
  List<AnalysisHistoryItem> get currentRecords =>
      List<AnalysisHistoryItem>.unmodifiable(_records);

  /// Loads current history records into state.
  /// Strictly reads local in-memory records; does NOT make any network or medical API calls.
  Future<void> loadHistory() async {
    emit(const HistoryLoading());
    emit(HistoryLoaded(List.unmodifiable(_records)));
  }

  /// Adds a completed, immutable analysis snapshot to history.
  /// Rejects invalid records and ensures newest items appear first.
  void addRecord(AnalysisHistoryItem item) {
    if (item.id.trim().isEmpty) {
      emit(const HistoryError('Cannot save history item with empty identifier.'));
      return;
    }

    // Deduplicate: remove any pre-existing record with identical ID
    _records.removeWhere((r) => r.id == item.id);

    // Insert at index 0 (newest records appear first)
    _records.insert(0, item);

    emit(HistoryLoaded(List.unmodifiable(_records)));
  }

  /// Clears all stored in-memory history records.
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
