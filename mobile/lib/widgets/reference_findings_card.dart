import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/common/enums.dart';
import '../models/reference/analysis_result.dart';
import '../models/reference/batch_analysis.dart';

/// Renders deterministic laboratory reference range findings from Phase 6.
class ReferenceFindingsCard extends StatelessWidget {
  final BatchAnalysisResponse? response;
  final String? errorMessage;

  const ReferenceFindingsCard({
    super.key,
    this.response,
    this.errorMessage,
  });

  @override
  Widget build(BuildContext context) {
    if (errorMessage != null && response == null) {
      return Card(
        color: AppColors.criticalBg,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
          side: const BorderSide(color: AppColors.criticalBorder),
        ),
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Row(
            children: [
              const Icon(Icons.error_outline, color: AppColors.critical),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Reference Analysis Error',
                      style: TextStyle(
                        fontWeight: FontWeight.bold,
                        color: AppColors.critical,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(errorMessage!, style: const TextStyle(fontSize: 13)),
                  ],
                ),
              ),
            ],
          ),
        ),
      );
    }

    if (response == null || response!.results.isEmpty) {
      return const SizedBox.shrink();
    }

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppColors.primarySurface,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: const Icon(
                    Icons.biotech_outlined,
                    color: AppColors.primary,
                    size: 20,
                  ),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Laboratory Reference Findings',
                    style: TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                      color: AppColors.textPrimary,
                      letterSpacing: -0.3,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.primaryContainer,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Text(
                    '${response!.totalClassified}/${response!.totalSubmitted} Evaluated',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.bold,
                      color: AppColors.primaryDark,
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Deterministic classification against published medical laboratory intervals.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
            const Divider(height: 24),
            ListView.separated(
              shrinkWrap: true,
              physics: const NeverScrollableScrollPhysics(),
              itemCount: response!.results.length,
              separatorBuilder: (_, _) => const Divider(height: 20),
              itemBuilder: (context, index) {
                final item = response!.results[index];
                return _buildAnalyteRow(context, item);
              },
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildAnalyteRow(BuildContext context, AnalysisResult item) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    item.canonicalName ?? item.originalTestName,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 14,
                      color: AppColors.textPrimary,
                    ),
                  ),
                  if (item.canonicalName != null &&
                      item.canonicalName != item.originalTestName)
                    Text(
                      'Reported as: ${item.originalTestName}',
                      style: const TextStyle(
                        fontSize: 11,
                        color: AppColors.textSecondary,
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            _buildClassificationChip(item),
          ],
        ),
        const SizedBox(height: 6),
        Row(
          children: [
            const Text(
              'Observed: ',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
            Text(
              '${item.numericValue ?? item.originalValueText ?? "N/A"} ${item.normalizedUnit ?? item.unit ?? ""}',
              style: const TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: AppColors.primaryDark,
              ),
            ),
            if (item.referenceRange != null) ...[
              const SizedBox(width: 12),
              Expanded(
                child: Text(
                  'Range: ${item.referenceRange!.normalLow ?? "?"} - ${item.referenceRange!.normalHigh ?? "?"} ${item.referenceRange!.unit}',
                  style: const TextStyle(
                    fontSize: 11,
                    color: AppColors.textSecondary,
                  ),
                  overflow: TextOverflow.ellipsis,
                ),
              ),
            ],
          ],
        ),
        if (item.referenceSource != null) ...[
          const SizedBox(height: 3),
          Text(
            'Source: ${item.referenceSource}',
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.textMuted,
              fontStyle: FontStyle.italic,
            ),
          ),
        ],
        if (item.warnings.isNotEmpty) ...[
          const SizedBox(height: 4),
          ...item.warnings.map(
            (w) => Row(
              children: [
                const Icon(Icons.info_outline, size: 12, color: AppColors.high),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    w,
                    style:
                        const TextStyle(fontSize: 11, color: AppColors.high),
                  ),
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildClassificationChip(AnalysisResult item) {
    if (item.classification != null) {
      Color bg;
      Color fg;
      IconData icon;
      final c = item.classification!;

      switch (c) {
        case AnalyteClassification.low:
          bg = AppColors.lowBg;
          fg = AppColors.low;
          icon = Icons.arrow_downward;
          break;
        case AnalyteClassification.normal:
          bg = AppColors.normalBg;
          fg = AppColors.normal;
          icon = Icons.check;
          break;
        case AnalyteClassification.high:
          bg = AppColors.highBg;
          fg = AppColors.high;
          icon = Icons.arrow_upward;
          break;
        case AnalyteClassification.critical:
          bg = AppColors.criticalBg;
          fg = AppColors.critical;
          icon = Icons.warning_amber_rounded;
          break;
      }

      return Container(
        padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
        decoration: BoxDecoration(
          color: bg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: fg.withValues(alpha: 0.3)),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(icon, size: 12, color: fg),
            const SizedBox(width: 4),
            Text(
              c.value.toUpperCase(),
              style: TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: fg,
              ),
            ),
          ],
        ),
      );
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: const Color(0xFFF1F5F9),
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        item.analysisStatus,
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }
}
