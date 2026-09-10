import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../state/document/document_cubit.dart';
import '../../state/document/document_state.dart';
import '../../widgets/disclaimer_banner.dart';

class UploadScreen extends StatelessWidget {
  const UploadScreen({super.key});

  Future<void> _pickAndUpload(BuildContext context) async {
    final result = await FilePicker.platform.pickFiles(
      type: FileType.custom,
      allowedExtensions: ['pdf', 'png', 'jpg', 'jpeg'],
    );

    if (result != null && result.files.single.path != null) {
      if (context.mounted) {
        context
            .read<DocumentCubit>()
            .extractDocument(result.files.single.path!);
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Upload Medical Report')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              const DisclaimerBanner(),
              const SizedBox(height: 24),
              Expanded(
                child: BlocConsumer<DocumentCubit, DocumentState>(
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
                    if (state is DocumentLoading) {
                      return const Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            CircularProgressIndicator(),
                            SizedBox(height: 16),
                            Text('Extracting document with FastAPI backend...'),
                          ],
                        ),
                      );
                    }

                    if (state is DocumentExtracted) {
                      final result = state.result;
                      return SingleChildScrollView(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              'Document Extracted: ${result.filename}',
                              style: const TextStyle(
                                  fontWeight: FontWeight.bold, fontSize: 16),
                            ),
                            Text('Source: ${result.sourceType.value}'),
                            Text('Pages: ${result.totalPages}'),
                            Text(
                                'Confidence: ${(result.confidence * 100).toStringAsFixed(1)}%'),
                            const SizedBox(height: 12),
                            Container(
                              padding: const EdgeInsets.all(12),
                              decoration: BoxDecoration(
                                color: Colors.grey.shade100,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Text(
                                result.fullText.isNotEmpty
                                    ? result.fullText
                                    : 'No text extracted.',
                                maxLines: 10,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          ],
                        ),
                      );
                    }

                    return Center(
                      child: Column(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          const Icon(
                            Icons.upload_file,
                            size: 64,
                            color: AppColors.primary,
                          ),
                          const SizedBox(height: 16),
                          const Text(
                            'Select PDF or Image Report',
                            style: TextStyle(
                              fontSize: 16,
                              fontWeight: FontWeight.bold,
                            ),
                          ),
                          const SizedBox(height: 8),
                          const Text(
                            'Supported formats: PDF, PNG, JPG',
                            style: TextStyle(color: AppColors.textMuted),
                          ),
                          const SizedBox(height: 24),
                          ElevatedButton.icon(
                            icon: const Icon(Icons.folder_open),
                            label: const Text('Browse Files'),
                            onPressed: () => _pickAndUpload(context),
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
