import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/history/analysis_history_item.dart';
import '../../models/common/enums.dart';
import '../../state/analysis/analysis_cubit.dart';
import '../../state/analysis/analysis_state.dart';
import '../../state/document/document_cubit.dart';
import '../../state/document/document_state.dart';
import '../../state/history/history_cubit.dart';
import '../../state/verification/verification_cubit.dart';
import '../../widgets/disclaimer_banner.dart';
import '../../widgets/genai_explanation_card.dart';
import '../../widgets/ml_risk_card.dart';
import '../../widgets/reference_findings_card.dart';

/// Redesigned clinical results dashboard combining deterministic laboratory
/// findings, statistical ML disease risk predictions, and multilingual GenAI explanations.
class ResultsScreen extends StatefulWidget {
  const ResultsScreen({super.key});

  @override
  State<ResultsScreen> createState() => _ResultsScreenState();
}

class _ResultsScreenState extends State<ResultsScreen> {
  String? _savedHistoryId;

  void _saveToHistory(BuildContext context, AnalysisState state) {
    if (state.snapshot == null || state.isGenAiLoading) return;

    String docName = 'Medical Report';
    final docState = context.read<DocumentCubit>().state;
    if (docState is DocumentExtracted) {
      final fileName = docState.filePath.split(Platform.pathSeparator).last;
      if (fileName.trim().isNotEmpty) {
        docName = fileName;
      }
    }

    final historyId = 'hist_${DateTime.now().millisecondsSinceEpoch}';
    final historyItem = AnalysisHistoryItem.fromAnalysisState(
      id: historyId,
      createdAt: DateTime.now(),
      documentName: docName,
      state: state,
    );

    context.read<HistoryCubit>().addRecord(historyItem);

    setState(() {
      _savedHistoryId = historyId;
    });

    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('Analysis saved to local session history.'),
        duration: Duration(seconds: 2),
      ),
    );
  }

  void _startNewAnalysis(BuildContext context) {
    context.read<AnalysisCubit>().reset();
    context.read<DocumentCubit>().reset();
    context.read<VerificationCubit>().reset();
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Analysis & Risk Assessment'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
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
                  // 1. Mandatory Educational Disclaimer Banner
                  const DisclaimerBanner(),
                  const SizedBox(height: 14),

                  // 2. 3-Step Guided Progress Tracker
                  _buildStepTracker(currentStep: 3),
                  const SizedBox(height: 16),

                  // 3. Loading State Indicator
                  if (state.isLoading) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.primarySurface,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(
                            color: AppColors.primary.withValues(alpha: 0.3)),
                      ),
                      child: Row(
                        children: [
                          const SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2.5,
                              color: AppColors.primary,
                            ),
                          ),
                          const SizedBox(width: 14),
                          Expanded(
                            child: Text(
                              state.loadingStage ??
                                  'Analyzing clinical measurements...',
                              style: const TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.bold,
                                color: AppColors.primaryDark,
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),
                  ],

                  // 4. General Error Banner
                  if (state.generalError != null && !state.hasResults) ...[
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(16),
                      decoration: BoxDecoration(
                        color: AppColors.criticalBg,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: AppColors.criticalBorder),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.error_outline,
                                  color: AppColors.critical),
                              SizedBox(width: 8),
                              Text(
                                'Analysis Failed',
                                style: TextStyle(
                                  fontWeight: FontWeight.bold,
                                  color: AppColors.critical,
                                  fontSize: 15,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 8),
                          Text(
                            state.generalError!,
                            style: const TextStyle(
                              fontSize: 13,
                              color: AppColors.textPrimary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 16),
                  ],

                  // 5. Clinical Results Overview Card
                  _buildResultsOverviewCard(state),
                  const SizedBox(height: 16),

                  // 6. Laboratory Reference Findings Card (Phase 6)
                  ReferenceFindingsCard(
                    response: state.referenceAnalysis,
                    errorMessage: state.referenceError,
                  ),
                  const SizedBox(height: 16),

                  // 7. Statistical Disease Risk Indicators Section (Phase 7)
                  const Text(
                    'Statistical Disease Risk Indicators',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                      letterSpacing: -0.3,
                    ),
                  ),
                  const SizedBox(height: 4),
                  const Text(
                    'Statistical multivariate models estimating continuous probability from patient profile.',
                    style: TextStyle(
                        fontSize: 12, color: AppColors.textSecondary),
                  ),
                  const SizedBox(height: 12),

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

                  // 8. Educational AI Explanation Card (Phase 8)
                  GenAIExplanationCard(
                    response: state.genAiExplanation,
                    errorMessage: state.genAiError,
                    isLoading: state.isGenAiLoading,
                    selectedLanguage: state.selectedLanguage,
                    onRetry: () => context.read<AnalysisCubit>().retryGenAI(),
                  ),
                  const SizedBox(height: 20),

                  // 9. Bottom Actions: Save to History & Start New Analysis
                  _buildBottomActions(context, state),
                  const SizedBox(height: 24),
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildStepTracker({required int currentStep}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: const Row(
        children: [
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.check_circle, size: 18, color: AppColors.normal),
              SizedBox(width: 6),
              Text(
                'Upload',
                style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppColors.normal),
              ),
            ],
          ),
          Expanded(
            child: Divider(
                color: AppColors.normal, thickness: 2, indent: 8, endIndent: 8),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.check_circle, size: 18, color: AppColors.normal),
              SizedBox(width: 6),
              Text(
                'Verified',
                style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppColors.normal),
              ),
            ],
          ),
          Expanded(
            child: Divider(
                color: AppColors.normal, thickness: 2, indent: 8, endIndent: 8),
          ),
          Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(Icons.insights, size: 18, color: AppColors.primary),
              SizedBox(width: 6),
              Text(
                'Results',
                style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primaryDark),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildResultsOverviewCard(AnalysisState state) {
    int totalCount = state.snapshot?.measurements.length ?? 0;
    int normalCount = 0;
    int attentionCount = 0;

    if (state.referenceAnalysis != null) {
      for (final r in state.referenceAnalysis!.results) {
        if (r.classification == AnalyteClassification.normal) {
          normalCount++;
        } else if (r.classification != null) {
          attentionCount++;
        }
      }
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
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
                  Icons.assessment_outlined,
                  color: AppColors.primary,
                  size: 20,
                ),
              ),
              const SizedBox(width: 10),
              const Expanded(
                child: Text(
                  'Clinical Summary Overview',
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                    letterSpacing: -0.3,
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 14),
          Row(
            children: [
              Expanded(
                child: _buildMetricPill(
                  label: 'Analyzed',
                  value: '$totalCount',
                  bg: const Color(0xFFF1F5F9),
                  fg: AppColors.textPrimary,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildMetricPill(
                  label: 'In Range',
                  value: '$normalCount',
                  bg: AppColors.normalBg,
                  fg: AppColors.normal,
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: _buildMetricPill(
                  label: 'Outside Range',
                  value: '$attentionCount',
                  bg: attentionCount > 0
                      ? AppColors.highBg
                      : const Color(0xFFF1F5F9),
                  fg: attentionCount > 0
                      ? AppColors.high
                      : AppColors.textSecondary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          Text(
            attentionCount > 0
                ? '$attentionCount measurement${attentionCount > 1 ? "s are" : " is"} outside standard reference intervals. Consult your healthcare professional to discuss these findings.'
                : 'All evaluated measurements are within standard reference intervals.',
            style: const TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildMetricPill({
    required String label,
    required String value,
    required Color bg,
    required Color fg,
  }) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 10, horizontal: 12),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Column(
        children: [
          Text(
            value,
            style: TextStyle(
              fontSize: 18,
              fontWeight: FontWeight.bold,
              color: fg,
            ),
          ),
          const SizedBox(height: 2),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildBottomActions(BuildContext context, AnalysisState state) {
    final isSaved = _savedHistoryId != null;
    final canSave = state.status == AnalysisStatus.success &&
        state.snapshot != null &&
        !state.isGenAiLoading &&
        state.hasResults;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: [
          SizedBox(
            width: double.infinity,
            height: 48,
            child: ElevatedButton.icon(
              icon: Icon(
                isSaved
                    ? Icons.check_circle_rounded
                    : Icons.bookmark_add_outlined,
              ),
              label: Text(
                isSaved
                    ? 'Saved to History'
                    : (state.isGenAiLoading
                        ? 'Generating AI Explanation...'
                        : 'Save to History'),
                style: const TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                ),
              ),
              style: ElevatedButton.styleFrom(
                backgroundColor:
                    isSaved ? AppColors.normal : AppColors.primary,
              ),
              onPressed: (canSave && !isSaved)
                  ? () => _saveToHistory(context, state)
                  : null,
            ),
          ),
          const SizedBox(height: 10),
          SizedBox(
            width: double.infinity,
            height: 48,
            child: OutlinedButton.icon(
              icon: const Icon(Icons.add_circle_outline_rounded),
              label: const Text(
                'Start New Analysis',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
              ),
              onPressed: () => _startNewAnalysis(context),
            ),
          ),
          if (isSaved) ...[
            const SizedBox(height: 10),
            const Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.check, size: 14, color: AppColors.normal),
                SizedBox(width: 6),
                Text(
                  'Saved in local session history. Accessible in History tab.',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.normal,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ),
          ],
        ],
      ),
    );
  }
}
