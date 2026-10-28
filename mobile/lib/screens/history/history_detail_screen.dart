import 'package:flutter/material.dart';
import '../../core/theme/app_colors.dart';
import '../../models/common/enums.dart';
import '../../models/history/analysis_history_item.dart';
import '../../models/ml_risk/risk_prediction_response.dart';
import '../../widgets/disclaimer_banner.dart';

/// Read-only inspection screen displaying an immutable historical analysis snapshot.
///
/// Strictly displays data preserved in the history record; does NOT make any network
/// or medical API calls.
class HistoryDetailScreen extends StatelessWidget {
  final AnalysisHistoryItem item;

  const HistoryDetailScreen({super.key, required this.item});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Historical Analysis'),
        elevation: 0,
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Mandatory Educational Disclaimer Banner
              const DisclaimerBanner(),
              const SizedBox(height: 12),

              // 2. Read-Only Historical Snapshot Banner (Exact text required by e2e tests)
              Container(
                width: double.infinity,
                padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                decoration: BoxDecoration(
                  color: AppColors.warningBg,
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppColors.warning.withValues(alpha: 0.3)),
                ),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Icon(Icons.history, color: AppColors.warning, size: 20),
                    const SizedBox(width: 10),
                    Expanded(
                      child: Text(
                        'Historical Snapshot (Read-Only) • Saved on ${item.formattedDate}. '
                        'Results represent the exact analysis state when recorded.',
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF92400E),
                          fontWeight: FontWeight.w600,
                          height: 1.3,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // 3. Document & Patient Context Card
              _buildContextCard(),
              const SizedBox(height: 20),

              // 4. Laboratory Reference Findings
              _buildReferenceFindingsSection(),
              const SizedBox(height: 20),

              // 5. ML Disease Risk Indicators
              _buildMLRiskSection(),
              const SizedBox(height: 20),

              // 6. Educational GenAI Explanation
              _buildGenAISection(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContextCard() {
    final ageText = item.patientAge != null
        ? '${item.patientAge!.toStringAsFixed(0)} yrs'
        : '—';
    final sexText = item.patientSex ?? '—';

    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [BoxStyle.cardShadow],
      ),
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: AppColors.primaryLight.withValues(alpha: 0.12),
                  borderRadius: BorderRadius.circular(10),
                ),
                child: const Icon(Icons.description_outlined, color: AppColors.primary, size: 22),
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
                        fontSize: 16,
                        color: AppColors.textPrimary,
                      ),
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                    ),
                    const SizedBox(height: 2),
                    Text(
                      'Recorded: ${item.formattedDate}',
                      style: const TextStyle(fontSize: 12, color: AppColors.textMuted),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const Padding(
            padding: EdgeInsets.symmetric(vertical: 12),
            child: Divider(height: 1, color: AppColors.divider),
          ),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              _buildContextMetaPill(
                icon: Icons.check_circle_outline,
                label: 'Verified Tests',
                value: '${item.verifiedMeasurementCount}',
              ),
              _buildContextMetaPill(
                icon: Icons.cake_outlined,
                label: 'Age',
                value: ageText,
              ),
              _buildContextMetaPill(
                icon: Icons.person_outline,
                label: 'Sex',
                value: sexText,
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildContextMetaPill({required IconData icon, required String label, required String value}) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 14, color: AppColors.textSecondary),
            const SizedBox(width: 4),
            Text(label, style: const TextStyle(fontSize: 11, color: AppColors.textSecondary)),
          ],
        ),
        const SizedBox(height: 2),
        Text(
          value,
          style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
        ),
      ],
    );
  }

  Widget _buildReferenceFindingsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Laboratory Reference Range Findings',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
        ),
        const SizedBox(height: 4),
        const Text(
          'Phase 6 deterministic interval comparison preserved from completed analysis.',
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 12),
        if (item.referenceResults.isEmpty)
          Container(
            width: double.infinity,
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.cardSurface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.cardBorder),
            ),
            child: const Text('No laboratory test results recorded.', style: TextStyle(color: AppColors.textMuted)),
          )
        else
          Container(
            decoration: BoxDecoration(
              color: AppColors.cardSurface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.cardBorder),
              boxShadow: [BoxStyle.cardShadow],
            ),
            child: Column(
              children: [
                // Header summary badges
                Padding(
                  padding: const EdgeInsets.all(14),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      _buildCountChip(
                        'Total: ${item.referenceResults.length}',
                        AppColors.primary,
                        AppColors.primaryLight.withValues(alpha: 0.12),
                      ),
                      if (item.normalCount > 0)
                        _buildCountChip('Normal: ${item.normalCount}', AppColors.normal, AppColors.normalBg),
                      if (item.lowCount > 0)
                        _buildCountChip('Low: ${item.lowCount}', AppColors.low, AppColors.lowBg),
                      if (item.highCount > 0)
                        _buildCountChip('High: ${item.highCount}', AppColors.high, AppColors.highBg),
                      if (item.criticalCount > 0)
                        _buildCountChip('Critical: ${item.criticalCount}', AppColors.critical, AppColors.criticalBg),
                    ],
                  ),
                ),
                const Divider(height: 1, color: AppColors.divider),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: item.referenceResults.length,
                  separatorBuilder: (_, _) => const Divider(height: 1, color: AppColors.divider),
                  itemBuilder: (context, index) {
                    final res = item.referenceResults[index];
                    final ref = res.referenceRange;
                    final intervalText = ref != null
                        ? '${ref.normalLow ?? "—"} – ${ref.normalHigh ?? "—"} ${ref.unit}'
                        : 'Interval not available';

                    return Padding(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      child: Row(
                        children: [
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  res.canonicalName ?? res.originalTestName,
                                  style: const TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 14,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 3),
                                Text(
                                  'Value: ${res.numericValue ?? res.originalValueText ?? "—"} ${res.unit ?? ""} • Ref: $intervalText',
                                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                                ),
                              ],
                            ),
                          ),
                          const SizedBox(width: 8),
                          _buildClassificationChip(res.classification),
                        ],
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
      ],
    );
  }

  Widget _buildClassificationChip(AnalyteClassification? classification) {
    if (classification == null) {
      return const Chip(label: Text('UNKNOWN'));
    }

    Color bg;
    Color fg;

    switch (classification) {
      case AnalyteClassification.low:
        bg = AppColors.lowBg;
        fg = AppColors.low;
        break;
      case AnalyteClassification.normal:
        bg = AppColors.normalBg;
        fg = AppColors.normal;
        break;
      case AnalyteClassification.high:
        bg = AppColors.highBg;
        fg = AppColors.high;
        break;
      case AnalyteClassification.critical:
        bg = AppColors.criticalBg;
        fg = AppColors.critical;
        break;
      case AnalyteClassification.requiresReview:
        bg = const Color(0xFFF1F5F9);
        fg = const Color(0xFF475569);
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: fg.withValues(alpha: 0.3)),
      ),
      child: Text(
        classification.value.toUpperCase(),
        style: TextStyle(
          color: fg,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Widget _buildCountChip(String label, Color fg, Color bg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withValues(alpha: 0.2)),
      ),
      child: Text(
        label,
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: fg),
      ),
    );
  }

  Widget _buildMLRiskSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Statistical Disease Risk Indicators',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
        ),
        const SizedBox(height: 4),
        const Text(
          'Multivariate ML probability scores preserved from completed analysis.',
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 12),
        _buildMLCard('Diabetes Risk Model', item.diabetesRisk),
        const SizedBox(height: 10),
        _buildMLCard('Heart Disease Risk Model', item.heartRisk),
        const SizedBox(height: 10),
        _buildMLCard('Chronic Kidney Disease Model', item.kidneyRisk),
      ],
    );
  }

  Widget _buildMLCard(String title, RiskPredictionResponse? risk) {
    if (risk == null) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.cardSurface,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: AppColors.cardBorder),
        ),
        child: Row(
          children: [
            const Icon(Icons.info_outline, color: AppColors.textMuted, size: 18),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                '$title: Not evaluated in this run',
                style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
            ),
          ],
        ),
      );
    }

    final isOk = risk.status == 'OK';
    final isInsufficient = risk.status == 'INSUFFICIENT_FEATURES';

    return Container(
      decoration: BoxDecoration(
        color: AppColors.cardSurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: [BoxStyle.cardShadow],
      ),
      padding: const EdgeInsets.all(14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                title,
                style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 14, color: AppColors.textPrimary),
              ),
              if (isOk && risk.riskBand != null)
                _buildRiskBandChip(risk.riskBand!)
              else if (isInsufficient)
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: AppColors.warningBg,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.warning.withValues(alpha: 0.4)),
                  ),
                  child: const Text(
                    'INSUFFICIENT FEATURES',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.bold,
                      color: AppColors.warning,
                    ),
                  ),
                ),
            ],
          ),
          const SizedBox(height: 8),
          if (isOk && risk.riskProbability != null) ...[
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Estimated Risk Probability',
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
                Text(
                  '${(risk.riskProbability! * 100).toStringAsFixed(1)}%',
                  style: const TextStyle(fontSize: 13, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: risk.riskProbability,
                minHeight: 8,
                backgroundColor: AppColors.divider,
                valueColor: AlwaysStoppedAnimation<Color>(_getRiskColor(risk.riskBand)),
              ),
            ),
          ] else if (isInsufficient) ...[
            Text(
              'Missing required clinical features: ${risk.missingFeatures.join(", ")}',
              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildRiskBandChip(RiskBand band) {
    Color color = _getRiskColor(band);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color.withValues(alpha: 0.5)),
      ),
      child: Text(
        band.value.toUpperCase(),
        style: TextStyle(
          color: color,
          fontSize: 11,
          fontWeight: FontWeight.bold,
        ),
      ),
    );
  }

  Color _getRiskColor(RiskBand? band) {
    if (band == null) return Colors.grey;
    switch (band) {
      case RiskBand.low:
        return AppColors.normal;
      case RiskBand.moderate:
        return AppColors.high;
      case RiskBand.elevated:
        return AppColors.critical;
    }
  }

  Widget _buildGenAISection() {
    final exp = item.genAiExplanation?.explanation;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            const Text(
              'Educational AI Explanation',
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: AppColors.textPrimary),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: AppColors.primaryLight.withValues(alpha: 0.12),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'Language: ${item.selectedLanguage.name}',
                style: const TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primary,
                ),
              ),
            ),
          ],
        ),
        const SizedBox(height: 10),
        if (exp != null)
          Container(
            decoration: BoxDecoration(
              color: AppColors.cardSurface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.cardBorder),
              boxShadow: [BoxStyle.cardShadow],
            ),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  exp.summary,
                  style: const TextStyle(fontSize: 14, height: 1.5, color: AppColors.textPrimary),
                ),
                if (exp.followUpGuidance.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  const Text(
                    'Next Steps & Discussion Points:',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 6),
                  for (final g in exp.followUpGuidance)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('• ', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                          Expanded(
                            child: Text(
                              g,
                              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.3),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
                if (exp.recommendedQuestionsForDoctor.isNotEmpty) ...[
                  const SizedBox(height: 14),
                  const Text(
                    'Questions to Ask Your Doctor:',
                    style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13, color: AppColors.textPrimary),
                  ),
                  const SizedBox(height: 6),
                  for (final q in exp.recommendedQuestionsForDoctor)
                    Padding(
                      padding: const EdgeInsets.only(bottom: 6),
                      child: Row(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Text('? ', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                          Expanded(
                            child: Text(
                              q,
                              style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.3),
                            ),
                          ),
                        ],
                      ),
                    ),
                ],
              ],
            ),
          )
        else
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.cardSurface,
              borderRadius: BorderRadius.circular(16),
              border: Border.all(color: AppColors.cardBorder),
            ),
            child: const Row(
              children: [
                Icon(Icons.info_outline, color: AppColors.textMuted, size: 18),
                SizedBox(width: 8),
                Expanded(
                  child: Text(
                    'AI explanation was unavailable or not generated when this historical record was saved.',
                    style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                  ),
                ),
              ],
            ),
          ),
      ],
    );
  }
}
