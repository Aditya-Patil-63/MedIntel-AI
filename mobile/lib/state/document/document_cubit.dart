import 'dart:io';
import 'package:file_picker/file_picker.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import 'document_state.dart';

/// Enforces file constraints and coordinates document extraction.
class DocumentCubit extends Cubit<DocumentState> {
  final ApiService apiService;

  static const int maxFileSizeBytes = 10 * 1024 * 1024; // 10 MB
  static const Set<String> allowedExtensions = {'pdf', 'png', 'jpg', 'jpeg'};

  DocumentCubit({required this.apiService}) : super(const DocumentInitial());

  /// Validates file extension and size before calling backend.
  String? validateFileAttributes(String filePath, int sizeBytes) {
    final dotIndex = filePath.lastIndexOf('.');
    if (dotIndex == -1) {
      return 'File has no extension. Please select a valid PDF or image file.';
    }

    final ext = filePath.substring(dotIndex + 1).toLowerCase();
    if (!allowedExtensions.contains(ext)) {
      return 'Unsupported file format (.$ext). Only PDF, PNG, and JPG files are supported.';
    }

    if (sizeBytes > maxFileSizeBytes) {
      final sizeMb = (sizeBytes / (1024 * 1024)).toStringAsFixed(1);
      return 'File size ($sizeMb MB) exceeds the 10 MB limit. Please select a smaller file.';
    }

    if (sizeBytes == 0) {
      return 'Selected file is empty (0 bytes).';
    }

    return null;
  }

  /// Triggers file selection via FilePicker, performs client validation, and uploads.
  Future<void> pickAndProcessDocument() async {
    emit(const DocumentSelecting());

    try {
      final pickerResult = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: allowedExtensions.toList(),
      );

      if (pickerResult == null || pickerResult.files.isEmpty) {
        emit(const DocumentInitial());
        return;
      }

      final file = pickerResult.files.single;
      final path = file.path;
      final filename = file.name;

      if (path == null) {
        emit(const DocumentValidationFailed(
          message: 'Unable to access the selected file path.',
        ));
        return;
      }

      emit(DocumentValidating(filename));

      final ioFile = File(path);
      final size = ioFile.existsSync() ? ioFile.lengthSync() : file.size;

      final validationError = validateFileAttributes(path, size);
      if (validationError != null) {
        emit(DocumentValidationFailed(
          message: validationError,
          filename: filename,
          fileSizeBytes: size,
        ));
        return;
      }

      await uploadAndExtract(path, filename: filename);
    } catch (e) {
      emit(DocumentError(message: 'File selection error: ${e.toString()}'));
    }
  }

  /// Directly upload a validated file path.
  Future<void> uploadAndExtract(
    String filePath, {
    String? filename,
    String? engine,
  }) async {
    final name = filename ?? filePath.split(Platform.pathSeparator).last;

    emit(DocumentUploading(filename: name, progress: 0.5));
    emit(DocumentExtracting(filename: name));

    try {
      final result =
          await apiService.extractDocument(filePath, engine: engine);
      emit(DocumentExtracted(result: result, filePath: filePath));
    } catch (e) {
      emit(DocumentError(
        message: e.toString().replaceFirst('ApiException: ', ''),
        lastFilePath: filePath,
      ));
    }
  }

  /// Alias for uploadAndExtract for compatibility.
  Future<void> extractDocument(
    String filePath, {
    String? filename,
    String? engine,
  }) =>
      uploadAndExtract(filePath, filename: filename, engine: engine);

  /// Retry last failed document extraction.
  Future<void> retryLastExtraction() async {
    final currentState = state;
    if (currentState is DocumentError && currentState.lastFilePath != null) {
      await uploadAndExtract(currentState.lastFilePath!);
    }
  }

  void reset() => emit(const DocumentInitial());
}
