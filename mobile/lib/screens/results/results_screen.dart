import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/history/analysis_history_item.dart';
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

/// Comprehensive clinical analysis results dashboard rendering Phase 6 deterministic
/// reference findings, Phase 7 ML risk estimation, and Phase 8 GenAI explanations.
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
    // 1. Clear current analysis state
    context.read<AnalysisCubit>().reset();
    // 2. Clear current document/extraction state
    context.read<DocumentCubit>().reset();
    // 3. Clear verification state
    context.read<VerificationCubit>().reset();
    // 4. Return to home
    Navigator.of(context).popUntil((route) => route.isFirst);
  }

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
                                state.loadingStage ??
                                    'Analyzing clinical measurements...',
                                style: const TextStyle(
                                    fontSize: 13, fontWeight: FontWeight.w600),
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
                                Icon(Icons.error_outline,
                                    color: AppColors.critical),
                                SizedBox(width: 8),
                                Text(
                                  'Analysis Failed',
                                  style: TextStyle(
                                      fontWeight: FontWeight.bold,
                                      color: AppColors.critical),
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
                    style:
                        TextStyle(fontSize: 12, color: AppColors.textSecondary),
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
                  const SizedBox(height: 16),

                  // 8. Bottom Action Bar: Save to History & Start New Analysis
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

  Widget _buildBottomActions(BuildContext context, AnalysisState state) {
    final isSaved = _savedHistoryId != null;
    final canSave = state.status == AnalysisStatus.success &&
        state.snapshot != null &&
        !state.isGenAiLoading &&
        state.hasResults;

    return Card(
      elevation: 0,
      color: const Color(0xFFF8FAFC),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          children: [
            Row(
              children: [
                Expanded(
                  child: ElevatedButton.icon(
                    icon: Icon(isSaved
                        ? Icons.check_circle
                        : Icons.bookmark_add_outlined),
                    label: Text(
                      isSaved
                          ? 'Saved to History'
                          : (state.isGenAiLoading
                              ? 'Generating AI...'
                              : 'Save to History'),
                      style: const TextStyle(fontWeight: FontWeight.bold),
                    ),
                    style: ElevatedButton.styleFrom(
                      backgroundColor:
                          isSaved ? AppColors.normal : AppColors.primary,
                      padding: const EdgeInsets.symmetric(vertical: 12),
                    ),
                    onPressed: (canSave && !isSaved)
                        ? () => _saveToHistory(context, state)
                        : null,
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: OutlinedButton.icon(
                    icon: const Icon(Icons.add_circle_outline),
                    label: const Text(
                      'Start New Analysis',
                      style: TextStyle(fontWeight: FontWeight.bold),
                    ),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 12),
                      foregroundColor: AppColors.primary,
                      side: const BorderSide(color: AppColors.primary),
                    ),
                    onPressed: () => _startNewAnalysis(context),
                  ),
                ),
              ],
            ),
            if (isSaved) ...[
              const SizedBox(height: 8),
              const Text(
                'Snapshot recorded in local session history. View in Report History tab.',
                style: TextStyle(
                    fontSize: 11,
                    color: AppColors.normal,
                    fontWeight: FontWeight.w500),
              ),
            ],
          ],
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
                  style:
                      const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
                ),
              ],
            ),
            Row(
              children: [
                Text(
                  'Age: ${ctx.age != null ? "${ctx.age!.toStringAsFixed(0)}y" : "—"}',
                  style: const TextStyle(
                      fontSize: 12, color: AppColors.textSecondary),
                ),
                const SizedBox(width: 8),
                Text(
                  'Sex: ${ctx.sex ?? "—"}',
                  style: const TextStyle(
                      fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
