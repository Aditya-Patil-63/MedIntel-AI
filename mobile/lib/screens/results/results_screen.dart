import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../state/analysis/analysis_cubit.dart';
import '../../state/analysis/analysis_state.dart';
import '../../widgets/disclaimer_banner.dart';
import '../../widgets/genai_explanation_card.dart';
import '../../widgets/ml_risk_card.dart';
import '../../widgets/reference_findings_card.dart';

/// Comprehensive clinical analysis results dashboard rendering Phase 6 deterministic
/// reference findings, Phase 7 ML risk estimation, and Phase 8 GenAI explanations.
class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis & Risk Assessment'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Re-analyze',
            onPressed: () {
              final snap = context.read<AnalysisCubit>().state.snapshot;
              if (snap != null) {
                context.read<AnalysisCubit>().runFullAnalysis(snap);
              }
            },
          ),
        ],
      ),
      body: SafeArea(
        child: BlocBuilder<AnalysisCubit, AnalysisState>(
          builder: (context, state) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // 1. Mandatory Educational Non-Diagnostic Disclaimer
                  const DisclaimerBanner(),
                  const SizedBox(height: 12),

                  // 2. Loading State Indicator
                  if (state.isLoading) ...[
                    Card(
                      elevation: 0,
                      color: AppColors.primaryLight.withValues(alpha: 0.1),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: const BorderSide(color: AppColors.primaryLight),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Row(
                          children: [
                            const SizedBox(
                              width: 20,
                              height: 20,
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                            const SizedBox(width: 12),
                            Expanded(
                              child: Text(
                                state.loadingStage ?? 'Analyzing clinical measurements...',
                                style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w600),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 12),
                  ],

                  // 3. General Error Banner
                  if (state.generalError != null && !state.hasResults) ...[
                    Card(
                      color: AppColors.criticalBg,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: const BorderSide(color: AppColors.critical),
                      ),
                      child: Padding(
                        padding: const EdgeInsets.all(16),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Row(
                              children: [
                                Icon(Icons.error_outline, color: AppColors.critical),
                                SizedBox(width: 8),
                                Text(
                                  'Analysis Failed',
                                  style: TextStyle(fontWeight: FontWeight.bold, color: AppColors.critical),
                                ),
                              ],
                            ),
                            const SizedBox(height: 8),
                            Text(
                              state.generalError!,
                              style: const TextStyle(fontSize: 13),
                            ),
                          ],
                        ),
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // 4. Verification Summary & Context Header
                  if (state.snapshot != null) ...[
                    _buildSnapshotSummary(context, state),
                    const SizedBox(height: 16),
                  ],

                  // 5. Laboratory Reference Findings Card (Phase 6)
                  ReferenceFindingsCard(
                    response: state.referenceAnalysis,
                    errorMessage: state.referenceError,
                  ),
                  const SizedBox(height: 16),

                  // 6. ML Risk Assessment Section (Phase 7)
                  const Text(
                    'Statistical Disease Risk Indicators',
                    style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Multivariate research models estimating continuous probability from patient profile.',
                    style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 10),

                  MLRiskCard(
                    title: 'Diabetes Risk Model',
                    conditionName: 'diabetes',
                    response: state.diabetesRisk,
                    errorMessage: state.diabetesError,
                  ),
                  const SizedBox(height: 10),

                  MLRiskCard(
                    title: 'Heart Disease Risk Model',
                    conditionName: 'heart disease',
                    response: state.heartRisk,
                    errorMessage: state.heartError,
                  ),
                  const SizedBox(height: 10),

                  MLRiskCard(
                    title: 'Chronic Kidney Disease Model',
                    conditionName: 'kidney disease',
                    response: state.kidneyRisk,
                    errorMessage: state.kidneyError,
                  ),
                  const SizedBox(height: 16),

                  // 7. Educational AI Explanation Card (Phase 8)
                  GenAIExplanationCard(
                    response: state.genAiExplanation,
                    errorMessage: state.genAiError,
                    isLoading: state.isGenAiLoading,
                    selectedLanguage: state.selectedLanguage,
                    onRetry: () => context.read<AnalysisCubit>().retryGenAI(),
                  ),
                  const SizedBox(height: 24),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildSnapshotSummary(BuildContext context, AnalysisState state) {
    final snap = state.snapshot!;
    final ctx = snap.patientContext;

    return Card(
      elevation: 0,
      color: const Color(0xFFF8FAFC),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Row(
              children: [
                const Icon(Icons.verified, color: AppColors.normal, size: 18),
                const SizedBox(width: 6),
                Text(
                  '${snap.measurementCount} Verified Tests',
                  style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
              ],
            ),
            Row(
              children: [
                Text(
                  'Age: ${ctx.age != null ? "${ctx.age!.toStringAsFixed(0)}y" : "—"}',
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
                const SizedBox(width: 8),
                Text(
                  'Sex: ${ctx.sex ?? "—"}',
                  style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
