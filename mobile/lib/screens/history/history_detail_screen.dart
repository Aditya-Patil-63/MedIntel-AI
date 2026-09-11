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
      appBar: AppBar(
        title: const Text('Historical Analysis'),
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

              // 2. Read-Only Historical Snapshot Banner
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFFEF3C7), // Light amber
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFFFCD34D)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.history, color: Color(0xFFB45309), size: 20),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Historical Snapshot (Read-Only) • Saved on ${item.formattedDate}. '
                        'Results represent the exact analysis state when recorded.',
                        style: const TextStyle(
                          fontSize: 12,
                          color: Color(0xFF92400E),
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // 3. Document & Patient Context Card
              _buildContextCard(),
              const SizedBox(height: 16),

              // 4. Laboratory Reference Findings
              _buildReferenceFindingsSection(),
              const SizedBox(height: 16),

              // 5. ML Disease Risk Indicators
              _buildMLRiskSection(),
              const SizedBox(height: 16),

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

    return Card(
      elevation: 0,
      color: const Color(0xFFF8FAFC),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.description_outlined,
                    color: AppColors.primary, size: 20),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(
                    item.documentName,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 16,
                    ),
                  ),
                ),
              ],
            ),
            const Divider(height: 20),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Verified Tests: ${item.verifiedMeasurementCount}',
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
                Text(
                  'Age: $ageText • Sex: $sexText',
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textSecondary,
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildReferenceFindingsSection() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Laboratory Reference Range Findings',
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        const Text(
          'Phase 6 deterministic interval comparison preserved from completed analysis.',
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 10),
        if (item.referenceResults.isEmpty)
          const Card(
            child: Padding(
              padding: EdgeInsets.all(16),
              child: Text('No laboratory test results recorded.'),
            ),
          )
        else
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: const BorderSide(color: AppColors.divider),
            ),
            child: Column(
              children: [
                // Header summary badges
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 6,
                    children: [
                      _buildCountChip('Total: ${item.referenceResults.length}',
                          AppColors.primary, AppColors.primaryLight.withValues(alpha: 0.1)),
                      if (item.normalCount > 0)
                        _buildCountChip('Normal: ${item.normalCount}',
                            AppColors.normal, AppColors.normalBg),
                      if (item.lowCount > 0)
                        _buildCountChip('Low: ${item.lowCount}', AppColors.low,
                            AppColors.lowBg),
                      if (item.highCount > 0)
                        _buildCountChip('High: ${item.highCount}',
                            AppColors.high, AppColors.highBg),
                      if (item.criticalCount > 0)
                        _buildCountChip('Critical: ${item.criticalCount}',
                            AppColors.critical, AppColors.criticalBg),
                    ],
                  ),
                ),
                const Divider(height: 1),
                ListView.separated(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: item.referenceResults.length,
                  separatorBuilder: (_, _) => const Divider(height: 1),
                  itemBuilder: (context, index) {
                    final res = item.referenceResults[index];
                    final ref = res.referenceRange;
                    final intervalText = ref != null
                        ? '${ref.normalLow ?? "—"} – ${ref.normalHigh ?? "—"} ${ref.unit}'
                        : 'Interval not available';

                    return ListTile(
                      title: Text(
                        res.canonicalName ?? res.originalTestName,
                        style: const TextStyle(
                            fontWeight: FontWeight.bold, fontSize: 14),
                      ),
                      subtitle: Text(
                        'Value: ${res.numericValue ?? res.originalValueText ?? "—"} ${res.unit ?? ""} • Ref: $intervalText',
                        style: const TextStyle(
                            fontSize: 12, color: AppColors.textSecondary),
                      ),
                      trailing: _buildClassificationChip(res.classification),
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
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: fg.withValues(alpha: 0.5)),
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
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(8),
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
          style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
        ),
        const SizedBox(height: 4),
        const Text(
          'Multivariate ML probability scores preserved from completed analysis.',
          style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        const SizedBox(height: 10),
        _buildMLCard('Diabetes Risk Model', item.diabetesRisk),
        const SizedBox(height: 8),
        _buildMLCard('Heart Disease Risk Model', item.heartRisk),
        const SizedBox(height: 8),
        _buildMLCard('Chronic Kidney Disease Model', item.kidneyRisk),
      ],
    );
  }

  Widget _buildMLCard(String title, RiskPredictionResponse? risk) {
    if (risk == null) {
      return Card(
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              const Icon(Icons.info_outline, color: AppColors.textMuted, size: 18),
              const SizedBox(width: 8),
              Text(
                '$title: Not evaluated in this run',
                style: const TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
      );
    }

    final isOk = risk.status == 'OK';
    final isInsufficient = risk.status == 'INSUFFICIENT_FEATURES';

    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                      fontWeight: FontWeight.bold, fontSize: 14),
                ),
                if (isOk && risk.riskBand != null)
                  _buildRiskBandChip(risk.riskBand!)
                else if (isInsufficient)
                  Container(
                    padding:
                        const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: Colors.amber.shade50,
                      borderRadius: BorderRadius.circular(8),
                      border: Border.all(color: Colors.amber.shade300),
                    ),
                    child: const Text(
                      'INSUFFICIENT FEATURES',
                      style: TextStyle(
                          fontSize: 10,
                          fontWeight: FontWeight.bold,
                          color: Colors.amber),
                    ),
                  ),
              ],
            ),
            const SizedBox(height: 6),
            if (isOk && risk.riskProbability != null) ...[
              Text(
                'Estimated Risk Probability: ${(risk.riskProbability! * 100).toStringAsFixed(1)}%',
                style: const TextStyle(
                    fontSize: 13, fontWeight: FontWeight.w600),
              ),
              const SizedBox(height: 4),
              ClipRRect(
                borderRadius: BorderRadius.circular(4),
                child: LinearProgressIndicator(
                  value: risk.riskProbability,
                  minHeight: 6,
                  backgroundColor: Colors.grey.shade200,
                  valueColor: AlwaysStoppedAnimation<Color>(
                    _getRiskColor(risk.riskBand),
                  ),
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
      ),
    );
  }

  Widget _buildRiskBandChip(RiskBand band) {
    Color color = _getRiskColor(band);
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.1),
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: color),
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
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
              decoration: BoxDecoration(
                color: AppColors.primaryLight.withValues(alpha: 0.15),
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
        const SizedBox(height: 8),
        if (exp != null)
          Card(
            shape: RoundedRectangleBorder(
              borderRadius: BorderRadius.circular(10),
              side: const BorderSide(color: AppColors.divider),
            ),
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    exp.summary,
                    style: const TextStyle(fontSize: 14, height: 1.4),
                  ),
                  if (exp.followUpGuidance.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    const Text(
                      'Next Steps & Discussion Points:',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    const SizedBox(height: 4),
                    for (final g in exp.followUpGuidance)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('• ', style: TextStyle(fontWeight: FontWeight.bold)),
                            Expanded(child: Text(g, style: const TextStyle(fontSize: 12))),
                          ],
                        ),
                      ),
                  ],
                  if (exp.recommendedQuestionsForDoctor.isNotEmpty) ...[
                    const SizedBox(height: 12),
                    const Text(
                      'Questions to Ask Your Doctor:',
                      style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                    ),
                    const SizedBox(height: 4),
                    for (final q in exp.recommendedQuestionsForDoctor)
                      Padding(
                        padding: const EdgeInsets.only(bottom: 4),
                        child: Row(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text('? ', style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.primary)),
                            Expanded(child: Text(q, style: const TextStyle(fontSize: 12))),
                          ],
                        ),
                      ),
                  ],
                ],
              ),
            ),
          )
        else
          Card(
            child: Padding(
              padding: const EdgeInsets.all(14),
              child: Row(
                children: [
                  const Icon(Icons.info_outline, color: AppColors.textMuted, size: 18),
                  const SizedBox(width: 8),
                  const Expanded(
                    child: Text(
                      'AI explanation was unavailable or not generated when this historical record was saved.',
                      style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
          ),
      ],
    );
  }
}
