import 'package:equatable/equatable.dart';
import '../../models/genai/genai_explain_response.dart';
import '../../models/ml_risk/risk_prediction_response.dart';
import '../../models/reference/batch_analysis.dart';

abstract class AnalysisState extends Equatable {
  const AnalysisState();

  @override
  List<Object?> get props => [];
}

class AnalysisInitial extends AnalysisState {
  const AnalysisInitial();
}

class AnalysisLoading extends AnalysisState {
  final String stage;
  const AnalysisLoading(this.stage);

  @override
  List<Object?> get props => [stage];
}

class AnalysisSuccess extends AnalysisState {
  final BatchAnalysisResponse? referenceAnalysis;
  final List<RiskPredictionResponse> mlRisks;
  final GenAIExplainResponse? genAiExplanation;

  const AnalysisSuccess({
    this.referenceAnalysis,
    this.mlRisks = const [],
    this.genAiExplanation,
  });

  @override
  List<Object?> get props => [referenceAnalysis, mlRisks, genAiExplanation];
}

class AnalysisError extends AnalysisState {
  final String message;
  const AnalysisError(this.message);

  @override
  List<Object?> get props => [message];
}
