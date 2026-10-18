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
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen> {
  final TextEditingController _searchController = TextEditingController();
  String _filterCategory = 'ALL'; // 'ALL', 'ATTENTION', 'NORMAL'

  @override
  void dispose() {
    _searchController.dispose();
    super.dispose();
  }

  void _confirmClearHistory(BuildContext context) {
    showDialog(
      context: context,
      builder: (dialogContext) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Row(
          children: [
            Icon(Icons.delete_outline, color: AppColors.critical, size: 22),
            SizedBox(width: 8),
            Text('Clear Session History?'),
          ],
        ),
        content: const Text(
          'This will remove all stored analysis snapshots from this session. '
          'This action cannot be undone.',
          style: TextStyle(fontSize: 14, color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel', style: TextStyle(color: AppColors.textSecondary)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.critical,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
            ),
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
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Report History'),
        elevation: 0,
        actions: [
          BlocBuilder<HistoryCubit, HistoryState>(
            builder: (context, state) {
              final hasRecords = state is HistoryLoaded && state.records.isNotEmpty;
              if (!hasRecords) return const SizedBox.shrink();

              return IconButton(
                icon: const Icon(Icons.delete_sweep_outlined),
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
              padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
              child: Column(
                children: [
                  // 1. Mandatory Educational Disclaimer Banner
                  const DisclaimerBanner(),
                  const SizedBox(height: 10),

                  // 2. Session Storage Notice
                  Container(
                    width: double.infinity,
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                    decoration: BoxDecoration(
                      color: AppColors.cardSurface,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: AppColors.cardBorder),
                    ),
                    child: Row(
                      children: [
                        Container(
                          padding: const EdgeInsets.all(6),
                          decoration: BoxDecoration(
                            color: AppColors.primaryLight.withValues(alpha: 0.12),
                            shape: BoxShape.circle,
                          ),
                          child: const Icon(Icons.lock_clock_outlined, size: 14, color: AppColors.primary),
                        ),
                        const SizedBox(width: 10),
                        const Expanded(
                          child: Text(
                            'Session History: Records are saved locally for this session. '
                            'Tap any record to inspect read-only details.',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary,
                              height: 1.3,
                            ),
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
                    return const Center(child: CircularProgressIndicator(color: AppColors.primary));
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

                  final allRecords = state is HistoryLoaded ? state.records : <AnalysisHistoryItem>[];

                  if (allRecords.isEmpty) {
                    return _buildEmptyState();
                  }

                  // Apply search and filter
                  final query = _searchController.text.trim().toLowerCase();
                  final filtered = allRecords.where((item) {
                    final matchesQuery = query.isEmpty ||
                        item.documentName.toLowerCase().contains(query) ||
                        item.referenceResults.any((r) =>
                            (r.canonicalName ?? r.originalTestName).toLowerCase().contains(query));

                    if (!matchesQuery) return false;

                    if (_filterCategory == 'ATTENTION') {
                      return item.criticalCount > 0 || item.highCount > 0 || item.lowCount > 0;
                    } else if (_filterCategory == 'NORMAL') {
                      return item.criticalCount == 0 && item.highCount == 0 && item.lowCount == 0;
                    }
                    return true;
                  }).toList();

                  return Column(
                    children: [
                      // Search and Filter Bar
                      Padding(
                        padding: const EdgeInsets.fromLTRB(16, 8, 16, 6),
                        child: Column(
                          children: [
                            Container(
                              height: 42,
                              decoration: BoxDecoration(
                                color: AppColors.cardSurface,
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(color: AppColors.cardBorder),
                              ),
                              child: TextField(
                                controller: _searchController,
                                onChanged: (_) => setState(() {}),
                                style: const TextStyle(fontSize: 13, color: AppColors.textPrimary),
                                decoration: InputDecoration(
                                  hintText: 'Search by document name or test...',
                                  hintStyle: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                                  prefixIcon: const Icon(Icons.search, size: 18, color: AppColors.textMuted),
                                  suffixIcon: _searchController.text.isNotEmpty
                                      ? IconButton(
                                          icon: const Icon(Icons.clear, size: 16, color: AppColors.textMuted),
                                          onPressed: () {
                                            _searchController.clear();
                                            setState(() {});
                                          },
                                        )
                                      : null,
                                  border: InputBorder.none,
                                  contentPadding: const EdgeInsets.symmetric(vertical: 10),
                                ),
                              ),
                            ),
                            const SizedBox(height: 8),
                            // Filter chips row
                            SingleChildScrollView(
                              scrollDirection: Axis.horizontal,
                              child: Row(
                                children: [
                                  _buildFilterChip('All Reports (${allRecords.length})', 'ALL'),
                                  const SizedBox(width: 6),
                                  _buildFilterChip('Needs Attention', 'ATTENTION'),
                                  const SizedBox(width: 6),
                                  _buildFilterChip('All Normal', 'NORMAL'),
                                ],
                              ),
                            ),
                          ],
                        ),
                      ),
                      Expanded(
                        child: filtered.isEmpty
                            ? Center(
                                child: Padding(
                                  padding: const EdgeInsets.all(24),
                                  child: Column(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Icon(Icons.search_off, size: 48, color: Colors.grey.shade400),
                                      const SizedBox(height: 12),
                                      const Text(
                                        'No matching reports found',
                                        style: TextStyle(
                                          fontSize: 14,
                                          fontWeight: FontWeight.bold,
                                          color: AppColors.textSecondary,
                                        ),
                                      ),
                                      const SizedBox(height: 4),
                                      const Text(
                                        'Try adjusting your search or filter criteria.',
                                        style: TextStyle(fontSize: 12, color: AppColors.textMuted),
                                      ),
                                    ],
                                  ),
                                ),
                              )
                            : ListView.builder(
                                padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                                itemCount: filtered.length,
                                itemBuilder: (context, index) {
                                  final item = filtered[index];
                                  return _buildHistoryCard(context, item);
                                },
                              ),
                      ),
                    ],
                  );
                },
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildFilterChip(String label, String categoryKey) {
    final isSelected = _filterCategory == categoryKey;
    return GestureDetector(
      onTap: () => setState(() => _filterCategory = categoryKey),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 5),
        decoration: BoxDecoration(
          color: isSelected ? AppColors.primary : AppColors.cardSurface,
          borderRadius: BorderRadius.circular(20),
          border: Border.all(
            color: isSelected ? AppColors.primary : AppColors.cardBorder,
          ),
        ),
        child: Text(
          label,
          style: TextStyle(
            fontSize: 11,
            fontWeight: isSelected ? FontWeight.w600 : FontWeight.normal,
            color: isSelected ? Colors.white : AppColors.textSecondary,
          ),
        ),
      ),
    );
  }

  Widget _buildEmptyState() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: AppColors.primaryLight.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.folder_shared_outlined,
                size: 56,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'No Saved Reports Yet',
              style: TextStyle(
                fontSize: 17,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            const Text(
              'Complete an analysis workflow and tap "Save to History" on the results screen to review historical reports here.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, color: AppColors.textSecondary, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildHistoryCard(BuildContext context, AnalysisHistoryItem item) {
    final hasAttention = item.criticalCount > 0 || item.highCount > 0 || item.lowCount > 0;

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: hasAttention
              ? AppColors.cardBorder
              : AppColors.cardBorder,
        ),
        boxShadow: [
          BoxStyle.cardShadow,
        ],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) => HistoryDetailScreen(item: item),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Header: Document Name & Date
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Container(
                      padding: const EdgeInsets.all(9),
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(10),
                      ),
                      child: const Icon(Icons.description_outlined, size: 20, color: AppColors.primary),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.documentName,
                            style: const TextStyle(
                              fontWeight: FontWeight.bold,
                              fontSize: 15,
                              color: AppColors.textPrimary,
                            ),
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                          ),
                          const SizedBox(height: 3),
                          Row(
                            children: [
                              const Icon(Icons.access_time, size: 12, color: AppColors.textMuted),
                              const SizedBox(width: 4),
                              Text(
                                item.formattedDate,
                                style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // Summary Metadata: exact string pattern required by tests
                Text(
                  '${item.verifiedMeasurementCount} Verified Measurements'
                  '${item.patientAge != null ? " • Age: ${item.patientAge!.toStringAsFixed(0)}y" : ""}'
                  '${item.patientSex != null ? " • Sex: ${item.patientSex}" : ""}',
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
                ),
                const SizedBox(height: 10),

                // Reference findings breakdown badges
                Wrap(
                  spacing: 6,
                  runSpacing: 6,
                  children: [
                    _buildMiniBadge(
                      '${item.referenceResults.length} Tests Evaluated',
                      AppColors.primary,
                      AppColors.primaryLight.withValues(alpha: 0.12),
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
                const SizedBox(height: 10),

                // ML Risk Indicator Summary (Non-diagnostic)
                _buildMLSummaryRow(item),
                const Divider(height: 20, color: AppColors.divider),

                // Footer: Language + Tap to View action
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: AppColors.divider),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.language, size: 13, color: AppColors.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            item.selectedLanguage.name,
                            style: const TextStyle(fontSize: 11, color: AppColors.textSecondary, fontWeight: FontWeight.w500),
                          ),
                        ],
                      ),
                    ),
                    const Row(
                      children: [
                        Text(
                          'View Snapshot',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: AppColors.primary,
                          ),
                        ),
                        SizedBox(width: 4),
                        Icon(Icons.arrow_forward, size: 15, color: AppColors.primary),
                      ],
                    ),
                  ],
                ),
              ],
            ),
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
      padding: const EdgeInsets.only(bottom: 3),
      child: Row(
        children: [
          Text(
            '$modelLabel: ',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
          ),
          Text(
            statusText,
            style: TextStyle(fontSize: 12, color: statusColor, fontWeight: FontWeight.w600),
          ),
        ],
      ),
    );
  }

  Widget _buildMiniBadge(String text, Color fg, Color bg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withValues(alpha: 0.2)),
      ),
      child: Text(
        text,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: fg),
      ),
    );
  }
}
