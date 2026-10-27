import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/common/enums.dart';
import '../../models/history/analysis_history_item.dart';
import '../../models/reference/analysis_result.dart';
import '../../widgets/disclaimer_banner.dart';

/// Health Tracking and Biomarker Trends Screen (Objective 3, Requirement 7).
///
/// Enables patients to:
/// 1. Track longitudinal progression of key biomarkers (e.g. Glucose, Hemoglobin, Creatinine) over time.
/// 2. Visualize changes, trends, and reference interval boundaries.
/// 3. Compare two historical reports side-by-side with difference deltas.
class BiomarkerTrendsScreen extends StatefulWidget {
  final List<AnalysisHistoryItem> records;

  const BiomarkerTrendsScreen({
    super.key,
    required this.records,
  });

  @override
  State<BiomarkerTrendsScreen> createState() => _BiomarkerTrendsScreenState();
}

class _BiomarkerTrendsScreenState extends State<BiomarkerTrendsScreen>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  String? _selectedBiomarker;

  // Comparison Tab state
  String? _compareReportIdA;
  String? _compareReportIdB;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);

    final available = _getAvailableBiomarkers();
    if (available.isNotEmpty) {
      _selectedBiomarker = available.first;
    }

    if (widget.records.isNotEmpty) {
      _compareReportIdA = widget.records.first.id;
      if (widget.records.length > 1) {
        _compareReportIdB = widget.records[1].id;
      } else {
        _compareReportIdB = widget.records.first.id;
      }
    }
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  List<String> _getAvailableBiomarkers() {
    final set = <String>{};
    for (final item in widget.records) {
      for (final r in item.referenceResults) {
        final name = r.canonicalName ?? r.originalTestName;
        if (name.isNotEmpty && r.numericValue != null) {
          set.add(name);
        }
      }
    }
    final list = set.toList();
    list.sort((a, b) => a.compareTo(b));
    return list;
  }

  @override
  Widget build(BuildContext context) {
    final availableBiomarkers = _getAvailableBiomarkers();

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Health Tracking & Trends'),
        bottom: TabBar(
          controller: _tabController,
          labelColor: Colors.white,
          unselectedLabelColor: Colors.white70,
          indicatorColor: AppColors.primaryContainer,
          tabs: const [
            Tab(icon: Icon(Icons.show_chart_rounded), text: 'Biomarker Trends'),
            Tab(icon: Icon(Icons.compare_arrows_rounded), text: 'Compare Reports'),
          ],
        ),
      ),
      body: SafeArea(
        child: Column(
          children: [
            const Padding(
              padding: EdgeInsets.fromLTRB(16, 12, 16, 4),
              child: DisclaimerBanner(),
            ),
            Expanded(
              child: TabBarView(
                controller: _tabController,
                children: [
                  _buildBiomarkerTrendsTab(availableBiomarkers),
                  _buildReportComparisonTab(),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 1: Biomarker Longitudinal Trends
  // ---------------------------------------------------------------------------

  Widget _buildBiomarkerTrendsTab(List<String> availableBiomarkers) {
    if (widget.records.isEmpty) {
      return const Center(
        child: Text(
          'No historical records available to analyze trends.',
          style: TextStyle(color: AppColors.textSecondary),
        ),
      );
    }

    if (availableBiomarkers.isEmpty) {
      return const Center(
        child: Padding(
          padding: EdgeInsets.all(24),
          child: Text(
            'No numeric biomarkers found across existing report records. '
            'Upload a medical report with standard blood tests to track trends over time.',
            textAlign: TextAlign.center,
            style: TextStyle(color: AppColors.textSecondary),
          ),
        ),
      );
    }

    final activeBiomarker = _selectedBiomarker ?? availableBiomarkers.first;
    final timelinePoints = _getTimelinePoints(activeBiomarker);

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Biomarker Selector Dropdown Card
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: AppColors.cardBorder),
            ),
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              child: Row(
                children: [
                  const Icon(Icons.analytics_rounded, color: AppColors.primary),
                  const SizedBox(width: 12),
                  const Text(
                    'Biomarker:',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: DropdownButtonHideUnderline(
                      child: DropdownButton<String>(
                        value: availableBiomarkers.contains(activeBiomarker)
                            ? activeBiomarker
                            : availableBiomarkers.first,
                        isExpanded: true,
                        icon: const Icon(Icons.arrow_drop_down, color: AppColors.primary),
                        items: availableBiomarkers.map((name) {
                          return DropdownMenuItem(
                            value: name,
                            child: Text(
                              name,
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          );
                        }).toList(),
                        onChanged: (val) {
                          if (val != null) {
                            setState(() => _selectedBiomarker = val);
                          }
                        },
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Overview Summary Card
          _buildBiomarkerOverviewCard(activeBiomarker, timelinePoints),
          const SizedBox(height: 16),

          // Longitudinal Progression Timeline
          const Text(
            'Timeline Progression',
            style: TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 10),
          _buildTimelineList(timelinePoints),
        ],
      ),
    );
  }

  List<_BiomarkerDataPoint> _getTimelinePoints(String biomarkerName) {
    final points = <_BiomarkerDataPoint>[];

    for (final item in widget.records) {
      final matches = item.referenceResults.where((r) {
        final name = r.canonicalName ?? r.originalTestName;
        return name.toLowerCase() == biomarkerName.toLowerCase() && r.numericValue != null;
      });

      for (final m in matches) {
        points.add(_BiomarkerDataPoint(
          reportId: item.id,
          reportName: item.documentName,
          date: item.createdAt,
          result: m,
        ));
      }
    }

    // Sort chronologically ascending
    points.sort((a, b) => a.date.compareTo(b.date));
    return points;
  }

  Widget _buildBiomarkerOverviewCard(
      String biomarkerName, List<_BiomarkerDataPoint> points) {
    if (points.isEmpty) {
      return const SizedBox.shrink();
    }

    final latest = points.last;
    final first = points.first;
    final diff = points.length > 1
        ? (latest.result.numericValue! - first.result.numericValue!)
        : null;

    final ref = latest.result.referenceRange;
    final refRangeStr = (ref?.normalLow != null && ref?.normalHigh != null)
        ? '${ref!.normalLow} - ${ref.normalHigh}'
        : 'Standard Clinical';

    return Card(
      elevation: 1,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.cardBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Expanded(
                  child: Text(
                    biomarkerName,
                    style: const TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                    ),
                  ),
                ),
                _buildClassificationChip(latest.result.classification),
              ],
            ),
            const SizedBox(height: 12),
            Row(
              crossAxisAlignment: CrossAxisAlignment.baseline,
              textBaseline: TextBaseline.alphabetic,
              children: [
                Text(
                  latest.result.numericValue!.toStringAsFixed(
                    latest.result.numericValue!.truncateToDouble() ==
                            latest.result.numericValue!
                        ? 0
                        : 2,
                  ),
                  style: const TextStyle(
                    fontSize: 32,
                    fontWeight: FontWeight.w800,
                    color: AppColors.textPrimary,
                  ),
                ),
                const SizedBox(width: 8),
                Text(
                  latest.result.normalizedUnit ?? latest.result.unit ?? '',
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textSecondary,
                  ),
                ),
                const Spacer(),
                if (diff != null) ...[
                  Icon(
                    diff > 0
                        ? Icons.trending_up_rounded
                        : (diff < 0
                            ? Icons.trending_down_rounded
                            : Icons.trending_flat_rounded),
                    size: 20,
                    color: diff == 0
                        ? AppColors.textSecondary
                        : (latest.result.classification == AnalyteClassification.high ||
                                latest.result.classification ==
                                    AnalyteClassification.critical
                            ? AppColors.critical
                            : AppColors.normal),
                  ),
                  const SizedBox(width: 4),
                  Text(
                    '${diff > 0 ? "+" : ""}${diff.toStringAsFixed(1)} net change',
                    style: TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.bold,
                      color: diff == 0
                          ? AppColors.textSecondary
                          : (latest.result.classification == AnalyteClassification.high ||
                                  latest.result.classification ==
                                      AnalyteClassification.critical
                              ? AppColors.critical
                              : AppColors.normal),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 12),
            const Divider(height: 1),
            const SizedBox(height: 10),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Reference Interval: $refRangeStr ${latest.result.normalizedUnit ?? ""}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w500,
                  ),
                ),
                Text(
                  '${points.length} record${points.length > 1 ? "s" : ""}',
                  style: const TextStyle(
                    fontSize: 12,
                    color: AppColors.textMuted,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ],
            ),
            if (latest.result.alertMessage != null &&
                latest.result.alertMessage!.isNotEmpty) ...[
              const SizedBox(height: 10),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                decoration: BoxDecoration(
                  color: AppColors.criticalBg.withValues(alpha: 0.5),
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.criticalBorder),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.info_outline, size: 16, color: AppColors.critical),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        latest.result.alertMessage!,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.critical,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ],
        ),
      ),
    );
  }

  Widget _buildTimelineList(List<_BiomarkerDataPoint> points) {
    if (points.isEmpty) {
      return const SizedBox.shrink();
    }

    return ListView.separated(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: points.length,
      separatorBuilder: (context, index) => const SizedBox(height: 8),
      itemBuilder: (context, index) {
        // Chronological order: reverse index so latest appears first
        final p = points[points.length - 1 - index];
        final dateStr =
            '${p.date.day.toString().padLeft(2, '0')}/${p.date.month.toString().padLeft(2, '0')}/${p.date.year}';

        return Container(
          padding: const EdgeInsets.all(14),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.cardBorder),
          ),
          child: Row(
            children: [
              Container(
                width: 36,
                height: 36,
                decoration: BoxDecoration(
                  color: AppColors.primaryContainer.withValues(alpha: 0.3),
                  shape: BoxShape.circle,
                ),
                child: Center(
                  child: Text(
                    '${points.length - index}',
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: AppColors.primaryDark,
                    ),
                  ),
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      p.reportName,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      dateStr,
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.textMuted,
                      ),
                    ),
                  ],
                ),
              ),
              Column(
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  Row(
                    children: [
                      Text(
                        '${p.result.numericValue} ',
                        style: const TextStyle(
                          fontSize: 15,
                          fontWeight: FontWeight.bold,
                          color: AppColors.textPrimary,
                        ),
                      ),
                      Text(
                        p.result.normalizedUnit ?? p.result.unit ?? '',
                        style: const TextStyle(
                          fontSize: 11,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  _buildClassificationChip(p.result.classification, isSmall: true),
                ],
              ),
            ],
          ),
        );
      },
    );
  }

  // ---------------------------------------------------------------------------
  // Tab 2: Side-by-Side Report Comparison
  // ---------------------------------------------------------------------------

  Widget _buildReportComparisonTab() {
    if (widget.records.length < 2) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.compare_arrows_rounded,
                  size: 48, color: AppColors.textMuted),
              const SizedBox(height: 12),
              const Text(
                'At least 2 reports are required to compare results.',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              const Text(
                'Upload another medical report to unlock side-by-side comparative analysis.',
                style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    final reportA = widget.records.firstWhere(
      (r) => r.id == _compareReportIdA,
      orElse: () => widget.records.first,
    );
    final reportB = widget.records.firstWhere(
      (r) => r.id == _compareReportIdB,
      orElse: () => widget.records.last,
    );

    // Build map of common analytes
    final mapA = <String, AnalysisResult>{};
    for (final r in reportA.referenceResults) {
      final name = r.canonicalName ?? r.originalTestName;
      mapA[name.toLowerCase()] = r;
    }

    final mapB = <String, AnalysisResult>{};
    for (final r in reportB.referenceResults) {
      final name = r.canonicalName ?? r.originalTestName;
      mapB[name.toLowerCase()] = r;
    }

    final allAnalytes = {...mapA.keys, ...mapB.keys}.toList();
    allAnalytes.sort();

    return SingleChildScrollView(
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Selectors Card
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(14),
              side: const BorderSide(color: AppColors.cardBorder),
            ),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                children: [
                  _buildReportDropdownRow(
                    label: 'Report A (Baseline):',
                    selectedId: reportA.id,
                    onChanged: (id) => setState(() => _compareReportIdA = id),
                  ),
                  const Divider(height: 20),
                  _buildReportDropdownRow(
                    label: 'Report B (Follow-up):',
                    selectedId: reportB.id,
                    onChanged: (id) => setState(() => _compareReportIdB = id),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          Text(
            'Comparing ${allAnalytes.length} Medical Parameters',
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 10),

          // Side-by-side comparison items
          ListView.separated(
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            itemCount: allAnalytes.length,
            separatorBuilder: (context, index) => const SizedBox(height: 10),
            itemBuilder: (context, index) {
              final key = allAnalytes[index];
              final resA = mapA[key];
              final resB = mapB[key];
              final displayName =
                  resB?.canonicalName ?? resA?.canonicalName ?? resB?.originalTestName ?? resA?.originalTestName ?? key;

              final valA = resA?.numericValue;
              final valB = resB?.numericValue;
              final unit = resB?.normalizedUnit ?? resA?.normalizedUnit ?? resB?.unit ?? resA?.unit ?? '';
              final delta = (valA != null && valB != null) ? (valB - valA) : null;

              return Card(
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(12),
                  side: const BorderSide(color: AppColors.cardBorder),
                ),
                child: Padding(
                  padding: const EdgeInsets.all(14),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Expanded(
                            child: Text(
                              displayName,
                              style: const TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                            ),
                          ),
                          if (delta != null) ...[
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 3),
                              decoration: BoxDecoration(
                                color: delta == 0
                                    ? AppColors.borderSubtle
                                    : (delta > 0
                                        ? AppColors.criticalBg
                                        : AppColors.normalBg),
                                borderRadius: BorderRadius.circular(6),
                              ),
                              child: Text(
                                '${delta > 0 ? "+" : ""}${delta.toStringAsFixed(1)} $unit',
                                style: TextStyle(
                                  fontSize: 12,
                                  fontWeight: FontWeight.bold,
                                  color: delta == 0
                                      ? AppColors.textSecondary
                                      : (delta > 0
                                          ? AppColors.critical
                                          : AppColors.normal),
                                ),
                              ),
                            ),
                          ],
                        ],
                      ),
                      const SizedBox(height: 10),
                      Row(
                        children: [
                          // Report A Value
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: AppColors.background,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Report A',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: AppColors.textMuted,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    valA != null
                                        ? '$valA $unit'
                                        : (resA?.originalValueText ?? 'Not in Report'),
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: AppColors.textPrimary,
                                    ),
                                  ),
                                  if (resA != null) ...[
                                    const SizedBox(height: 4),
                                    _buildClassificationChip(
                                        resA.classification,
                                        isSmall: true),
                                  ],
                                ],
                              ),
                            ),
                          ),
                          const SizedBox(width: 8),
                          const Icon(Icons.arrow_forward_rounded,
                              size: 16, color: AppColors.textMuted),
                          const SizedBox(width: 8),
                          // Report B Value
                          Expanded(
                            child: Container(
                              padding: const EdgeInsets.all(10),
                              decoration: BoxDecoration(
                                color: AppColors.background,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Report B',
                                    style: TextStyle(
                                      fontSize: 11,
                                      color: AppColors.textMuted,
                                      fontWeight: FontWeight.bold,
                                    ),
                                  ),
                                  const SizedBox(height: 2),
                                  Text(
                                    valB != null
                                        ? '$valB $unit'
                                        : (resB?.originalValueText ?? 'Not in Report'),
                                    style: const TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w600,
                                      color: AppColors.textPrimary,
                                    ),
                                  ),
                                  if (resB != null) ...[
                                    const SizedBox(height: 4),
                                    _buildClassificationChip(
                                        resB.classification,
                                        isSmall: true),
                                  ],
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              );
            },
          ),
        ],
      ),
    );
  }

  Widget _buildReportDropdownRow({
    required String label,
    required String selectedId,
    required ValueChanged<String> onChanged,
  }) {
    return Row(
      children: [
        SizedBox(
          width: 140,
          child: Text(
            label,
            style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: AppColors.textSecondary,
            ),
          ),
        ),
        Expanded(
          child: DropdownButtonHideUnderline(
            child: DropdownButton<String>(
              value: selectedId,
              isExpanded: true,
              items: widget.records.map((r) {
                final dateStr =
                    '${r.createdAt.day.toString().padLeft(2, '0')}/${r.createdAt.month.toString().padLeft(2, '0')}/${r.createdAt.year}';
                return DropdownMenuItem(
                  value: r.id,
                  child: Text(
                    '${r.documentName} ($dateStr)',
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w500,
                      color: AppColors.textPrimary,
                    ),
                  ),
                );
              }).toList(),
              onChanged: (id) {
                if (id != null) onChanged(id);
              },
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildClassificationChip(AnalyteClassification? classification,
      {bool isSmall = false}) {
    Color bg = AppColors.borderSubtle;
    Color border = AppColors.divider;
    Color text = AppColors.textSecondary;
    String label = 'NORMAL';

    switch (classification) {
      case AnalyteClassification.low:
        bg = AppColors.lowBg;
        border = AppColors.lowBorder;
        text = AppColors.low;
        label = 'LOW';
        break;
      case AnalyteClassification.normal:
        bg = AppColors.normalBg;
        border = AppColors.normalBorder;
        text = AppColors.normal;
        label = 'NORMAL';
        break;
      case AnalyteClassification.high:
        bg = AppColors.highBg;
        border = AppColors.highBorder;
        text = AppColors.high;
        label = 'HIGH';
        break;
      case AnalyteClassification.critical:
        bg = AppColors.criticalBg;
        border = AppColors.criticalBorder;
        text = AppColors.critical;
        label = 'CRITICAL';
        break;
      case AnalyteClassification.requiresReview:
      case null:
        bg = const Color(0xFFF1F5F9);
        border = const Color(0xFFCBD5E1);
        text = const Color(0xFF475569);
        label = 'REQUIRES REVIEW';
        break;
    }

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isSmall ? 6 : 8,
        vertical: isSmall ? 2 : 4,
      ),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: border),
      ),
      child: Text(
        label,
        style: TextStyle(
          fontSize: isSmall ? 10 : 11,
          fontWeight: FontWeight.bold,
          color: text,
        ),
      ),
    );
  }
}

class _BiomarkerDataPoint {
  final String reportId;
  final String reportName;
  final DateTime date;
  final AnalysisResult result;

  _BiomarkerDataPoint({
    required this.reportId,
    required this.reportName,
    required this.date,
    required this.result,
  });
}
