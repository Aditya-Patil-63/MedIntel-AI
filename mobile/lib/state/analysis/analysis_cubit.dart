import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/errors/api_exception.dart';
import '../../models/analysis/verified_snapshot.dart';
import '../../models/common/enums.dart';
import '../../models/genai/genai_explain_request.dart';
import '../../models/genai/genai_explain_response.dart';
import '../../models/ml_risk/risk_prediction_response.dart';
import '../../models/reference/batch_analysis.dart';
import '../../repositories/medical_repository.dart';
import '../../services/feature_mapper.dart';
import 'analysis_state.dart';

/// Orchestrates multi-stage medical analysis:
/// 1. Evaluates user-verified snapshot against Phase 6 reference intervals.
/// 2. Invokes Phase 7 ML risk estimation for Diabetes, Heart Disease, and Kidney Disease in parallel.
/// 3. Aggregates findings and requests Phase 8 GenAI educational explanation with multilingual support.
class AnalysisCubit extends Cubit<AnalysisState> {
  final MedicalRepository repository;

  AnalysisCubit({required this.repository})
      : super(const AnalysisState());

  static String _formatError(Object e) {
    if (e is ApiException) return e.message;
    return e.toString().replaceFirst('Exception: ', '').replaceFirst('ApiException: ', '');
  }

  static String _formatGenAIError(Object e) {
    if (e is ApiException) {
      if (e.statusCode == 429 || e.message.toLowerCase().contains('rate limit')) {
        return 'AI explanation temporarily unavailable due to provider rate limits. Tap retry to check again.';
      }
      if (e.statusCode == 503 || e.message.toLowerCase().contains('unavailable')) {
        return 'AI explanation service is currently unavailable.';
      }
      if (e.statusCode == 504 || e.message.toLowerCase().contains('timeout')) {
        return 'AI explanation timed out. Please retry.';
      }
      return e.message;
    }
    final msg = e.toString();
    if (msg.contains('429')) {
      return 'AI explanation temporarily unavailable due to provider rate limits. Tap retry to check again.';
    }
    return 'Unable to generate AI explanation. Please check your connection and retry.';
  }

  /// Runs full multi-stage analysis pipeline from an immutable verified snapshot.
  Future<void> runFullAnalysis(VerifiedSnapshot snapshot) async {
    // 1. Mandatory Client Safeguard: Require verification gate confirmation
    if (!snapshot.isVerified) {
      emit(state.copyWith(
        status: AnalysisStatus.failure,
        generalError: 'Client Safeguard: Measurements must be confirmed and verified before analysis.',
      ));
      return;
    }

    if (!snapshot.hasMeasurements) {
      emit(state.copyWith(
        status: AnalysisStatus.failure,
        generalError: 'No verified measurements available to analyze.',
      ));
      return;
    }

    // 2. Set loading state with new snapshot (purges any old stale results)
    emit(AnalysisState(
      status: AnalysisStatus.loading,
      loadingStage: 'Evaluating laboratory reference intervals and disease risk models...',
      snapshot: snapshot,
      selectedLanguage: state.selectedLanguage,
    ));

    // 3. Build parallel requests via pure FeatureMapper
    final refReq = FeatureMapper.toBatchAnalysisRequest(snapshot);
    final diabetesReq = FeatureMapper.toDiabetesRiskRequest(snapshot);
    final heartReq = FeatureMapper.toHeartDiseaseRiskRequest(snapshot);
    final kidneyReq = FeatureMapper.toKidneyDiseaseRiskRequest(snapshot);

    BatchAnalysisResponse? refResult;
    String? refError;

    RiskPredictionResponse? diabetesResult;
    String? diabetesError;

    RiskPredictionResponse? heartResult;
    String? heartError;

    RiskPredictionResponse? kidneyResult;
    String? kidneyError;

    // 4. Parallel execution of independent analytical modules
    // Each request is wrapped in an isolated try-catch so one failure never destroys other results.
    await Future.wait([
      () async {
        try {
          refResult = await repository.analyzeMeasurements(
            measurements: refReq.measurements,
            isUserVerified: true,
          );
        } catch (e) {
          refError = _formatError(e);
        }
      }(),
      () async {
        try {
          diabetesResult = await repository.predictDiabetes(request: diabetesReq);
        } catch (e) {
          diabetesError = _formatError(e);
        }
      }(),
      () async {
        try {
          heartResult = await repository.predictHeartDisease(request: heartReq);
        } catch (e) {
          heartError = _formatError(e);
        }
      }(),
      () async {
        try {
          kidneyResult = await repository.predictKidneyDisease(request: kidneyReq);
        } catch (e) {
          kidneyError = _formatError(e);
        }
      }(),
    ]);

    // 5. Check for complete analytical failure
    if (refResult == null && diabetesResult == null && heartResult == null && kidneyResult == null) {
      emit(AnalysisState(
        status: AnalysisStatus.failure,
        generalError: 'Analysis failed: ${refError ?? "Service unavailable."}',
        snapshot: snapshot,
        referenceError: refError,
        diabetesError: diabetesError,
        heartError: heartError,
        kidneyError: kidneyError,
        selectedLanguage: state.selectedLanguage,
      ));
      return;
    }

    // 6. Transition to GenAI Explanation Stage
    emit(AnalysisState(
      status: AnalysisStatus.loading,
      loadingStage: 'Synthesizing educational explanation in ${state.selectedLanguage.name}...',
      snapshot: snapshot,
      referenceAnalysis: refResult,
      referenceError: refError,
      diabetesRisk: diabetesResult,
      diabetesError: diabetesError,
      heartRisk: heartResult,
      heartError: heartError,
      kidneyRisk: kidneyResult,
      kidneyError: kidneyError,
      selectedLanguage: state.selectedLanguage,
      isGenAiLoading: true,
    ));

    // 7. Map findings to GenAI schema
    final analytes = refResult != null
        ? FeatureMapper.toVerifiedAnalyteSummaries(refResult!)
        : <VerifiedAnalyteSummary>[];

    final mlRisks = FeatureMapper.toMLRiskSummaries([
      if (diabetesResult != null) diabetesResult!,
      if (heartResult != null) heartResult!,
      if (kidneyResult != null) kidneyResult!,
    ]);

    GenAIExplainResponse? genAiResult;
    String? genAiError;

    if (analytes.isNotEmpty || mlRisks.isNotEmpty) {
      try {
        final genAiReq = GenAIExplainRequest(
          isUserVerified: true,
          patientAge: snapshot.patientContext.age,
          patientSex: snapshot.patientContext.sex,
          analytes: analytes,
          mlRisks: mlRisks,
          language: state.selectedLanguage,
          detailLevel: DetailLevel.simple,
        );
        genAiResult = await repository.generateExplanation(request: genAiReq);
      } catch (e) {
        genAiError = _formatGenAIError(e);
      }
    } else {
      genAiError = 'No verified findings available to explain.';
    }

    // 8. Emit final complete/partial success state
    emit(AnalysisState(
      status: AnalysisStatus.success,
      snapshot: snapshot,
      referenceAnalysis: refResult,
      referenceError: refError,
      diabetesRisk: diabetesResult,
      diabetesError: diabetesError,
      heartRisk: heartResult,
      heartError: heartError,
      kidneyRisk: kidneyResult,
      kidneyError: kidneyError,
      genAiExplanation: genAiResult,
      genAiError: genAiError,
      isGenAiLoading: false,
      selectedLanguage: state.selectedLanguage,
    ));
  }

  /// Switches GenAI explanation language without re-running reference or ML analysis.
  Future<void> changeLanguage(SupportedLanguage newLanguage) async {
    if (state.selectedLanguage == newLanguage && state.genAiExplanation != null) return;
    if (state.snapshot == null || !state.snapshot!.isVerified) return;

    emit(state.copyWith(
      selectedLanguage: newLanguage,
      isGenAiLoading: true,
      genAiError: null,
    ));

    final analytes = state.referenceAnalysis != null
        ? FeatureMapper.toVerifiedAnalyteSummaries(state.referenceAnalysis!)
        : <VerifiedAnalyteSummary>[];

    final mlRisks = FeatureMapper.toMLRiskSummaries([
      if (state.diabetesRisk != null) state.diabetesRisk!,
      if (state.heartRisk != null) state.heartRisk!,
      if (state.kidneyRisk != null) state.kidneyRisk!,
    ]);

    if (analytes.isEmpty && mlRisks.isEmpty) {
      emit(state.copyWith(
        isGenAiLoading: false,
        genAiError: 'No verified findings available to translate.',
      ));
      return;
    }

    try {
      final genAiReq = GenAIExplainRequest(
        isUserVerified: true,
        patientAge: state.snapshot!.patientContext.age,
        patientSex: state.snapshot!.patientContext.sex,
        analytes: analytes,
        mlRisks: mlRisks,
        language: newLanguage,
        detailLevel: DetailLevel.simple,
      );
      final genAiResult = await repository.generateExplanation(request: genAiReq);
      emit(state.copyWith(
        genAiExplanation: genAiResult,
        isGenAiLoading: false,
        genAiError: null,
      ));
    } catch (e) {
      emit(state.copyWith(
        isGenAiLoading: false,
        genAiError: _formatGenAIError(e),
      ));
    }
  }

  /// Retries only the GenAI explanation step if previously rate-limited or unavailable.
  Future<void> retryGenAI() async {
    if (state.snapshot == null || !state.snapshot!.isVerified) return;
    await changeLanguage(state.selectedLanguage);
  }

  /// Purges active analysis state when underlying verification is invalidated.
  void invalidate() => emit(const AnalysisState());

  void reset() => emit(const AnalysisState());
}
