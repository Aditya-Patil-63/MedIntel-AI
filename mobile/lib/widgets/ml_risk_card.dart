import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/common/enums.dart';
import '../models/ml_risk/risk_prediction_response.dart';

/// Card rendering statistical disease risk probability or missing feature status.
class MLRiskCard extends StatelessWidget {
  final String title;
  final String conditionName;
  final RiskPredictionResponse? response;
  final String? errorMessage;
  final VoidCallback? onRetry;

  const MLRiskCard({
    super.key,
    required this.title,
    required this.conditionName,
    this.response,
    this.errorMessage,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.analytics_outlined, color: AppColors.secondary, size: 20),
                const SizedBox(width: 8),
                Text(
                  title,
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
                ),
                const Spacer(),
                if (response != null && response!.status == 'OK')
                  _buildRiskBandChip(response!.riskBand)
                else if (response != null && response!.status == 'INSUFFICIENT_FEATURES')
                  _buildStatusChip('INSUFFICIENT DATA', AppColors.highBg, AppColors.high, Icons.help_outline),
              ],
            ),
            const SizedBox(height: 10),
            _buildContent(context),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    if (errorMessage != null) {
      return Row(
        children: [
          const Icon(Icons.error_outline, size: 16, color: AppColors.critical),
          const SizedBox(width: 6),
          Expanded(
            child: Text(
              errorMessage!,
              style: const TextStyle(fontSize: 12, color: AppColors.critical),
            ),
          ),
          if (onRetry != null)
            TextButton(
              onPressed: onRetry,
              child: const Text('Retry', style: TextStyle(fontSize: 12)),
            ),
        ],
      );
    }

    if (response == null) {
      return const Text(
        'Awaiting evaluation...',
        style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
      );
    }

    if (response!.status == 'OK') {
      final prob = response!.riskProbability ?? 0.0;
      final pct = (prob * 100).toStringAsFixed(1);
      final band = response!.riskBand ?? 'UNKNOWN';

      return Semantics(
        label: 'Estimated $conditionName risk probability: $pct percent. Educational risk band: $band.',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Model-Estimated Risk Probability:',
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
                Text(
                  '$pct%',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16),
                ),
              ],
            ),
            const SizedBox(height: 6),
            ClipRRect(
              borderRadius: BorderRadius.circular(4),
              child: LinearProgressIndicator(
                value: prob,
                minHeight: 8,
                backgroundColor: AppColors.divider,
                valueColor: AlwaysStoppedAnimation<Color>(_getBarColor(prob)),
              ),
            ),
            const SizedBox(height: 6),
            Text(
              'Statistical model: ${response!.modelName ?? "Champion"} (Version: ${response!.modelVersion?.split("T").first ?? "Audited"})',
              style: const TextStyle(fontSize: 10, color: AppColors.textSecondary),
            ),
          ],
        ),
      );
    }

    if (response!.status == 'INSUFFICIENT_FEATURES') {
      final supplied = response!.suppliedFeaturesCount;
      final requiredCount = response!.requiredFeaturesCount;
      final missing = response!.missingFeatures;

      return Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            'Insufficient features for complete ML assessment ($supplied of $requiredCount provided).',
            style: const TextStyle(fontSize: 12, fontWeight: FontWeight.w600, color: AppColors.textPrimary),
          ),
          const SizedBox(height: 4),
          if (missing.isNotEmpty)
            Text(
              'Missing parameters: ${missing.take(4).join(", ")}${missing.length > 4 ? " and ${missing.length - 4} more" : ""}.',
              style: const TextStyle(fontSize: 11, color: AppColors.textSecondary),
            ),
          const SizedBox(height: 4),
          const Text(
            'Note: Zero default values were substituted. Missing parameters prevent statistical risk estimation.',
            style: TextStyle(fontSize: 10, color: AppColors.textSecondary, fontStyle: FontStyle.italic),
          ),
        ],
      );
    }

    return Text(
      'Status: ${response!.status}',
      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
    );
  }

  Color _getBarColor(double prob) {
    if (prob < 0.30) return AppColors.normal;
    if (prob < 0.70) return AppColors.high;
    return AppColors.critical;
  }

  Widget _buildRiskBandChip(RiskBand? band) {
    Color bg;
    Color fg;
    IconData icon;
    final b = (band?.value ?? 'LOW').toUpperCase();

    switch (b) {
      case 'LOW':
        bg = AppColors.normalBg;
        fg = AppColors.normal;
        icon = Icons.check_circle_outline;
        break;
      case 'MODERATE':
        bg = AppColors.highBg;
        fg = AppColors.high;
        icon = Icons.warning_amber_rounded;
        break;
      case 'ELEVATED':
      case 'HIGH':
        bg = AppColors.criticalBg;
        fg = AppColors.critical;
        icon = Icons.priority_high_rounded;
        break;
      default:
        bg = Colors.grey.shade100;
        fg = Colors.grey.shade700;
        icon = Icons.info_outline;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: fg),
          const SizedBox(width: 4),
          Text(
            '$b RISK',
            style: TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: fg),
          ),
        ],
      ),
    );
  }

  Widget _buildStatusChip(String label, Color bg, Color fg, IconData icon) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: fg),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(fontSize: 10, fontWeight: FontWeight.bold, color: fg),
          ),
        ],
      ),
    );
  }
}
