import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/history/analysis_history_item.dart';
import 'package:medintel_mobile/models/reference/analysis_result.dart';
import 'package:medintel_mobile/models/reference/patient_details.dart';
import 'package:medintel_mobile/models/reference/reference_range_summary.dart';
import 'package:medintel_mobile/screens/history/biomarker_trends_screen.dart';
import 'package:medintel_mobile/widgets/structured_medical_table.dart';

void main() {
  group('Objective 3: Structured Medical Table & Dashboard Tests', () {
    final sampleResults = [
      const AnalysisResult(
        originalTestName: 'Fasting Blood Glucose',
        canonicalName: 'Glucose, Fasting',
        numericValue: 142.0,
        unit: 'mg/dL',
        normalizedUnit: 'mg/dL',
        classification: AnalyteClassification.high,
        analysisStatus: 'EVALUATED',
        referenceRange: ReferenceRangeSummary(
          canonicalName: 'Glucose, Fasting',
          unit: 'mg/dL',
          normalLow: 70.0,
          normalHigh: 99.0,
          criticalLow: 50.0,
          criticalHigh: 400.0,
          source: 'ADA Standards of Care 2024',
        ),
        alertMessage: 'Fasting glucose is elevated above the normal physiological threshold (70-99 mg/dL).',
        possibleHealthImplications: 'Consistently elevated blood sugar indicates impaired glucose tolerance.',
        precautionsAndNextSteps: 'Consult your physician for confirmation through HbA1c testing.',
      ),
      const AnalysisResult(
        originalTestName: 'Serum Creatinine',
        canonicalName: 'Creatinine',
        numericValue: 1.1,
        unit: 'mg/dL',
        normalizedUnit: 'mg/dL',
        classification: AnalyteClassification.normal,
        analysisStatus: 'EVALUATED',
        referenceRange: ReferenceRangeSummary(
          canonicalName: 'Creatinine',
          unit: 'mg/dL',
          normalLow: 0.7,
          normalHigh: 1.3,
          source: 'KDIGO 2023 Clinical Practice Guideline',
        ),
        alertMessage: 'Creatinine level is within expected healthy physiological limits.',
        possibleHealthImplications: 'Normal kidney filtration function indicated.',
        precautionsAndNextSteps: 'Maintain routine hydration and periodic annual checkups.',
      ),
      const AnalysisResult(
        originalTestName: 'Unknown Marker Test',
        canonicalName: null,
        numericValue: null,
        originalValueText: 'Borderline Positive',
        unit: null,
        classification: AnalyteClassification.requiresReview,
        analysisStatus: 'REQUIRES_REVIEW',
        alertMessage: 'Automated evaluation requires clinical review.',
        possibleHealthImplications: 'Implications could not be automatically determined.',
        precautionsAndNextSteps: 'Share this finding with your attending physician.',
      ),
    ];

    testWidgets('Renders all 9 required columns and patient details banner', (tester) async {
      const patientDetails = PatientDetails(
        name: 'Anita Desai',
        age: 48,
        gender: 'Female',
        date: '15/10/2026',
        labName: 'Metropolis Healthcare Pathology Laboratory',
      );

      tester.view.physicalSize = const Size(1920, 1080);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(tester.view.resetPhysicalSize);
      addTearDown(tester.view.resetDevicePixelRatio);

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: StructuredMedicalTable(
                patientDetails: patientDetails,
                results: sampleResults,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // 1. Patient Details Banner
      expect(find.text('Report & Patient Details'), findsOneWidget);
      expect(find.textContaining('Anita Desai'), findsWidgets);
      expect(find.textContaining('48 Y'), findsWidgets);
      expect(find.textContaining('Female'), findsWidgets);
      expect(find.textContaining('Metropolis Healthcare'), findsOneWidget);

      // 2. Table Column Headers
      expect(find.text('Patient Details'), findsOneWidget);
      expect(find.text('Test Name'), findsOneWidget);
      expect(find.text('Observed Value'), findsOneWidget);
      expect(find.text('Unit'), findsOneWidget);
      expect(find.text('Reference Range'), findsOneWidget);
      expect(find.text('Status'), findsOneWidget);
      expect(find.text('Alert Message'), findsOneWidget);
      expect(find.text('Possible Health Implications'), findsOneWidget);
      expect(find.text('Precautions and Next Steps'), findsOneWidget);

      // 3. Observed Data
      expect(find.text('142'), findsOneWidget);
      expect(find.text('HIGH'), findsOneWidget);
      expect(find.text('NORMAL'), findsOneWidget);
      expect(find.text('REQUIRES REVIEW'), findsOneWidget);
    });

    testWidgets('Displays "Not Available" for missing patient details without hallucination', (tester) async {
      // Missing patient details defaults to "Not Available"
      const emptyDetails = PatientDetails();

      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: StructuredMedicalTable(
                patientDetails: emptyDetails,
                results: sampleResults,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      expect(find.textContaining('Not Available'), findsWidgets);
    });

    testWidgets('Toggles between Table view and Card view cleanly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: SingleChildScrollView(
              child: StructuredMedicalTable(
                results: sampleResults,
              ),
            ),
          ),
        ),
      );
      await tester.pumpAndSettle();

      // Find Cards toggle button
      final cardsButton = find.text('Cards');
      expect(cardsButton, findsOneWidget);
      await tester.tap(cardsButton);
      await tester.pumpAndSettle();

      // Verify card layout renders
      expect(find.text('Glucose, Fasting'), findsOneWidget);
      expect(find.text('Creatinine'), findsOneWidget);
    });

    testWidgets('BiomarkerTrendsScreen displays timeline and comparison tabs', (tester) async {
      final records = [
        AnalysisHistoryItem(
          id: 'rep_1',
          createdAt: DateTime(2026, 9, 1),
          documentName: 'Baseline_Lab_Report.pdf',
          verifiedMeasurementCount: 2,
          referenceResults: sampleResults,
          totalClassified: 2,
        ),
        AnalysisHistoryItem(
          id: 'rep_2',
          createdAt: DateTime(2026, 10, 1),
          documentName: 'Followup_Lab_Report.pdf',
          verifiedMeasurementCount: 2,
          referenceResults: [
            sampleResults[0].copyWith(numericValue: 125.0),
            sampleResults[1],
          ],
          totalClassified: 2,
        ),
      ];

      await tester.pumpWidget(
        MaterialApp(
          home: BiomarkerTrendsScreen(records: records),
        ),
      );
      await tester.pumpAndSettle();

      // Verify Tab headers
      expect(find.text('Biomarker Trends'), findsOneWidget);
      expect(find.text('Compare Reports'), findsOneWidget);

      // Verify trend values
      expect(find.text('Timeline Progression'), findsOneWidget);
      expect(find.text('Baseline_Lab_Report.pdf'), findsOneWidget);
      expect(find.text('Followup_Lab_Report.pdf'), findsOneWidget);

      // Switch to Compare Reports tab
      await tester.tap(find.text('Compare Reports'));
      await tester.pumpAndSettle();

      expect(find.text('Report A (Baseline):'), findsOneWidget);
      expect(find.text('Report B (Follow-up):'), findsOneWidget);
    });
  });
}
