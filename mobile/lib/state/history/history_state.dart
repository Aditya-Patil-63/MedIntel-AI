import 'package:equatable/equatable.dart';
import '../../models/history/analysis_history_item.dart';
import '../../models/history/prescription_history_item.dart';
import '../../models/history/unified_history_item.dart';

/// State representation for user history containing reports and prescriptions.
abstract class HistoryState extends Equatable {
  const HistoryState();

  @override
  List<Object?> get props => [];
}

class HistoryInitial extends HistoryState {
  const HistoryInitial();
}

class HistoryLoading extends HistoryState {
  const HistoryLoading();
}

class HistoryLoaded extends HistoryState {
  /// Preserved for backward compatibility: all medical report items.
  final List<AnalysisHistoryItem> records;

  /// All prescription history items.
  final List<PrescriptionHistoryItem> prescriptions;

  /// Combined chronological list of all history items (reports + prescriptions, newest first).
  final List<UnifiedHistoryItem> allItems;

  HistoryLoaded(
    List<AnalysisHistoryItem> records, {
    List<PrescriptionHistoryItem> prescriptions = const [],
    List<UnifiedHistoryItem>? allItems,
  })  : records = List<AnalysisHistoryItem>.unmodifiable(records),
        prescriptions =
            List<PrescriptionHistoryItem>.unmodifiable(prescriptions),
        allItems = List<UnifiedHistoryItem>.unmodifiable(
          allItems ?? _buildUnifiedList(records, prescriptions),
        );

  static List<UnifiedHistoryItem> _buildUnifiedList(
    List<AnalysisHistoryItem> reports,
    List<PrescriptionHistoryItem> prescriptions,
  ) {
    final list = <UnifiedHistoryItem>[
      ...reports.map((r) => UnifiedHistoryItem.fromReport(r)),
      ...prescriptions.map((p) => UnifiedHistoryItem.fromPrescription(p)),
    ];
    list.sort((a, b) => b.timestamp.compareTo(a.timestamp));
    return list;
  }

  bool get hasReports => records.isNotEmpty;
  bool get hasPrescriptions => prescriptions.isNotEmpty;
  bool get isEmpty => records.isEmpty && prescriptions.isEmpty;
  bool get isNotEmpty => !isEmpty;

  @override
  List<Object?> get props => [records, prescriptions, allItems];
}

class HistoryError extends HistoryState {
  final String message;
  const HistoryError(this.message);

  @override
  List<Object?> get props => [message];
}
