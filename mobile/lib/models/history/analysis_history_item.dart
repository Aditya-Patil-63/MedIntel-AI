import 'package:equatable/equatable.dart';
import '../common/enums.dart';
import '../genai/genai_explain_response.dart';
import '../ml_risk/risk_prediction_response.dart';
import '../reference/analysis_result.dart';
import '../../state/analysis/analysis_state.dart';

/// Strongly typed, immutable snapshot representing a completed clinical analysis run.
///
/// Captures the verified findings, deterministic reference evaluations, ML risk predictions,
/// and educational GenAI explanations exactly as they existed upon completion.
class AnalysisHistoryItem extends Equatable {
  final String id;
  final DateTime createdAt;
  final String documentName;
  final int verifiedMeasurementCount;
  final double? patientAge;
  final String? patientSex;
  final List<AnalysisResult> referenceResults;
  final int totalClassified;
  final RiskPredictionResponse? diabetesRisk;
  final RiskPredictionResponse? heartRisk;
  final RiskPredictionResponse? kidneyRisk;
  final GenAIExplainResponse? genAiExplanation;
  final SupportedLanguage selectedLanguage;
  final String disclaimer;

  AnalysisHistoryItem({
    required this.id,
    required this.createdAt,
    required this.documentName,
    required this.verifiedMeasurementCount,
    this.patientAge,
    this.patientSex,
    required List<AnalysisResult> referenceResults,
    required this.totalClassified,
    this.diabetesRisk,
    this.heartRisk,
    this.kidneyRisk,
    this.genAiExplanation,
    this.selectedLanguage = SupportedLanguage.english,
    this.disclaimer =
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
  }) : referenceResults = List<AnalysisResult>.unmodifiable(referenceResults);

  /// Factory constructor taking an existing AnalysisState and capturing an immutable snapshot.
  factory AnalysisHistoryItem.fromAnalysisState({
    required String id,
    required DateTime createdAt,
    required String documentName,
    required AnalysisState state,
  }) {
    final snap = state.snapshot;
    final results = state.referenceAnalysis?.results ?? const <AnalysisResult>[];

    return AnalysisHistoryItem(
      id: id,
      createdAt: createdAt,
      documentName: documentName,
      verifiedMeasurementCount: snap?.measurementCount ?? results.length,
      patientAge: snap?.patientContext.age,
      patientSex: snap?.patientContext.sex,
      referenceResults: List<AnalysisResult>.unmodifiable(results),
      totalClassified: state.referenceAnalysis?.totalClassified ?? results.length,
      diabetesRisk: state.diabetesRisk,
      heartRisk: state.heartRisk,
      kidneyRisk: state.kidneyRisk,
      genAiExplanation: state.genAiExplanation,
      selectedLanguage: state.selectedLanguage,
    );
  }

  // --- Convenience Summary Getters ---

  int get lowCount => referenceResults
      .where((r) => r.classification == AnalyteClassification.low)
      .length;

  int get normalCount => referenceResults
      .where((r) => r.classification == AnalyteClassification.normal)
      .length;

  int get highCount => referenceResults
      .where((r) => r.classification == AnalyteClassification.high)
      .length;

  int get criticalCount => referenceResults
      .where((r) => r.classification == AnalyteClassification.critical)
      .length;

  bool get hasAbnormalReferenceFindings =>
      lowCount > 0 || highCount > 0 || criticalCount > 0;

  bool get hasDiabetesResult => diabetesRisk != null;
  bool get hasHeartResult => heartRisk != null;
  bool get hasKidneyResult => kidneyRisk != null;
  bool get hasGenAiExplanation => genAiExplanation?.explanation != null;

  String get formattedDate {
    final y = createdAt.year.toString();
    final m = createdAt.month.toString().padLeft(2, '0');
    final d = createdAt.day.toString().padLeft(2, '0');
    final h = createdAt.hour.toString().padLeft(2, '0');
    final min = createdAt.minute.toString().padLeft(2, '0');
    return '$y-$m-$d $h:$min';
  }

  // --- Serialization ---

  Map<String, dynamic> toJson() => {
        'id': id,
        'created_at': createdAt.toIso8601String(),
        'document_name': documentName,
        'verified_measurement_count': verifiedMeasurementCount,
        if (patientAge != null) 'patient_age': patientAge,
        if (patientSex != null) 'patient_sex': patientSex,
        'reference_results': referenceResults.map((r) => r.toJson()).toList(),
        'total_classified': totalClassified,
        if (diabetesRisk != null) 'diabetes_risk': diabetesRisk!.toJson(),
        if (heartRisk != null) 'heart_risk': heartRisk!.toJson(),
        if (kidneyRisk != null) 'kidney_risk': kidneyRisk!.toJson(),
        if (genAiExplanation != null)
          'genai_explanation': genAiExplanation!.toJson(),
        'selected_language': selectedLanguage.code,
        'disclaimer': disclaimer,
      };

  factory AnalysisHistoryItem.fromJson(Map<String, dynamic> json) {
    return AnalysisHistoryItem(
      id: json['id'] as String? ?? '',
      createdAt: DateTime.tryParse(json['created_at'] as String? ?? '') ??
          DateTime.now(),
      documentName: json['document_name'] as String? ?? 'Medical Report',
      verifiedMeasurementCount:
          (json['verified_measurement_count'] as num?)?.toInt() ?? 0,
      patientAge: (json['patient_age'] as num?)?.toDouble(),
      patientSex: json['patient_sex'] as String?,
      referenceResults: (json['reference_results'] as List<dynamic>?)
              ?.map((e) => AnalysisResult.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      totalClassified: (json['total_classified'] as num?)?.toInt() ?? 0,
      diabetesRisk: json['diabetes_risk'] != null
          ? RiskPredictionResponse.fromJson(
              json['diabetes_risk'] as Map<String, dynamic>)
          : null,
      heartRisk: json['heart_risk'] != null
          ? RiskPredictionResponse.fromJson(
              json['heart_risk'] as Map<String, dynamic>)
          : null,
      kidneyRisk: json['kidney_risk'] != null
          ? RiskPredictionResponse.fromJson(
              json['kidney_risk'] as Map<String, dynamic>)
          : null,
      genAiExplanation: json['genai_explanation'] != null
          ? GenAIExplainResponse.fromJson(
              json['genai_explanation'] as Map<String, dynamic>)
          : null,
      selectedLanguage:
          SupportedLanguage.fromCode(json['selected_language'] as String?),
      disclaimer: json['disclaimer'] as String? ??
          'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
    );
  }

  @override
  List<Object?> get props => [
        id,
        createdAt,
        documentName,
        verifiedMeasurementCount,
        patientAge,
        patientSex,
        referenceResults,
        totalClassified,
        diabetesRisk,
        heartRisk,
        kidneyRisk,
        genAiExplanation,
        selectedLanguage,
        disclaimer,
      ];
}
