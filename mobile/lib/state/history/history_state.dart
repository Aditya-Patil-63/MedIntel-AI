import 'package:equatable/equatable.dart';
import '../../models/history/analysis_history_item.dart';

/// State representation for local session history of completed analyses.
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
  final List<AnalysisHistoryItem> records;

  HistoryLoaded(List<AnalysisHistoryItem> records)
      : records = List<AnalysisHistoryItem>.unmodifiable(records);

  @override
  List<Object?> get props => [records];
}

class HistoryError extends HistoryState {
  final String message;
  const HistoryError(this.message);

  @override
  List<Object?> get props => [message];
}
