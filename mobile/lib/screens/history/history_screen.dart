import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/common/enums.dart';
import '../../models/history/analysis_history_item.dart';
import '../../models/ml_risk/risk_prediction_response.dart';
import '../../state/history/history_cubit.dart';
import '../../state/history/history_state.dart';
import '../../widgets/disclaimer_banner.dart';
import 'history_detail_screen.dart';

/// Screen displaying locally saved completed analysis history records.
///
/// NOTE: History is maintained as in-memory local session snapshots.
/// Opening history does NOT trigger any backend or medical API calls.
class HistoryScreen extends StatelessWidget {
  const HistoryScreen({super.key});

  void _confirmClearHistory(BuildContext context) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Clear Session History?'),
        content: const Text(
          'This will remove all stored analysis snapshots from this session. '
          'This action cannot be undone.',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(backgroundColor: AppColors.critical),
            onPressed: () {
              Navigator.pop(dialogContext);
              context.read<HistoryCubit>().clearHistory();
            },
            child: const Text('Clear All'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Report History'),
        actions: [
          BlocBuilder<HistoryCubit, HistoryState>(
            builder: (context, state) {
              final hasRecords = state is HistoryLoaded && state.records.isNotEmpty;
              if (!hasRecords) return const SizedBox.shrink();

              return IconButton(
                icon: const Icon(Icons.delete_outline),
                tooltip: 'Clear History',
                onPressed: () => _confirmClearHistory(context),
              );
            },
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: Column(
                children: [
                  // 1. Mandatory Educational Disclaimer Banner
                  const DisclaimerBanner(),
                  const SizedBox(height: 8),

                  // 2. Session Storage Notice
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                    decoration: BoxDecoration(
                      color: const Color(0xFFF1F5F9),
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: AppColors.divider),
                    ),
                    child: const Row(
                      children: [
                        Icon(Icons.info_outline, size: 16, color: AppColors.textSecondary),
                        SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            'Session History: Records are saved locally for this session. '
                            'Tap any record to inspect read-only details.',
                            style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            ),
            Expanded(
              child: BlocBuilder<HistoryCubit, HistoryState>(
                builder: (context, state) {
                  if (state is HistoryLoading) {
                    return const Center(child: CircularProgressIndicator());
                  }

                  if (state is HistoryError) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text(
                          state.message,
                          style: const TextStyle(color: AppColors.critical),
                          textAlign: TextAlign.center,
                        ),
                      ),
                    );
                  }

                  final records = state is HistoryLoaded ? state.records : <AnalysisHistoryItem>[];

                  if (records.isEmpty) {
                    return Center(
                      child: Padding(
                        padding: const EdgeInsets.all(32),
                        child: Column(
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Icon(
                              Icons.history_toggle_off,
                              size: 64,
                              color: Colors.grey.shade400,
                            ),
                            const SizedBox(height: 16),
                            const Text(
                              'No Saved Reports Yet',
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textSecondary,
                              ),
                            ),
                            const SizedBox(height: 8),
                            const Text(
                              'Complete an analysis workflow and tap "Save to History" on the results screen to review historical reports here.',
                              textAlign: TextAlign.center,
                              style: TextStyle(fontSize: 13, color: AppColors.textMuted),
                            ),
                          ],
                        ),
                      ),
                    );
                  }

                  return ListView.builder(
                    padding: const EdgeInsets.fromLTRB(16, 8, 16, 16),
                    itemCount: records.length,
                    itemBuilder: (context, index) {
                      final item = records[index];
                      return _buildHistoryCard(context, item);
                    },
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryCard(BuildContext context, AnalysisHistoryItem item) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: InkWell(
        borderRadius: BorderRadius.circular(12),
        onTap: () {
          Navigator.push(
            context,
            MaterialPageRoute(
              builder: (_) => HistoryDetailScreen(item: item),
            ),
          );
        },
        child: Padding(
          padding: const EdgeInsets.all(14),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Header: Document Name & Date
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Expanded(
                    child: Row(
                      children: [
                        const Icon(Icons.description, size: 18, color: AppColors.primary),
                        const SizedBox(width: 8),
                        Expanded(
                          child: Text(
                            item.documentName,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                            ),
                            overflow: TextOverflow.ellipsis,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    item.formattedDate,
                    style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                  ),
                ],
              ),
              const SizedBox(height: 8),

              // Summary Metadata
              Text(
                '${item.verifiedMeasurementCount} Verified Measurements'
                '${item.patientAge != null ? " • Age: ${item.patientAge!.toStringAsFixed(0)}y" : ""}'
                '${item.patientSex != null ? " • Sex: ${item.patientSex}" : ""}',
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
              const SizedBox(height: 8),

              // Reference findings breakdown
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: [
                  _buildMiniBadge(
                    '${item.referenceResults.length} Tests Evaluated',
                    AppColors.primary,
                    AppColors.primaryLight.withValues(alpha: 0.1),
                  ),
                  if (item.criticalCount > 0)
                    _buildMiniBadge('${item.criticalCount} Critical', AppColors.critical, AppColors.criticalBg),
                  if (item.highCount > 0)
                    _buildMiniBadge('${item.highCount} High', AppColors.high, AppColors.highBg),
                  if (item.lowCount > 0)
                    _buildMiniBadge('${item.lowCount} Low', AppColors.low, AppColors.lowBg),
                  if (item.normalCount > 0 && item.criticalCount == 0 && item.highCount == 0 && item.lowCount == 0)
                    _buildMiniBadge('All Normal (${item.normalCount})', AppColors.normal, AppColors.normalBg),
                ],
              ),
              const SizedBox(height: 8),

              // ML Risk Indicator Summary (Non-diagnostic)
              _buildMLSummaryRow(item),
              const Divider(height: 16),

              // Footer: Language + Tap to View action
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  Row(
                    children: [
                      const Icon(Icons.language, size: 14, color: AppColors.textMuted),
                      const SizedBox(width: 4),
                      Text(
                        item.selectedLanguage.name,
                        style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
                      ),
                    ],
                  ),
                  const Row(
                    children: [
                      Text(
                        'View Snapshot',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                          color: AppColors.primary,
                        ),
                      ),
                      SizedBox(width: 4),
                      Icon(Icons.chevron_right, size: 16, color: AppColors.primary),
                    ],
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildMLSummaryRow(AnalysisHistoryItem item) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        _buildModelRiskLine('Diabetes', item.diabetesRisk),
        _buildModelRiskLine('Heart Disease', item.heartRisk),
        _buildModelRiskLine('Kidney Disease', item.kidneyRisk),
      ],
    );
  }

  Widget _buildModelRiskLine(String modelLabel, RiskPredictionResponse? risk) {
    if (risk == null) return const SizedBox.shrink();

    String statusText;
    Color statusColor;

    if (risk.status == 'OK' && risk.riskBand != null) {
      statusText = 'Estimated risk: ${risk.riskBand!.value.toUpperCase()}';
      switch (risk.riskBand!) {
        case RiskBand.low:
          statusColor = AppColors.normal;
          break;
        case RiskBand.moderate:
          statusColor = AppColors.high;
          break;
        case RiskBand.elevated:
          statusColor = AppColors.critical;
          break;
      }
    } else if (risk.status == 'INSUFFICIENT_FEATURES') {
      statusText = 'Insufficient verified features';
      statusColor = AppColors.textMuted;
    } else {
      statusText = 'Status: ${risk.status}';
      statusColor = AppColors.textMuted;
    }

    return Padding(
      padding: const EdgeInsets.only(bottom: 2),
      child: Row(
        children: [
          Text(
            '$modelLabel: ',
            style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w600),
          ),
          Text(
            statusText,
            style: TextStyle(fontSize: 11, color: statusColor, fontWeight: FontWeight.w500),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniBadge(String text, Color fg, Color bg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: fg),
      ),
    );
  }
}
