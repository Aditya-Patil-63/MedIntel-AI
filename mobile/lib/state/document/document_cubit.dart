import 'package:flutter_bloc/flutter_bloc.dart';
import '../../services/api_service.dart';
import 'document_state.dart';

class DocumentCubit extends Cubit<DocumentState> {
  final ApiService apiService;

  DocumentCubit({required this.apiService})
      : super(const DocumentInitial());

  Future<void> extractDocument(String filePath, {String? engine}) async {
    emit(const DocumentLoading(message: 'Extracting medical document...'));
    try {
      final result =
          await apiService.extractDocument(filePath, engine: engine);
      emit(DocumentExtracted(result));
    } catch (e) {
      emit(DocumentError(e.toString()));
    }
  }

  void reset() => emit(const DocumentInitial());
}
