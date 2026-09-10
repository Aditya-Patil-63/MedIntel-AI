import 'package:equatable/equatable.dart';
import '../../models/extraction/document_extraction_result.dart';

abstract class DocumentState extends Equatable {
  const DocumentState();

  @override
  List<Object?> get props => [];
}

class DocumentInitial extends DocumentState {
  const DocumentInitial();
}

class DocumentLoading extends DocumentState {
  final String? message;
  const DocumentLoading({this.message});

  @override
  List<Object?> get props => [message];
}

class DocumentExtracted extends DocumentState {
  final DocumentExtractionResult result;
  const DocumentExtracted(this.result);

  @override
  List<Object?> get props => [result];
}

class DocumentError extends DocumentState {
  final String message;
  const DocumentError(this.message);

  @override
  List<Object?> get props => [message];
}
