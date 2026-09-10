import 'package:equatable/equatable.dart';
import '../../models/analysis/verified_snapshot.dart';
import '../../models/common/enums.dart';
import '../../models/genai/genai_explain_response.dart';
import '../../models/ml_risk/risk_prediction_response.dart';
import '../../models/reference/batch_analysis.dart';

enum AnalysisStatus { initial, loading, success, failure }

/// Comprehensive state of multi-stage medical analysis and risk estimation.
class AnalysisState extends Equatable {
  final AnalysisStatus status;
  final String? loadingStage;
  final VerifiedSnapshot? snapshot;

  // Subsystem 1: Reference Analysis
  final BatchAnalysisResponse? referenceAnalysis;
  final String? referenceError;

  // Subsystem 2: Machine Learning Models
  final RiskPredictionResponse? diabetesRisk;
  final String? diabetesError;

  final RiskPredictionResponse? heartRisk;
  final String? heartError;

  final RiskPredictionResponse? kidneyRisk;
  final String? kidneyError;

  // Subsystem 3: GenAI Explanation
  final GenAIExplainResponse? genAiExplanation;
  final String? genAiError;
  final bool isGenAiLoading;

  // Language & Workflow
  final SupportedLanguage selectedLanguage;
  final String? generalError;

  const AnalysisState({
    this.status = AnalysisStatus.initial,
    this.loadingStage,
    this.snapshot,
    this.referenceAnalysis,
    this.referenceError,
    this.diabetesRisk,
    this.diabetesError,
    this.heartRisk,
    this.heartError,
    this.kidneyRisk,
    this.kidneyError,
    this.genAiExplanation,
    this.genAiError,
    this.isGenAiLoading = false,
    this.selectedLanguage = SupportedLanguage.english,
    this.generalError,
  });

  bool get isLoading => status == AnalysisStatus.loading;
  bool get isSuccess => status == AnalysisStatus.success;
  bool get isFailure => status == AnalysisStatus.failure;

  bool get hasResults =>
      referenceAnalysis != null ||
      diabetesRisk != null ||
      heartRisk != null ||
      kidneyRisk != null ||
      genAiExplanation != null;

  AnalysisState copyWith({
    AnalysisStatus? status,
    String? loadingStage,
    VerifiedSnapshot? snapshot,
    BatchAnalysisResponse? referenceAnalysis,
    String? referenceError,
    RiskPredictionResponse? diabetesRisk,
    String? diabetesError,
    RiskPredictionResponse? heartRisk,
    String? heartError,
    RiskPredictionResponse? kidneyRisk,
    String? kidneyError,
    GenAIExplainResponse? genAiExplanation,
    String? genAiError,
    bool? isGenAiLoading,
    SupportedLanguage? selectedLanguage,
    String? generalError,
  }) {
    return AnalysisState(
      status: status ?? this.status,
      loadingStage: loadingStage,
      snapshot: snapshot ?? this.snapshot,
      referenceAnalysis: referenceAnalysis ?? this.referenceAnalysis,
      referenceError: referenceError,
      diabetesRisk: diabetesRisk ?? this.diabetesRisk,
      diabetesError: diabetesError,
      heartRisk: heartRisk ?? this.heartRisk,
      heartError: heartError,
      kidneyRisk: kidneyRisk ?? this.kidneyRisk,
      kidneyError: kidneyError,
      genAiExplanation: genAiExplanation ?? this.genAiExplanation,
      genAiError: genAiError,
      isGenAiLoading: isGenAiLoading ?? this.isGenAiLoading,
      selectedLanguage: selectedLanguage ?? this.selectedLanguage,
      generalError: generalError,
    );
  }

  @override
  List<Object?> get props => [
        status,
        loadingStage,
        snapshot,
        referenceAnalysis,
        referenceError,
        diabetesRisk,
        diabetesError,
        heartRisk,
        heartError,
        kidneyRisk,
        kidneyError,
        genAiExplanation,
        genAiError,
        isGenAiLoading,
        selectedLanguage,
        generalError,
      ];
}
