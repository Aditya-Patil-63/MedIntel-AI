import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../core/theme/app_colors.dart';
import '../models/common/enums.dart';
import '../models/genai/genai_explain_response.dart';
import '../state/analysis/analysis_cubit.dart';

/// Card rendering patient-friendly educational explanation and multilingual translation.
class GenAIExplanationCard extends StatelessWidget {
  final GenAIExplainResponse? response;
  final String? errorMessage;
  final bool isLoading;
  final SupportedLanguage selectedLanguage;
  final VoidCallback? onRetry;

  const GenAIExplanationCard({
    super.key,
    this.response,
    this.errorMessage,
    this.isLoading = false,
    this.selectedLanguage = SupportedLanguage.english,
    this.onRetry,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.primaryLight, width: 1.2),
      ),
      child: Padding(
        padding: const EdgeInsets.all(18),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Header with title and language selector
            Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(7),
                  decoration: BoxDecoration(
                    color: AppColors.primarySurface,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: const Icon(
                    Icons.auto_awesome_rounded,
                    color: AppColors.primary,
                    size: 18,
                  ),
                ),
                const SizedBox(width: 10),
                const Expanded(
                  child: Text(
                    'Educational AI Explanation',
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
                _buildLanguageSelector(context),
              ],
            ),
            const SizedBox(height: 6),
            const Text(
              'Synthesized from verified lab results and ML indicators.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
            ),
            const Divider(height: 24),
            _buildBody(context),
          ],
        ),
      ),
    );
  }

  Widget _buildLanguageSelector(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.primaryLight.withValues(alpha: 0.5)),
      ),
      child: DropdownButtonHideUnderline(
        child: DropdownButton<SupportedLanguage>(
          value: selectedLanguage,
          isDense: true,
          icon: const Icon(Icons.arrow_drop_down,
              size: 18, color: AppColors.primary),
          items: const [
            DropdownMenuItem(
              value: SupportedLanguage.english,
              child: Text('English',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            ),
            DropdownMenuItem(
              value: SupportedLanguage.hindi,
              child: Text('हिंदी (Hindi)',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            ),
            DropdownMenuItem(
              value: SupportedLanguage.marathi,
              child: Text('मराठी (Marathi)',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            ),
            DropdownMenuItem(
              value: SupportedLanguage.gujarati,
              child: Text('ગુજરાતી (Gujarati)',
                  style: TextStyle(fontSize: 12, fontWeight: FontWeight.w600)),
            ),
          ],
          onChanged: isLoading
              ? null
              : (newLang) {
                  if (newLang != null) {
                    context.read<AnalysisCubit>().changeLanguage(newLang);
                  }
                },
        ),
      ),
    );
  }

  Widget _buildBody(BuildContext context) {
    if (isLoading) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 24),
        child: Center(
          child: Column(
            children: [
              SizedBox(
                width: 28,
                height: 28,
                child: CircularProgressIndicator(
                  strokeWidth: 2.5,
                  color: AppColors.primary,
                ),
              ),
              SizedBox(height: 12),
              Text(
                'Generating clinical explanation...',
                style:
                    TextStyle(fontSize: 13, color: AppColors.textSecondary),
              ),
            ],
          ),
        ),
      );
    }

    if (errorMessage != null) {
      return Container(
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          color: AppColors.highBg,
          borderRadius: BorderRadius.circular(10),
          border: Border.all(color: AppColors.highBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.info_outline, size: 18, color: AppColors.high),
                SizedBox(width: 8),
                Text(
                  'Explanation Temporarily Unavailable',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 13,
                    color: AppColors.high,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              errorMessage!,
              style:
                  const TextStyle(fontSize: 12, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 12),
            ElevatedButton.icon(
              icon: const Icon(Icons.refresh, size: 16),
              label: const Text('Retry AI Explanation',
                  style: TextStyle(fontSize: 12)),
              onPressed: onRetry,
            ),
          ],
        ),
      );
    }

    if (response == null || response!.explanation == null) {
      return const Text(
        'No explanation generated yet.',
        style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
      );
    }

    final exp = response!.explanation!;
    final summaryText = response!.translatedSummary ?? exp.summary;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Summary block
        Text(
          summaryText,
          style: const TextStyle(
            fontSize: 13,
            height: 1.5,
            color: AppColors.textPrimary,
          ),
        ),
        if (exp.findings.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text(
            'Test Insights:',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 13,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          ...exp.findings.map(
            (f) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• ',
                      style: TextStyle(
                          fontWeight: FontWeight.bold,
                          color: AppColors.primary)),
                  Expanded(
                    child: RichText(
                      text: TextSpan(
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textPrimary,
                          height: 1.4,
                        ),
                        children: [
                          TextSpan(
                            text:
                                '${f.analyteName} (${f.observedValue ?? ""}): ',
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          TextSpan(text: f.plainLanguageMeaning),
                        ],
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
        if (exp.recommendedQuestionsForDoctor.isNotEmpty) ...[
          const SizedBox(height: 16),
          const Text(
            'Recommended Questions for Your Doctor:',
            style: TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 13,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          ...exp.recommendedQuestionsForDoctor.map(
            (q) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.help_outline,
                      size: 16, color: AppColors.primary),
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      q,
                      style: const TextStyle(
                        fontSize: 12,
                        color: AppColors.textPrimary,
                        height: 1.35,
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ],
    );
  }
}
