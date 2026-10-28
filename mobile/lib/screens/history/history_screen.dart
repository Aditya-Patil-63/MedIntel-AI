import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/common/enums.dart';
import '../../models/history/analysis_history_item.dart';
import '../../models/history/prescription_history_item.dart';
import '../../models/history/unified_history_item.dart';
import '../../state/history/history_cubit.dart';
import '../../state/history/history_state.dart';
import 'biomarker_trends_screen.dart';
import 'history_detail_screen.dart';
import 'prescription_history_detail_screen.dart';

/// Screen displaying user's saved medical analysis reports and prescription history.
///
/// Features:
/// - Unified tabbed navigation: All, Reports, Prescriptions
/// - Read-only inspection of previously analyzed documents without re-running models/OCR
/// - Chronological ordering with formatted local timestamps (e.g. 27 Oct 2026, 7:45 PM)
/// - Persistent SQLite backend retrieval with offline caching
class HistoryScreen extends StatefulWidget {
  const HistoryScreen({super.key});

  @override
  State<HistoryScreen> createState() => _HistoryScreenState();
}

class _HistoryScreenState extends State<HistoryScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _searchController = TextEditingController();

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 3, vsync: this);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        context.read<HistoryCubit>().loadHistory();
      }
    });
  }

  @override
  void dispose() {
    _tabController.dispose();
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
            Text('Clear History?'),
          ],
        ),
        content: const Text(
          'This will remove all stored reports and prescription records from your account. '
          'This action cannot be undone.',
          style: TextStyle(fontSize: 14, color: AppColors.textSecondary),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext),
            child: const Text('Cancel',
                style: TextStyle(color: AppColors.textSecondary)),
          ),
          ElevatedButton(
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.critical,
              foregroundColor: Colors.white,
              shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8)),
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
        title: const Text('History'),
        elevation: 0,
        actions: [
          BlocBuilder<HistoryCubit, HistoryState>(
            builder: (context, state) {
              final records = state is HistoryLoaded
                  ? state.records
                  : <AnalysisHistoryItem>[];
              final hasAny = state is HistoryLoaded && state.isNotEmpty;

              if (!hasAny) return const SizedBox.shrink();

              return Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  if (records.isNotEmpty)
                    IconButton(
                      icon: const Icon(Icons.show_chart_rounded),
                      tooltip: 'Track Metrics & Trends',
                      onPressed: () {
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) =>
                                BiomarkerTrendsScreen(records: records),
                          ),
                        );
                      },
                    ),
                  IconButton(
                    icon: const Icon(Icons.delete_sweep_outlined),
                    tooltip: 'Clear History',
                    onPressed: () => _confirmClearHistory(context),
                  ),
                ],
              );
            },
          ),
        ],
        bottom: PreferredSize(
          preferredSize: const Size.fromHeight(48),
          child: Container(
            color: Colors.white,
            child: TabBar(
              controller: _tabController,
              labelColor: AppColors.primary,
              unselectedLabelColor: AppColors.textSecondary,
              indicatorColor: AppColors.primary,
              indicatorWeight: 3,
              labelStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
              ),
              unselectedLabelStyle: const TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.normal,
              ),
              tabs: const [
                Tab(text: 'All'),
                Tab(text: 'Reports'),
                Tab(text: 'Prescriptions'),
              ],
            ),
          ),
        ),
      ),
      body: SafeArea(
        child: BlocBuilder<HistoryCubit, HistoryState>(
          builder: (context, state) {
            if (state is HistoryLoading) {
              return const Center(
                child: CircularProgressIndicator(color: AppColors.primary),
              );
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

            final loaded = state is HistoryLoaded
                ? state
                : HistoryLoaded(const [], prescriptions: const []);

            return Column(
              children: [
                // Search Bar
                Padding(
                  padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
                  child: Container(
                    height: 42,
                    decoration: BoxDecoration(
                      color: AppColors.cardSurface,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: AppColors.cardBorder),
                    ),
                    child: TextField(
                      controller: _searchController,
                      onChanged: (_) => setState(() {}),
                      style: const TextStyle(
                          fontSize: 13, color: AppColors.textPrimary),
                      decoration: InputDecoration(
                        hintText: 'Search by title, test, or medicine...',
                        hintStyle: const TextStyle(
                            fontSize: 12, color: AppColors.textMuted),
                        prefixIcon: const Icon(Icons.search,
                            size: 18, color: AppColors.textMuted),
                        suffixIcon: _searchController.text.isNotEmpty
                            ? IconButton(
                                icon: const Icon(Icons.clear,
                                    size: 16, color: AppColors.textMuted),
                                onPressed: () {
                                  _searchController.clear();
                                  setState(() {});
                                },
                              )
                            : null,
                        border: InputBorder.none,
                        contentPadding:
                            const EdgeInsets.symmetric(vertical: 11),
                      ),
                    ),
                  ),
                ),

                // Tab Content
                Expanded(
                  child: TabBarView(
                    controller: _tabController,
                    children: [
                      // Tab 1: All Items
                      _buildUnifiedTab(context, loaded.allItems),

                      // Tab 2: Reports Only
                      _buildReportsTab(context, loaded.records),

                      // Tab 3: Prescriptions Only
                      _buildPrescriptionsTab(context, loaded.prescriptions),
                    ],
                  ),
                ),
              ],
            );
          },
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 1: Unified All Items
  // ---------------------------------------------------------------------------
  Widget _buildUnifiedTab(
      BuildContext context, List<UnifiedHistoryItem> allItems) {
    if (allItems.isEmpty) {
      return _buildEmptyState(
        icon: Icons.history_rounded,
        title: 'No History Records Yet',
        subtitle:
            'Upload a medical report or analyze a prescription to see your health history here.',
      );
    }

    final query = _searchController.text.trim().toLowerCase();
    final filtered = allItems.where((item) {
      if (query.isEmpty) return true;
      if (item.title.toLowerCase().contains(query) ||
          item.subtitle.toLowerCase().contains(query) ||
          item.documentName.toLowerCase().contains(query)) {
        return true;
      }
      if (item.isReport && item.report != null) {
        return item.report!.referenceResults.any((r) =>
            (r.canonicalName ?? r.originalTestName)
                .toLowerCase()
                .contains(query));
      }
      if (item.isPrescription && item.prescription != null) {
        return item.prescription!.medicines.any(
            (m) => m.displayMedicineName.toLowerCase().contains(query));
      }
      return false;
    }).toList();

    if (filtered.isEmpty) {
      return _buildNoSearchResults();
    }

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
      itemCount: filtered.length,
      itemBuilder: (context, index) {
        final item = filtered[index];
        if (item.isReport && item.report != null) {
          return _buildReportCard(context, item.report!);
        } else if (item.isPrescription && item.prescription != null) {
          return _buildPrescriptionCard(context, item.prescription!);
        }
        return const SizedBox.shrink();
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 2: Reports Tab
  // ---------------------------------------------------------------------------
  Widget _buildReportsTab(
      BuildContext context, List<AnalysisHistoryItem> reports) {
    if (reports.isEmpty) {
      return _buildEmptyState(
        icon: Icons.analytics_outlined,
        title: 'No Medical Reports Saved Yet',
        subtitle:
            'Analyzed lab reports will automatically be stored here for read-only historical review.',
      );
    }

    final query = _searchController.text.trim().toLowerCase();
    final filtered = reports.where((item) {
      if (query.isEmpty) return true;
      return item.documentName.toLowerCase().contains(query) ||
          item.referenceResults.any((r) =>
              (r.canonicalName ?? r.originalTestName)
                  .toLowerCase()
                  .contains(query));
    }).toList();

    if (filtered.isEmpty) {
      return _buildNoSearchResults();
    }

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
      itemCount: filtered.length,
      itemBuilder: (context, index) {
        return _buildReportCard(context, filtered[index]);
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 3: Prescriptions Tab
  // ---------------------------------------------------------------------------
  Widget _buildPrescriptionsTab(
      BuildContext context, List<PrescriptionHistoryItem> prescriptions) {
    if (prescriptions.isEmpty) {
      return _buildEmptyState(
        icon: Icons.medication_liquid_rounded,
        title: 'No Prescriptions Saved Yet',
        subtitle:
            'Viewed prescriptions with dosage schedules and instructions will automatically be stored here.',
      );
    }

    final query = _searchController.text.trim().toLowerCase();
    final filtered = prescriptions.where((item) {
      if (query.isEmpty) return true;
      return item.title.toLowerCase().contains(query) ||
          item.documentName.toLowerCase().contains(query) ||
          item.medicines.any(
              (m) => m.displayMedicineName.toLowerCase().contains(query));
    }).toList();

    if (filtered.isEmpty) {
      return _buildNoSearchResults();
    }

    return ListView.builder(
      padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
      itemCount: filtered.length,
      itemBuilder: (context, index) {
        return _buildPrescriptionCard(context, filtered[index]);
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Card 1: Medical Report Card
  // ---------------------------------------------------------------------------
  Widget _buildReportCard(BuildContext context, AnalysisHistoryItem item) {
    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [BoxStyle.cardShadow],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            context.read<HistoryCubit>().touchItem(item.id);
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
                // Top Tag & Type
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.primaryLight.withValues(alpha: 0.12),
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.analytics_outlined,
                              size: 13, color: AppColors.primary),
                          SizedBox(width: 4),
                          Text(
                            'REPORT',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: AppColors.primary,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline,
                          size: 18, color: AppColors.textMuted),
                      tooltip: 'Delete Report',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                      onPressed: () {
                        context.read<HistoryCubit>().deleteRecord(item.id);
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // Document Name
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
                const SizedBox(height: 4),

                // Formatted Local Timestamp
                Row(
                  children: [
                    const Icon(Icons.access_time_rounded,
                        size: 12, color: AppColors.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      item.formattedDate,
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // Summary Metadata: exact string pattern tested by e2e
                Text(
                  '${item.verifiedMeasurementCount} Verified Measurements'
                  '${item.patientAge != null ? " • Age: ${item.patientAge!.toStringAsFixed(0)}y" : ""}'
                  '${item.patientSex != null ? " • Sex: ${item.patientSex}" : ""}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 10),

                // Findings Badges
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
                      _buildMiniBadge(
                        '${item.criticalCount} Critical',
                        AppColors.critical,
                        AppColors.criticalBg,
                      ),
                    if (item.highCount > 0)
                      _buildMiniBadge(
                        '${item.highCount} High',
                        AppColors.high,
                        AppColors.highBg,
                      ),
                    if (item.lowCount > 0)
                      _buildMiniBadge(
                        '${item.lowCount} Low',
                        AppColors.low,
                        AppColors.lowBg,
                      ),
                    if (item.normalCount > 0 &&
                        item.criticalCount == 0 &&
                        item.highCount == 0 &&
                        item.lowCount == 0)
                      _buildMiniBadge(
                        'All Normal (${item.normalCount})',
                        AppColors.normal,
                        AppColors.normalBg,
                      ),
                  ],
                ),
                const SizedBox(height: 10),

                // ML Risk Row
                _buildMLSummaryRow(item),
                const Divider(height: 20, color: AppColors.divider),

                // Footer Action
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.background,
                        borderRadius: BorderRadius.circular(6),
                        border: Border.all(color: AppColors.divider),
                      ),
                      child: Row(
                        children: [
                          const Icon(Icons.language,
                              size: 13, color: AppColors.textSecondary),
                          const SizedBox(width: 4),
                          Text(
                            item.selectedLanguage.name,
                            style: const TextStyle(
                              fontSize: 11,
                              color: AppColors.textSecondary,
                              fontWeight: FontWeight.w500,
                            ),
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
                        Icon(Icons.arrow_forward_rounded,
                            size: 15, color: AppColors.primary),
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

  // ---------------------------------------------------------------------------
  // Card 2: Prescription Card
  // ---------------------------------------------------------------------------
  Widget _buildPrescriptionCard(
      BuildContext context, PrescriptionHistoryItem item) {
    const rxColor = Color(0xFF7C3AED);
    const rxBg = Color(0xFFF3E8FF);

    return Container(
      margin: const EdgeInsets.only(bottom: 12),
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [BoxStyle.cardShadow],
      ),
      child: Material(
        color: Colors.transparent,
        child: InkWell(
          borderRadius: BorderRadius.circular(16),
          onTap: () {
            context.read<HistoryCubit>().touchItem(item.id);
            Navigator.push(
              context,
              MaterialPageRoute(
                builder: (_) =>
                    PrescriptionHistoryDetailScreen(item: item),
              ),
            );
          },
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                // Top Tag & Type
                Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: rxBg,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.medication_liquid_rounded,
                              size: 13, color: rxColor),
                          SizedBox(width: 4),
                          Text(
                            'PRESCRIPTION',
                            style: TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.bold,
                              color: rxColor,
                              letterSpacing: 0.5,
                            ),
                          ),
                        ],
                      ),
                    ),
                    IconButton(
                      icon: const Icon(Icons.delete_outline,
                          size: 18, color: AppColors.textMuted),
                      tooltip: 'Delete Prescription',
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                      onPressed: () {
                        context
                            .read<HistoryCubit>()
                            .deletePrescription(item.id);
                      },
                    ),
                  ],
                ),
                const SizedBox(height: 8),

                // Prescription Title
                Text(
                  item.title,
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 15,
                    color: AppColors.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                if ((item.doctorName != null && item.doctorName!.isNotEmpty) ||
                    (item.hospitalName != null && item.hospitalName!.isNotEmpty)) ...[
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(Icons.person_outline,
                          size: 13, color: AppColors.textSecondary),
                      const SizedBox(width: 4),
                      Text(
                        [
                          if (item.doctorName != null && item.doctorName!.isNotEmpty)
                            item.doctorName!,
                          if (item.hospitalName != null && item.hospitalName!.isNotEmpty)
                            item.hospitalName!,
                        ].join(' • '),
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ),
                ],
                const SizedBox(height: 4),

                // Formatted Local Timestamp
                Row(
                  children: [
                    const Icon(Icons.access_time_rounded,
                        size: 12, color: AppColors.textMuted),
                    const SizedBox(width: 4),
                    Text(
                      item.formattedDate,
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
                const SizedBox(height: 10),

                // Medicines Summary
                Text(
                  '${item.medicines.length} Prescribed Medicines • ${item.documentName}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                const SizedBox(height: 8),

                // Medicines pills / list preview
                Container(
                  width: double.infinity,
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 8),
                  decoration: BoxDecoration(
                    color: AppColors.background,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.list_alt_rounded,
                          size: 15, color: rxColor),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          item.medicineNamesSummary,
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textPrimary,
                            fontWeight: FontWeight.w500,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ],
                  ),
                ),
                const Divider(height: 20, color: AppColors.divider),

                // Footer Action
                const Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Row(
                      children: [
                        Icon(Icons.calendar_today_rounded,
                            size: 13, color: AppColors.textSecondary),
                        SizedBox(width: 4),
                        Text(
                          'Dosage Schedules Included',
                          style: TextStyle(
                            fontSize: 11,
                            color: AppColors.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ],
                    ),
                    Row(
                      children: [
                        Text(
                          'View Prescription',
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.bold,
                            color: rxColor,
                          ),
                        ),
                        SizedBox(width: 4),
                        Icon(Icons.arrow_forward_rounded,
                            size: 15, color: rxColor),
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

  // ---------------------------------------------------------------------------
  // Helper Widgets
  // ---------------------------------------------------------------------------
  Widget _buildMiniBadge(String text, Color textColor, Color bgColor) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: bgColor,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Text(
        text,
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: textColor,
        ),
      ),
    );
  }

  Widget _buildMLSummaryRow(AnalysisHistoryItem item) {
    final risks = <Widget>[];

    if (item.diabetesRisk != null && item.diabetesRisk!.isSuccess) {
      risks.add(_buildRiskPill(
          'Diabetes: ${item.diabetesRisk!.formattedProbability}',
          item.diabetesRisk!.riskBand));
    }
    if (item.heartRisk != null && item.heartRisk!.isSuccess) {
      risks.add(_buildRiskPill(
          'Heart: ${item.heartRisk!.formattedProbability}',
          item.heartRisk!.riskBand));
    }
    if (item.kidneyRisk != null && item.kidneyRisk!.isSuccess) {
      risks.add(_buildRiskPill(
          'Kidney: ${item.kidneyRisk!.formattedProbability}',
          item.kidneyRisk!.riskBand));
    }

    if (risks.isEmpty) {
      return const SizedBox.shrink();
    }

    return Padding(
      padding: const EdgeInsets.only(top: 2),
      child: Wrap(
        spacing: 6,
        runSpacing: 4,
        children: risks,
      ),
    );
  }

  Widget _buildRiskPill(String label, RiskBand? band) {
    Color color;
    Color bg;
    switch (band) {
      case RiskBand.elevated:
        color = AppColors.critical;
        bg = AppColors.criticalBg;
        break;
      case RiskBand.moderate:
        color = AppColors.high;
        bg = AppColors.highBg;
        break;
      case RiskBand.low:
      default:
        color = AppColors.normal;
        bg = AppColors.normalBg;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 7, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: color.withValues(alpha: 0.3)),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: 10,
          fontWeight: FontWeight.bold,
          color: color,
        ),
      ),
    );
  }

  Widget _buildEmptyState({
    required IconData icon,
    required String title,
    required String subtitle,
  }) {
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
              child: Icon(icon, size: 52, color: AppColors.primary),
            ),
            const SizedBox(height: 18),
            Text(
              title,
              style: const TextStyle(
                fontSize: 16,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 8),
            Text(
              subtitle,
              textAlign: TextAlign.center,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.textSecondary,
                height: 1.4,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildNoSearchResults() {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.search_off_rounded,
                size: 48, color: Colors.grey.shade400),
            const SizedBox(height: 12),
            const Text(
              'No matching records found',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 4),
            const Text(
              'Try adjusting your search criteria.',
              style: TextStyle(fontSize: 12, color: AppColors.textMuted),
            ),
          ],
        ),
      ),
    );
  }
}
