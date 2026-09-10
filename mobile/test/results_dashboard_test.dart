import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/genai/genai_explain_response.dart';
import 'package:medintel_mobile/models/ml_risk/risk_prediction_response.dart';
import 'package:medintel_mobile/models/reference/analysis_result.dart';
import 'package:medintel_mobile/models/reference/batch_analysis.dart';
import 'package:medintel_mobile/repositories/medical_repository.dart';
import 'package:medintel_mobile/services/api_service.dart';
import 'package:medintel_mobile/state/analysis/analysis_cubit.dart';
import 'package:medintel_mobile/widgets/genai_explanation_card.dart';
import 'package:medintel_mobile/widgets/ml_risk_card.dart';
import 'package:medintel_mobile/widgets/reference_findings_card.dart';

class StubApiService implements ApiService {
  @override
  dynamic noSuchMethod(Invocation invocation) => super.noSuchMethod(invocation);
}

void main() {
  group('Step 4 Results Dashboard Widgets', () {
    testWidgets('ReferenceFindingsCard renders classifications with badges', (tester) async {
      const resp = BatchAnalysisResponse(
        totalSubmitted: 3,
        totalClassified: 3,
        results: [
          AnalysisResult(
            originalTestName: 'Fasting Blood Sugar',
            canonicalName: 'Glucose',
            numericValue: 140.0,
            unit: 'mg/dL',
            classification: AnalyteClassification.high,
            analysisStatus: 'SUCCESS',
          ),
          AnalysisResult(
            originalTestName: 'Hemoglobin',
            canonicalName: 'Hemoglobin',
            numericValue: 14.5,
            unit: 'g/dL',
            classification: AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
          ),
          AnalysisResult(
            originalTestName: 'Potassium',
            canonicalName: 'Potassium',
            numericValue: 2.8,
            unit: 'mEq/L',
            classification: AnalyteClassification.critical,
            analysisStatus: 'SUCCESS',
          ),
        ],
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: ReferenceFindingsCard(response: resp),
            ),
          ),
        ),
      );

      expect(find.text('Laboratory Reference Findings'), findsOneWidget);
      expect(find.textContaining('Fasting Blood Sugar'), findsOneWidget);
      expect(find.text('HIGH'), findsOneWidget);
      expect(find.text('NORMAL'), findsOneWidget);
      expect(find.text('CRITICAL'), findsOneWidget);
    });

    testWidgets('MLRiskCard renders risk probability and band when OK', (tester) async {
      const resp = RiskPredictionResponse(
        condition: 'diabetes',
        status: 'OK',
        riskProbability: 0.62,
        riskBand: RiskBand.moderate,
        modelName: 'XGBoost_Pima',
        modelVersion: '1.0.0',
        suppliedFeaturesCount: 5,
        requiredFeaturesCount: 8,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: MLRiskCard(
              title: 'Diabetes Risk Model',
              conditionName: 'diabetes',
              response: resp,
            ),
          ),
        ),
      );

      expect(find.text('Diabetes Risk Model'), findsOneWidget);
      expect(find.text('62.0%'), findsOneWidget);
      expect(find.text('MODERATE RISK'), findsOneWidget);
      expect(find.textContaining('XGBoost_Pima'), findsOneWidget);
    });

    testWidgets('MLRiskCard renders missing features when INSUFFICIENT_FEATURES', (tester) async {
      const resp = RiskPredictionResponse(
        condition: 'heart_disease',
        status: 'INSUFFICIENT_FEATURES',
        suppliedFeaturesCount: 2,
        requiredFeaturesCount: 13,
        missingFeatures: ['chol', 'trestbps', 'thalach'],
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: MLRiskCard(
              title: 'Heart Disease Risk Model',
              conditionName: 'heart disease',
              response: resp,
            ),
          ),
        ),
      );

      expect(find.text('Heart Disease Risk Model'), findsOneWidget);
      expect(find.text('INSUFFICIENT DATA'), findsOneWidget);
      expect(find.textContaining('Insufficient features for complete ML assessment'), findsOneWidget);
      expect(find.textContaining('chol, trestbps, thalach'), findsOneWidget);
      // Ensures no misleading percentage is rendered
      expect(find.textContaining('%'), findsNothing);
    });

    testWidgets('GenAIExplanationCard renders multilingual selector and key findings', (tester) async {
      final cubit = AnalysisCubit(repository: MedicalRepository(apiService: StubApiService()));

      const resp = GenAIExplainResponse(
        status: GenAIStatus.success,
        language: SupportedLanguage.english,
        explanation: GenAIExplanationPayload(
          summary: 'Your glucose is slightly elevated while renal indicators are healthy.',
          findings: [
            AnalyteExplanationItem(
              analyteName: 'Glucose',
              observedValue: '115 mg/dL',
              classification: 'HIGH',
              plainLanguageMeaning: 'Elevated blood glucose.',
            ),
          ],
          followUpGuidance: ['Monitor fasting glucose'],
          recommendedQuestionsForDoctor: ['Should I monitor fasting glucose daily?'],
        ),
        modelProvider: 'gemini',
        generatedAt: '2026-09-10T12:00:00Z',
      );

      await tester.pumpWidget(
        MaterialApp(
          home: BlocProvider<AnalysisCubit>.value(
            value: cubit,
            child: const Scaffold(
              body: SingleChildScrollView(
                child: GenAIExplanationCard(
                  response: resp,
                  selectedLanguage: SupportedLanguage.english,
                ),
              ),
            ),
          ),
        ),
      );

      expect(find.text('Educational AI Explanation'), findsOneWidget);
      expect(find.textContaining('Your glucose is slightly elevated'), findsOneWidget);
      expect(find.text('Test Insights:'), findsOneWidget);
      expect(
        find.byWidgetPredicate((w) =>
            w is RichText && w.text.toPlainText().contains('Glucose')),
        findsOneWidget,
      );
      expect(find.text('Should I monitor fasting glucose daily?'), findsOneWidget);
      expect(find.text('English'), findsOneWidget);
    });

    testWidgets('GenAIExplanationCard displays graceful degradation and retry CTA on error', (tester) async {
      bool retryPressed = false;

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: GenAIExplanationCard(
              errorMessage: 'AI service rate limit reached (HTTP 429). Please try again shortly.',
              onRetry: () => retryPressed = true,
            ),
          ),
        ),
      );

      expect(find.text('Educational AI Explanation'), findsOneWidget);
      expect(find.text('Explanation Temporarily Unavailable'), findsOneWidget);
      expect(find.textContaining('HTTP 429'), findsOneWidget);
      expect(find.text('Retry AI Explanation'), findsOneWidget);

      await tester.tap(find.text('Retry AI Explanation'));
      expect(retryPressed, true);
    });
  });
}
