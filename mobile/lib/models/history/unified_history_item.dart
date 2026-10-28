import 'package:equatable/equatable.dart';
import '../../core/utils/date_formatter.dart';
import 'analysis_history_item.dart';
import 'prescription_history_item.dart';

enum HistoryItemType { report, prescription }

/// Unified display model for items appearing in the MedIntel AI History screen.
/// Can wrap either a lab AnalysisHistoryItem or a PrescriptionHistoryItem.
class UnifiedHistoryItem extends Equatable {
  final String id;
  final HistoryItemType type;
  final DateTime timestamp;
  final String title;
  final String subtitle;
  final String documentName;
  final AnalysisHistoryItem? report;
  final PrescriptionHistoryItem? prescription;

  const UnifiedHistoryItem({
    required this.id,
    required this.type,
    required this.timestamp,
    required this.title,
    required this.subtitle,
    required this.documentName,
    this.report,
    this.prescription,
  });

  bool get isReport => type == HistoryItemType.report;
  bool get isPrescription => type == HistoryItemType.prescription;

  String get formattedDate => formatHistoryTimestamp(timestamp);

  factory UnifiedHistoryItem.fromReport(AnalysisHistoryItem item) {
    String sub;
    if (item.criticalCount > 0 || item.highCount > 0 || item.lowCount > 0) {
      final parts = <String>[];
      if (item.criticalCount > 0) parts.add('${item.criticalCount} Critical');
      if (item.highCount > 0) parts.add('${item.highCount} High');
      if (item.lowCount > 0) parts.add('${item.lowCount} Low');
      sub = '${item.verifiedMeasurementCount} Tests • Attention Required (${parts.join(", ")})';
    } else if (item.verifiedMeasurementCount > 0) {
      sub = '${item.verifiedMeasurementCount} Tests • All Normal';
    } else {
      sub = 'Clinical Analysis Report';
    }

    return UnifiedHistoryItem(
      id: item.id,
      type: HistoryItemType.report,
      timestamp: item.updatedAt ?? item.createdAt,
      title: item.documentName,
      subtitle: sub,
      documentName: item.documentName,
      report: item,
    );
  }

  factory UnifiedHistoryItem.fromPrescription(PrescriptionHistoryItem item) {
    final sub = item.medicines.isNotEmpty
        ? '${item.medicines.length} Medicines • ${item.medicineNamesSummary}'
        : 'Prescription Schedule';

    return UnifiedHistoryItem(
      id: item.id,
      type: HistoryItemType.prescription,
      timestamp: item.updatedAt ?? item.createdAt,
      title: item.title,
      subtitle: sub,
      documentName: item.documentName,
      prescription: item,
    );
  }

  @override
  List<Object?> get props => [
        id,
        type,
        timestamp,
        title,
        subtitle,
        documentName,
        report,
        prescription,
      ];
}
