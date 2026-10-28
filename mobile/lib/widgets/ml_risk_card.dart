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

  static const Map<String, String> _friendlyFeatureNames = {
    // Diabetes
    'Pregnancies': 'Pregnancies',
    'Glucose': 'Plasma Glucose',
    'BloodPressure': 'Diastolic Blood Pressure',
    'SkinThickness': 'Triceps Skin Fold Thickness',
    'Insulin': 'Serum Insulin',
    'BMI': 'Body Mass Index (BMI)',
    'DiabetesPedigreeFunction': 'Diabetes Family History Score',
    'Age': 'Age',
    // Heart Disease
    'age': 'Age',
    'sex': 'Gender',
    'cp': 'Chest Pain Type',
    'trestbps': 'Resting Blood Pressure',
    'chol': 'Serum Cholesterol',
    'fbs': 'Fasting Blood Sugar',
    'restecg': 'Resting ECG',
    'thalach': 'Maximum Heart Rate',
    'exang': 'Exercise Angina',
    'oldpeak': 'ST Depression',
    'slope': 'ST Segment Slope',
    'ca': 'Major Vessels (Fluoroscopy)',
    'thal': 'Thalassemia Indicator',
    // Chronic Kidney Disease
    'bp': 'Blood Pressure',
    'sg': 'Specific Gravity (Urine)',
    'al': 'Albumin (Urine)',
    'su': 'Sugar (Urine)',
    'rbc': 'Red Blood Cells',
    'pc': 'Pus Cells',
    'pcc': 'Pus Cell Clumps',
    'ba': 'Bacteria',
    'bgr': 'Blood Glucose Random',
    'bu': 'Blood Urea',
    'sc': 'Serum Creatinine',
    'sod': 'Sodium',
    'pot': 'Potassium',
    'hemo': 'Hemoglobin',
    'pcv': 'Packed Cell Volume (Hematocrit)',
    'wc': 'White Blood Cell Count',
    'rc': 'Red Blood Cell Count',
    'htn': 'Hypertension',
    'dm': 'Diabetes Mellitus',
    'cad': 'Coronary Artery Disease',
    'appet': 'Appetite',
    'pe': 'Pedal Edema',
    'ane': 'Anemia',
  };

  static String _formatFeatureName(String raw) {
    return _friendlyFeatureNames[raw] ?? raw;
  }

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(7),
                  decoration: BoxDecoration(
                    color: AppColors.secondarySurface,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.insights_rounded,
                    color: AppColors.secondary,
                    size: 18,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Text(
                    title,
                    style: const TextStyle(
                      fontWeight: FontWeight.bold,
                      fontSize: 15,
                      color: AppColors.textPrimary,
                      letterSpacing: -0.2,
                    ),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
                const SizedBox(width: 8),
                if (response != null && response!.status == 'OK')
                  _buildRiskBandChip(response!.riskBand)
                else if (response != null &&
                    response!.status == 'INSUFFICIENT_FEATURES')
                  _buildStatusChip(
                    'INSUFFICIENT DATA',
                    AppColors.highBg,
                    AppColors.high,
                    Icons.help_outline,
                  ),
              ],
            ),
            const SizedBox(height: 12),
            _buildContent(context),
          ],
        ),
      ),
    );
  }

  Widget _buildContent(BuildContext context) {
    if (errorMessage != null) {
      return Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: AppColors.criticalBg,
          borderRadius: BorderRadius.circular(8),
        ),
        child: Row(
          children: [
            const Icon(Icons.error_outline,
                size: 16, color: AppColors.critical),
            const SizedBox(width: 8),
            Expanded(
              child: Text(
                errorMessage!,
                style:
                    const TextStyle(fontSize: 12, color: AppColors.critical),
              ),
            ),
            if (onRetry != null)
              TextButton(
                onPressed: onRetry,
                child: const Text('Retry', style: TextStyle(fontSize: 12)),
              ),
          ],
        ),
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
        label:
            'Estimated $conditionName risk probability: $pct percent. Educational risk band: $band.',
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Text(
                  'Model-Estimated Risk Probability:',
                  style:
                      TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
                Text(
                  '$pct%',
                  style: const TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 16,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            ClipRRect(
              borderRadius: BorderRadius.circular(6),
              child: LinearProgressIndicator(
                value: prob,
                minHeight: 8,
                backgroundColor: const Color(0xFFF1F5F9),
                valueColor: AlwaysStoppedAnimation<Color>(_getBarColor(prob)),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Statistical model: ${response!.modelName ?? "Champion"} (Version: ${response!.modelVersion?.split("T").first ?? "Audited"})',
                  style: const TextStyle(
                    fontSize: 10,
                    color: AppColors.textMuted,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 4),
            const Text(
              'Statistical risk estimate based on research models. This is not a diagnosis.',
              style: TextStyle(
                fontSize: 10,
                color: AppColors.textSecondary,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
      );
    }

    if (response!.status == 'INSUFFICIENT_FEATURES') {
      final supplied = response!.suppliedFeaturesCount;
      final requiredCount = response!.requiredFeaturesCount;
      final missing = response!.missingFeatures;

      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: const Color(0xFFF8FAFC),
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.divider),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Insufficient features for complete ML assessment.',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 2),
            Text(
              'Provided $supplied of $requiredCount clinical features.',
              style: const TextStyle(
                fontSize: 11,
                color: AppColors.textSecondary,
              ),
            ),
            if (missing.isNotEmpty) ...[
              const SizedBox(height: 6),
              Text(
                'Not tested in this report: ${missing.map(_formatFeatureName).join(", ")}',
                style: const TextStyle(
                  fontSize: 11,
                  color: AppColors.textSecondary,
                  height: 1.35,
                ),
              ),
            ],
            const SizedBox(height: 6),
            const Text(
              'Note: These parameters were not part of the uploaded laboratory panel. In accordance with clinical safety rules, missing features are never fabricated or guessed.',
              style: TextStyle(
                fontSize: 10,
                color: AppColors.textMuted,
                fontStyle: FontStyle.italic,
              ),
            ),
          ],
        ),
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
        bg = const Color(0xFFF1F5F9);
        fg = AppColors.textSecondary;
        icon = Icons.info_outline;
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
            '$b RISK',
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

  Widget _buildStatusChip(
    String label,
    Color bg,
    Color fg,
    IconData icon,
  ) {
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
            label,
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }
}
