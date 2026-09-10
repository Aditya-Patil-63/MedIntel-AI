import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../state/document/document_cubit.dart';
import '../../state/document/document_state.dart';
import '../../state/verification/verification_cubit.dart';
import '../../widgets/disclaimer_banner.dart';
import '../verification/verification_screen.dart';

/// Screen managing file selection, client-side validation, and OCR extraction.
class UploadScreen extends StatelessWidget {
  const UploadScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Upload Medical Report'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Reset',
            onPressed: () => context.read<DocumentCubit>().reset(),
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Mandatory Educational Disclaimer Banner
              const DisclaimerBanner(),
              const SizedBox(height: 16),

              // 2. Format & Size Constraints Card
              Card(
                elevation: 0,
                color: const Color(0xFFF1F5F9),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                  side: const BorderSide(color: AppColors.divider),
                ),
                child: const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  child: Row(
                    children: [
                      Icon(Icons.info_outline, size: 20, color: AppColors.textSecondary),
                      SizedBox(width: 10),
                      Expanded(
                        child: Text(
                          'Supported: PDF, PNG, JPG, JPEG • Maximum file size: 10 MB',
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w500,
                            color: AppColors.textSecondary,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),

              // 3. Dynamic State View
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
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildPickerState(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 32),
        child: Column(
          children: [
            Container(
              padding: const EdgeInsets.all(24),
              decoration: BoxDecoration(
                color: AppColors.primary.withValues(alpha: 0.1),
                shape: BoxShape.circle,
              ),
              child: const Icon(
                Icons.upload_file,
                size: 64,
                color: AppColors.primary,
              ),
            ),
            const SizedBox(height: 20),
            const Text(
              'Select Medical Report',
              style: TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const SizedBox(height: 8),
            const Text(
              'Choose a lab report or prescription to extract text',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textSecondary, fontSize: 13),
            ),
            const SizedBox(height: 24),
            ElevatedButton.icon(
              icon: const Icon(Icons.folder_open),
              label: const Text('Browse Files'),
              style: ElevatedButton.styleFrom(
                minimumSize: const Size(200, 48),
              ),
              onPressed: () =>
                  context.read<DocumentCubit>().pickAndProcessDocument(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildProcessingState(DocumentState state) {
    String message = 'Processing document...';
    if (state is DocumentSelecting) message = 'Selecting file...';
    if (state is DocumentValidating) message = 'Validating file constraints...';
    if (state is DocumentUploading) {
      message = 'Uploading "${state.filename}" to server...';
    }
    if (state is DocumentExtracting) {
      message = 'Extracting text with FastAPI OCR pipeline...';
    }

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(32),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const CircularProgressIndicator(color: AppColors.primary),
            const SizedBox(height: 20),
            Text(
              message,
              textAlign: TextAlign.center,
              style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 14),
            ),
            const SizedBox(height: 8),
            const Text(
              'Please wait while the document is securely processed',
              textAlign: TextAlign.center,
              style: TextStyle(color: AppColors.textMuted, fontSize: 12),
            ),
          ],
        ),
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
        borderRadius: BorderRadius.circular(12),
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
                  'File Validation Failed',
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
              style: const TextStyle(fontSize: 14, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 20),
            ElevatedButton.icon(
              icon: const Icon(Icons.refresh),
              label: const Text('Select Another File'),
              onPressed: () =>
                  context.read<DocumentCubit>().pickAndProcessDocument(),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildErrorState(BuildContext context, DocumentError state) {
    return Card(
      color: AppColors.criticalBg,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
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
              state.message,
              style: const TextStyle(fontSize: 14, color: AppColors.textPrimary),
            ),
            const SizedBox(height: 20),
            Row(
              children: [
                ElevatedButton.icon(
                  icon: const Icon(Icons.replay),
                  label: const Text('Retry Extraction'),
                  onPressed: () =>
                      context.read<DocumentCubit>().retryLastExtraction(),
                ),
                const SizedBox(width: 12),
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

  Widget _buildExtractedState(BuildContext context, DocumentExtracted state) {
    final result = state.result;

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Card(
          child: Padding(
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    const Icon(Icons.check_circle, color: AppColors.normal, size: 24),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        result.filename,
                        style: const TextStyle(
                          fontSize: 16,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ),
                  ],
                ),
                const Divider(height: 24),
                _buildMetaRow('Source Type', result.sourceType.value),
                _buildMetaRow('Extractor Used', result.extractor),
                _buildMetaRow('Pages Processed', result.totalPages.toString()),
                _buildMetaRow(
                  'OCR Confidence',
                  '${(result.confidence * 100).toStringAsFixed(1)}%',
                ),
                if (result.warnings.isNotEmpty) ...[
                  const SizedBox(height: 8),
                  Text(
                    'Warnings: ${result.warnings.join(", ")}',
                    style: const TextStyle(fontSize: 12, color: AppColors.high),
                  ),
                ],
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        const Text(
          'Extracted Text Preview',
          style: TextStyle(fontWeight: FontWeight.bold, fontSize: 14),
        ),
        const SizedBox(height: 8),
        Container(
          width: double.infinity,
          height: 160,
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(8),
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
              ),
            ),
          ),
        ),
        const SizedBox(height: 24),
        SizedBox(
          width: double.infinity,
          child: ElevatedButton.icon(
            icon: const Icon(Icons.arrow_forward),
            label: const Text('Proceed to Medical Verification'),
            style: ElevatedButton.styleFrom(
              minimumSize: const Size.fromHeight(50),
            ),
            onPressed: () {
              // Initiate reference parse-and-analyze
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
      ],
    );
  }

  Widget _buildMetaRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 3),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: AppColors.textSecondary, fontSize: 13)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13)),
        ],
      ),
    );
  }
}
