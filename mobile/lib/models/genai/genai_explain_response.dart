import 'package:equatable/equatable.dart';
import '../common/enums.dart';

/// Analyte breakdown item in explanation.
class AnalyteExplanationItem extends Equatable {
  final String analyteName;
  final String? observedValue;
  final String? classification;
  final String plainLanguageMeaning;

  const AnalyteExplanationItem({
    required this.analyteName,
    this.observedValue,
    this.classification,
    required this.plainLanguageMeaning,
  });

  factory AnalyteExplanationItem.fromJson(Map<String, dynamic> json) {
    return AnalyteExplanationItem(
      analyteName: json['analyte_name'] as String? ?? '',
      observedValue: json['observed_value'] as String?,
      classification: json['classification'] as String?,
      plainLanguageMeaning: json['plain_language_meaning'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'analyte_name': analyteName,
        if (observedValue != null) 'observed_value': observedValue,
        if (classification != null) 'classification': classification,
        'plain_language_meaning': plainLanguageMeaning,
      };

  @override
  List<Object?> get props =>
      [analyteName, observedValue, classification, plainLanguageMeaning];
}

/// Risk breakdown item in explanation.
class RiskExplanationItem extends Equatable {
  final String condition;
  final double? modelProbability;
  final String? riskBand;
  final String plainLanguageExplanation;

  const RiskExplanationItem({
    required this.condition,
    this.modelProbability,
    this.riskBand,
    required this.plainLanguageExplanation,
  });

  factory RiskExplanationItem.fromJson(Map<String, dynamic> json) {
    return RiskExplanationItem(
      condition: json['condition'] as String? ?? '',
      modelProbability: (json['model_probability'] as num?)?.toDouble(),
      riskBand: json['risk_band'] as String?,
      plainLanguageExplanation:
          json['plain_language_explanation'] as String? ?? '',
    );
  }

  Map<String, dynamic> toJson() => {
        'condition': condition,
        if (modelProbability != null) 'model_probability': modelProbability,
        if (riskBand != null) 'risk_band': riskBand,
        'plain_language_explanation': plainLanguageExplanation,
      };

  @override
  List<Object?> get props =>
      [condition, modelProbability, riskBand, plainLanguageExplanation];
}

/// Structured explanation payload.
class GenAIExplanationPayload extends Equatable {
  final String summary;
  final List<AnalyteExplanationItem> findings;
  final List<RiskExplanationItem> riskExplanations;
  final List<String> followUpGuidance;
  final List<String> recommendedQuestionsForDoctor;

  const GenAIExplanationPayload({
    required this.summary,
    this.findings = const [],
    this.riskExplanations = const [],
    this.followUpGuidance = const [],
    this.recommendedQuestionsForDoctor = const [],
  });

  factory GenAIExplanationPayload.fromJson(Map<String, dynamic> json) {
    return GenAIExplanationPayload(
      summary: json['summary'] as String? ?? '',
      findings: (json['findings'] as List<dynamic>?)
              ?.map((e) =>
                  AnalyteExplanationItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      riskExplanations: (json['risk_explanations'] as List<dynamic>?)
              ?.map(
                  (e) => RiskExplanationItem.fromJson(e as Map<String, dynamic>))
              .toList() ??
          const [],
      followUpGuidance: (json['follow_up_guidance'] as List<dynamic>?)
              ?.map((e) => e.toString())
              .toList() ??
          const [],
      recommendedQuestionsForDoctor:
          (json['recommended_questions_for_doctor'] as List<dynamic>?)
                  ?.map((e) => e.toString())
                  .toList() ??
              const [],
    );
  }

  Map<String, dynamic> toJson() => {
        'summary': summary,
        'findings': findings.map((e) => e.toJson()).toList(),
        'risk_explanations': riskExplanations.map((e) => e.toJson()).toList(),
        'follow_up_guidance': followUpGuidance,
        'recommended_questions_for_doctor': recommendedQuestionsForDoctor,
      };

  @override
  List<Object?> get props => [
        summary,
        findings,
        riskExplanations,
        followUpGuidance,
        recommendedQuestionsForDoctor,
      ];
}

/// Response payload from POST /api/v1/genai/explain.
class GenAIExplainResponse extends Equatable {
  final GenAIStatus status;
  final int? reportId;
  final SupportedLanguage language;
  final GenAIExplanationPayload? explanation;
  final String? translatedSummary;
  final String modelProvider;
  final String? modelName;
  final String disclaimer;
  final String generatedAt;
  final int? persistedSummaryId;

  const GenAIExplainResponse({
    required this.status,
    this.reportId,
    this.language = SupportedLanguage.english,
    this.explanation,
    this.translatedSummary,
    required this.modelProvider,
    this.modelName,
    this.disclaimer =
        'This explanation is generated for educational and informational purposes only. It is NOT a medical diagnosis.',
    required this.generatedAt,
    this.persistedSummaryId,
  });

  factory GenAIExplainResponse.fromJson(Map<String, dynamic> json) {
    return GenAIExplainResponse(
      status: GenAIStatus.fromString(json['status'] as String?),
      reportId: (json['report_id'] as num?)?.toInt(),
      language: SupportedLanguage.fromCode(json['language'] as String?),
      explanation: json['explanation'] != null
          ? GenAIExplanationPayload.fromJson(
              json['explanation'] as Map<String, dynamic>)
          : null,
      translatedSummary: json['translated_summary'] as String?,
      modelProvider: json['model_provider'] as String? ?? 'unknown',
      modelName: json['model_name'] as String?,
      disclaimer: json['disclaimer'] as String? ??
          'This explanation is generated for educational and informational purposes only. It is NOT a medical diagnosis.',
      generatedAt: json['generated_at'] as String? ?? '',
      persistedSummaryId: (json['persisted_summary_id'] as num?)?.toInt(),
    );
  }

  Map<String, dynamic> toJson() => {
        'status': status.value,
        if (reportId != null) 'report_id': reportId,
        'language': language.code,
        if (explanation != null) 'explanation': explanation!.toJson(),
        if (translatedSummary != null)
          'translated_summary': translatedSummary,
        'model_provider': modelProvider,
        if (modelName != null) 'model_name': modelName,
        'disclaimer': disclaimer,
        'generated_at': generatedAt,
        if (persistedSummaryId != null)
          'persisted_summary_id': persistedSummaryId,
      };

  @override
  List<Object?> get props => [
        status,
        reportId,
        language,
        explanation,
        translatedSummary,
        modelProvider,
        modelName,
        disclaimer,
        generatedAt,
        persistedSummaryId,
      ];
}
