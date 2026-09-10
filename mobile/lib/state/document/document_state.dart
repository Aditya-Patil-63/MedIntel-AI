import 'package:equatable/equatable.dart';
import '../../models/extraction/document_extraction_result.dart';

/// Explicit lifecycle states for document ingestion and OCR extraction.
abstract class DocumentState extends Equatable {
  const DocumentState();

  @override
  List<Object?> get props => [];
}

class DocumentInitial extends DocumentState {
  const DocumentInitial();
}

class DocumentSelecting extends DocumentState {
  const DocumentSelecting();
}

class DocumentValidating extends DocumentState {
  final String filename;
  const DocumentValidating(this.filename);

  @override
  List<Object?> get props => [filename];
}

class DocumentValidationFailed extends DocumentState {
  final String message;
  final String? filename;
  final int? fileSizeBytes;

  const DocumentValidationFailed({
    required this.message,
    this.filename,
    this.fileSizeBytes,
  });

  @override
  List<Object?> get props => [message, filename, fileSizeBytes];
}

class DocumentUploading extends DocumentState {
  final String filename;
  final double progress;

  const DocumentUploading({
    required this.filename,
    this.progress = 0.0,
  });

  @override
  List<Object?> get props => [filename, progress];
}

class DocumentLoading extends DocumentState {
  final String? message;
  const DocumentLoading({this.message});

  @override
  List<Object?> get props => [message];
}

class DocumentExtracting extends DocumentLoading {
  final String filename;

  const DocumentExtracting({required this.filename})
      : super(message: 'Extracting text with FastAPI OCR pipeline...');

  @override
  List<Object?> get props => [filename, message];
}

class DocumentExtracted extends DocumentState {
  final DocumentExtractionResult result;
  final String filePath;

  const DocumentExtracted({
    required this.result,
    required this.filePath,
  });

  @override
  List<Object?> get props => [result, filePath];
}

class DocumentError extends DocumentState {
  final String message;
  final String? lastFilePath;

  const DocumentError({
    required this.message,
    this.lastFilePath,
  });

  @override
  List<Object?> get props => [message, lastFilePath];
}
