import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../state/analysis/analysis_cubit.dart';
import '../../state/document/document_cubit.dart';
import '../../state/document/document_state.dart';
import '../../state/verification/verification_cubit.dart';
import '../results/results_screen.dart';
import '../verification/verification_screen.dart';

/// Redesigned production-grade document upload and extraction experience.
///
/// Features a step progress indicator, intuitive dropzone area, real-time
/// processing animations, patient-friendly error recovery, and seamless
/// transition into the clinical verification gate.
class UploadScreen extends StatelessWidget {
  const UploadScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Medical Report'),
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. 3-Step Guided Progress Tracker
              _buildStepTracker(currentStep: 1),
              const SizedBox(height: 12),

              // 2. Supported Formats Badge
              Container(
                width: double.infinity,
                padding:
                    const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(10),
                  border: Border.all(color: AppColors.divider),
                ),
                child: const Row(
                  children: [
                    Icon(
                      Icons.check_circle_outline,
                      size: 16,
                      color: AppColors.primary,
                    ),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Supported: PDF, PNG, JPG, JPEG • Maximum file size: 10 MB',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: AppColors.textSecondary,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),

              // 4. Dynamic State Views (Picker / Processing / Extracted / Error)
              BlocConsumer<DocumentCubit, DocumentState>(
                listener: (context, state) {
                  if (state is DocumentError) {
                    ScaffoldMessenger.of(context).showSnackBar(
                      SnackBar(
                        content: Text(state.message),
                        backgroundColor: AppColors.critical,
                      ),
                    );
                  }
                },
                builder: (context, state) {
                  if (state is DocumentSelecting ||
                      state is DocumentValidating ||
                      state is DocumentUploading ||
                      state is DocumentExtracting) {
                    return _buildProcessingState(state);
                  }

                  if (state is DocumentValidationFailed) {
                    return _buildValidationFailedState(context, state);
                  }

                  if (state is DocumentExtracted) {
                    return _buildExtractedState(context, state);
                  }

                  if (state is DocumentError) {
                    return _buildErrorState(context, state);
                  }

                  return _buildPickerState(context);
                },
              ),
              const SizedBox(height: 24),
            ],
          ),
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
      child: Row(
        children: [
          _buildStepNode(
            step: 1,
            label: 'Upload',
            isActive: currentStep == 1,
            isCompleted: currentStep > 1,
          ),
          _buildStepDivider(isCompleted: currentStep > 1),
          _buildStepNode(
            step: 2,
            label: 'Verify',
            isActive: currentStep == 2,
            isCompleted: currentStep > 2,
          ),
          _buildStepDivider(isCompleted: currentStep > 2),
          _buildStepNode(
            step: 3,
            label: 'Results',
            isActive: currentStep == 3,
            isCompleted: false,
          ),
        ],
      ),
    );
  }

  Widget _buildStepNode({
    required int step,
    required String label,
    required bool isActive,
    required bool isCompleted,
  }) {
    Color circleColor = const Color(0xFFF1F5F9);
    Color textColor = AppColors.textSecondary;
    Widget child = Text(
      '$step',
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.bold,
        color: AppColors.textSecondary,
      ),
    );

    if (isCompleted) {
      circleColor = AppColors.normalBg;
      textColor = AppColors.normal;
      child = const Icon(Icons.check, size: 14, color: AppColors.normal);
    } else if (isActive) {
      circleColor = AppColors.primary;
      textColor = AppColors.primaryDark;
      child = Text(
        '$step',
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 22,
          height: 22,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: circleColor,
            shape: BoxShape.circle,
          ),
          child: child,
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isActive ? FontWeight.bold : FontWeight.w500,
            color: textColor,
          ),
        ),
      ],
    );
  }

  Widget _buildStepDivider({required bool isCompleted}) {
    return Expanded(
      child: Container(
        height: 2,
        margin: const EdgeInsets.symmetric(horizontal: 8),
        color: isCompleted ? AppColors.normal : AppColors.divider,
      ),
    );
  }

  Widget _buildPickerState(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(vertical: 36, horizontal: 20),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: AppColors.primary.withValues(alpha: 0.3),
          width: 1.5,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 10,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.upload_file_rounded,
              size: 56,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'Select Medical Report',
            style: TextStyle(
              fontSize: 20,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
              letterSpacing: -0.3,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Upload a medical report to extract and analyze your test results.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 13,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 24),
          ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 280),
            child: SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: const Icon(Icons.folder_open_rounded, size: 20),
                label: const Text('Browse Files'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(12),
                  ),
                ),
                onPressed: () =>
                    context.read<DocumentCubit>().pickAndProcessDocument(),
              ),
            ),
          ),
          const SizedBox(height: 12),
          TextButton.icon(
            icon: const Icon(Icons.edit_note_rounded, size: 18),
            label: const Text(
              "Don't have a report? Enter values manually →",
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: AppColors.primary,
              ),
            ),
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const VerificationScreen()),
              );
            },
          ),
          const SizedBox(height: 12),
          const Text(
            'Next: You will review & confirm extracted values',
            style: TextStyle(
              fontSize: 11,
              color: AppColors.textMuted,
              fontWeight: FontWeight.w500,
            ),
          ),
        ],
      ),
    );
    }

  Widget _buildProcessingState(DocumentState state) {
    String message = 'Processing document...';
    if (state is DocumentSelecting) message = 'Selecting document file...';
    if (state is DocumentValidating) message = 'Validating file constraints...';
    if (state is DocumentUploading) {
      message = 'Uploading "${state.filename}" to server...';
    }
    if (state is DocumentExtracting) {
      message = 'Extracting numerical laboratory measurements...';
    }

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(32),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: [
          const SizedBox(
            width: 48,
            height: 48,
            child: CircularProgressIndicator(
              strokeWidth: 3.5,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(height: 20),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.w600,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 8),
          const Text(
            'Please wait a moment while the clinical parser runs.',
            textAlign: TextAlign.center,
            style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
          ),
        ],
      ),
    );
  }

  Widget _buildValidationFailedState(
    BuildContext context,
    DocumentValidationFailed state,
  ) {
    return Card(
      color: AppColors.criticalBg,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.critical),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.error_outline, color: AppColors.critical),
                SizedBox(width: 8),
                Text(
                  'Invalid File',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: AppColors.critical,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              state.message,
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.textPrimary,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 16),
            ElevatedButton.icon(
              icon: const Icon(Icons.upload_file_outlined),
              label: const Text('Choose Another File'),
              onPressed: () =>
                  context.read<DocumentCubit>().pickAndProcessDocument(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildExtractedState(
      BuildContext context, DocumentExtracted state) {
    final result = state.result;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(18),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: AppColors.normalBorder),
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppColors.normalBg,
                      shape: BoxShape.circle,
                    ),
                    child: const Icon(
                      Icons.check_circle_rounded,
                      color: AppColors.normal,
                      size: 24,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          result.filename,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.bold,
                            color: AppColors.textPrimary,
                          ),
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                        ),
                        Text(
                          '${result.totalPages} pages processed • ${result.sourceType.value}',
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
              if (result.warnings.isNotEmpty) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppColors.highBg,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppColors.highBorder),
                  ),
                  child: Text(
                    result.warnings.join("\n"),
                    style: const TextStyle(
                      fontSize: 11,
                      color: AppColors.high,
                      height: 1.3,
                    ),
                  ),
                ),
              ],
            ],
          ),
        ),
        const SizedBox(height: 16),

        // Text preview card
        const Text(
          'Extracted Text Preview',
          style: TextStyle(
            fontWeight: FontWeight.bold,
            fontSize: 14,
            color: AppColors.textPrimary,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          height: 140,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: AppColors.divider),
          ),
          child: SingleChildScrollView(
            child: Text(
              result.fullText.isNotEmpty
                  ? result.fullText
                  : 'No text extracted from this document.',
              style: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 12,
                height: 1.4,
                color: AppColors.textPrimary,
              ),
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Action Buttons
        SizedBox(
          width: double.infinity,
          height: 50,
          child: ElevatedButton.icon(
            icon: const Icon(Icons.auto_awesome_rounded, size: 20),
            label: const Text(
              'Auto-Analyze Report',
              style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
            ),
            style: ElevatedButton.styleFrom(
              backgroundColor: AppColors.primary,
              foregroundColor: Colors.white,
              elevation: 0,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            onPressed: () async {
              showDialog(
                context: context,
                barrierDismissible: false,
                builder: (ctx) => const Center(
                  child: Card(
                    margin: EdgeInsets.all(24),
                    child: Padding(
                      padding:
                          EdgeInsets.symmetric(horizontal: 24, vertical: 20),
                      child: Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          CircularProgressIndicator(strokeWidth: 3),
                          SizedBox(width: 16),
                          Text(
                            'Analyzing report automatically...',
                            style: TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              color: AppColors.textPrimary,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              );

              try {
                final vCubit = context.read<VerificationCubit>();
                await vCubit.parseExtractedText(result.fullText);
                final snapshot = vCubit.createSnapshot(autoConfirm: true);

                if (context.mounted) {
                  Navigator.of(context, rootNavigator: true).pop();
                  context.read<AnalysisCubit>().runFullAnalysis(snapshot);
                  Navigator.push(
                    context,
                    MaterialPageRoute(
                      builder: (_) => const ResultsScreen(),
                    ),
                  );
                }
              } catch (e) {
                if (context.mounted) {
                  Navigator.of(context, rootNavigator: true).pop();
                  ScaffoldMessenger.of(context).showSnackBar(
                    SnackBar(
                      content: Text('Auto-analysis error: $e'),
                      backgroundColor: AppColors.critical,
                    ),
                  );
                }
              }
            },
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          height: 48,
          child: OutlinedButton.icon(
            icon: const Icon(Icons.tune_rounded, size: 18),
            label: const Text(
              'Review & Verify Measurements',
              style: TextStyle(
                fontSize: 14,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            style: OutlinedButton.styleFrom(
              side: const BorderSide(color: AppColors.divider, width: 1.5),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
            onPressed: () {
              context
                  .read<VerificationCubit>()
                  .parseExtractedText(result.fullText);
              Navigator.push(
                context,
                MaterialPageRoute(
                  builder: (_) => const VerificationScreen(),
                ),
              );
            },
          ),
        ),
        const SizedBox(height: 12),
        SizedBox(
          width: double.infinity,
          child: TextButton.icon(
            icon: const Icon(Icons.refresh_rounded, size: 18),
            label: const Text(
              'Upload a Different Report',
              style: TextStyle(
                fontSize: 13,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
            onPressed: () =>
                context.read<DocumentCubit>().pickAndProcessDocument(),
          ),
        ),
      ],
    );
  }

  Widget _buildErrorState(BuildContext context, DocumentError state) {
    return Card(
      color: AppColors.criticalBg,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
        side: const BorderSide(color: AppColors.criticalBorder),
      ),
      child: Padding(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.error_outline, color: AppColors.critical),
                SizedBox(width: 8),
                Text(
                  'Extraction Error',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    color: AppColors.critical,
                    fontSize: 16,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            Text(
              _formatUserFriendlyError(state.message),
              style: const TextStyle(
                fontSize: 13,
                color: AppColors.textPrimary,
                height: 1.4,
              ),
            ),
            const SizedBox(height: 20),
            Wrap(
              spacing: 10,
              runSpacing: 10,
              children: [
                ElevatedButton(
                  onPressed: () =>
                      context.read<DocumentCubit>().retryLastExtraction(),
                  child: const Text('Retry Extraction'),
                ),
                OutlinedButton(
                  onPressed: () =>
                      context.read<DocumentCubit>().pickAndProcessDocument(),
                  child: const Text('Select Different File'),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  String _formatUserFriendlyError(String rawMessage) {
    if (rawMessage.contains('Unable to connect') ||
        rawMessage.contains('Connection refused') ||
        rawMessage.contains('NETWORK_ERROR')) {
      return 'Unable to reach the MedIntel AI backend server. '
          'Please ensure the backend server is running. You can verify network settings in Settings.';
    }
    if (rawMessage.contains('No extractable text') ||
        rawMessage.contains('empty')) {
      return "We couldn't read the text in this document. Try uploading a clearer PDF or image.";
    }
    return rawMessage;
  }
}
