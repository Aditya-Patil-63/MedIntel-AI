import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:mocktail/mocktail.dart';
import 'package:medintel_mobile/models/prescription/prescription_model.dart';
import 'package:medintel_mobile/screens/prescription/prescription_explainer_screen.dart';
import 'package:medintel_mobile/services/api_service.dart';
import 'package:medintel_mobile/state/prescription/prescription_cubit.dart';
import 'package:medintel_mobile/state/prescription/prescription_state.dart';

class MockApiService extends Mock implements ApiService {}

void main() {
  setUpAll(() {
    registerFallbackValue(const PrescriptionExplainRequest());
  });

  group('Prescription Models', () {
    test('PrescribedMedicineItem parses json correctly', () {
      final json = {
        'name': 'Metformin 500mg',
        'medicine_name': 'Metformin 500mg',
        'generic_name': 'Metformin Hydrochloride',
        'dosage': '500 mg Tablet',
        'purpose': 'Controls blood sugar levels',
        'when_to_take': 'With or after meals',
        'schedule': 'Twice daily with meals',
        'instructions': 'Swallow whole with water',
        'needs_confirmation': false,
        'confidence_note': null,
      };

      final item = PrescribedMedicineItem.fromJson(json);
      expect(item.name, 'Metformin 500mg');
      expect(item.displayMedicineName, 'Metformin 500mg');
      expect(item.displayDosage, '500 mg Tablet');
      expect(item.purpose, 'Controls blood sugar levels');
      expect(item.displayWhenToTake, 'With or after meals');
      expect(item.needsConfirmation, false);
    });

    test('PrescriptionExplainResponse parses with medicines and safety disclaimer', () {
      final json = {
        'doctor_notes': 'Prescription reviewed',
        'medicines': [
          {
            'name': 'UncertainHerb',
            'purpose': 'Herbal supplement',
            'dosage': '2 ml',
            'when_to_take': 'Before meals',
            'needs_confirmation': true,
            'confidence_note': 'Please confirm with pharmacist',
          }
        ],
        'general_guidance': 'Take regularly',
        'questions_for_doctor': ['How long to take?'],
        'language': 'english',
        'disclaimer': 'Do not override doctor instructions',
      };

      final response = PrescriptionExplainResponse.fromJson(json);
      expect(response.medicines.length, 1);
      expect(response.medicines.first.needsConfirmation, true);
      expect(response.medicines.first.confidenceNote, 'Please confirm with pharmacist');
      expect(response.questionsForDoctor.first, 'How long to take?');
    });
  });

  group('PrescriptionCubit', () {
    late MockApiService mockApiService;
    late PrescriptionCubit cubit;

    setUp(() {
      mockApiService = MockApiService();
      cubit = PrescriptionCubit(apiService: mockApiService);
    });

    tearDown(() {
      cubit.close();
    });

    test('initial state is PrescriptionInitial', () {
      expect(cubit.state, const PrescriptionInitial());
    });

    test('explainPrescriptionMedicines emits Loading and Success', () async {
      const mockResponse = PrescriptionExplainResponse(
        medicines: [
          PrescribedMedicineItem(
            name: 'Metformin',
            purpose: 'Controls sugar',
            dosage: '500mg',
            whenToTake: 'After meals',
          ),
        ],
        generalGuidance: 'Drink water',
        questionsForDoctor: ['When to take?'],
        language: 'english',
        disclaimer: 'Disclaimer test',
      );

      when(() => mockApiService.explainPrescription(any()))
          .thenAnswer((_) async => mockResponse);

      final expectedStates = [
        isA<PrescriptionLoading>(),
        isA<PrescriptionSuccess>(),
      ];

      expectLater(cubit.stream, emitsInOrder(expectedStates));

      await cubit.explainPrescriptionMedicines(['Metformin 500mg']);
    });

    test('explainPrescriptionMedicines emits Failure on error', () async {
      when(() => mockApiService.explainPrescription(any()))
          .thenThrow(Exception('Backend network error'));

      final expectedStates = [
        isA<PrescriptionLoading>(),
        isA<PrescriptionFailure>(),
      ];

      expectLater(cubit.stream, emitsInOrder(expectedStates));

      await cubit.explainPrescriptionMedicines(['Metformin 500mg']);
    });
  });

  group('PrescriptionExplainerScreen Widget Tests', () {
    late MockApiService mockApiService;

    setUp(() {
      mockApiService = MockApiService();
    });

    testWidgets('renders Prescription Explainer headers, tabs, and action button',
        (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(
            body: Builder(
              builder: (context) => ElevatedButton(
                onPressed: () {
                  Navigator.of(context).push(
                    MaterialPageRoute(
                      builder: (_) => RepositoryProvider<ApiService>.value(
                        value: mockApiService,
                        child: const PrescriptionExplainerScreen(),
                      ),
                    ),
                  );
                },
                child: const Text('Open'),
              ),
            ),
          ),
        ),
      );

      // Open screen via navigator to verify back button
      await tester.tap(find.text('Open'));
      await tester.pumpAndSettle();

      // App bar title and back button
      expect(find.text('Prescription Explainer'), findsOneWidget);
      expect(find.byType(BackButton), findsOneWidget);

      // Removed elements must be absent
      expect(find.text('OBJECTIVE 2'), findsNothing);
      expect(find.text('Understanding Prescriptions'), findsNothing);
      expect(find.byIcon(Icons.refresh), findsNothing);

      // Language selector
      expect(find.text('Language:'), findsOneWidget);
      expect(find.text('English'), findsOneWidget);

      // Input selector tabs
      expect(find.text('Photo / PDF Upload'), findsOneWidget);
      expect(find.text('Prescription Text'), findsOneWidget);

      // Prescription input area
      expect(find.text('Upload Prescription Image or PDF'), findsOneWidget);

      // Simplified action button without icon
      expect(find.text('Explain Prescription'), findsOneWidget);
      expect(find.text('Explain Prescription (Objective 2)'), findsNothing);
      expect(find.byIcon(Icons.table_chart_rounded), findsNothing);
    });

    testWidgets('switching to text tab shows clean text field and no presets',
        (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: RepositoryProvider<ApiService>.value(
            value: mockApiService,
            child: const PrescriptionExplainerScreen(),
          ),
        ),
      );

      await tester.tap(find.text('Prescription Text'));
      await tester.pumpAndSettle();

      // Clean hint text
      expect(find.text('Enter prescription details here...'), findsOneWidget);

      // Presets must be removed
      expect(find.text('Quick Demonstration Presets:'), findsNothing);
      expect(find.text('Chronic (BP/Diabetes)'), findsNothing);
      expect(find.text('Infection (Antibiotics)'), findsNothing);
      expect(find.text('Handwritten (Safety Flag)'), findsNothing);
    });

    testWidgets('entering prescription text updates controller and validates correctly',
        (tester) async {
      tester.view.physicalSize = const Size(800, 1400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      await tester.pumpWidget(
        MaterialApp(
          home: RepositoryProvider<ApiService>.value(
            value: mockApiService,
            child: const PrescriptionExplainerScreen(),
          ),
        ),
      );

      await tester.tap(find.text('Prescription Text'));
      await tester.pumpAndSettle();

      await tester.enterText(
        find.byType(TextField),
        'Tab. Metformin 500mg 1-0-1\nTab. Amlodipine 5mg',
      );
      await tester.pumpAndSettle();

      final textField = tester.widget<TextField>(find.byType(TextField));
      expect(textField.controller?.text, contains('Metformin 500mg'));
      expect(textField.controller?.text, contains('Amlodipine 5mg'));
    });

    testWidgets(
        'submitting prescription renders structured medicine cards, doctor notes, and questions without redundant banners',
        (tester) async {
      tester.view.physicalSize = const Size(800, 2400);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      const mockResponse = PrescriptionExplainResponse(
        doctorNotes: 'Doctor Advice: Low salt diet and brisk walk daily',
        medicines: [
          PrescribedMedicineItem(
            name: 'Metformin 500mg',
            medicineName: 'Metformin 500mg',
            genericName: 'Metformin Hydrochloride',
            dosage: '500 mg',
            purpose: 'Controls blood sugar levels in type 2 diabetes',
            whenToTake: 'Twice daily after meals',
            schedule: 'Twice daily with meals',
            instructions: 'Swallow whole with water',
            needsConfirmation: false,
          ),
          PrescribedMedicineItem(
            name: 'UnidentifiedMed? 2ml',
            medicineName: 'UnidentifiedMed? 2ml',
            genericName: 'Prescribed Medication',
            dosage: '2 ml',
            purpose: 'Medication prescribed by your physician',
            whenToTake: 'As advised by doctor or pharmacist',
            schedule: 'As directed',
            instructions: 'Consult doctor',
            needsConfirmation: true,
            confidenceNote: 'Please confirm with pharmacist',
          ),
        ],
        generalGuidance: 'Take medicines with plain water daily.',
        questionsForDoctor: ['How long should I take this medication?'],
        language: 'english',
        disclaimer:
            'This explanation is for educational purposes only. Gemini-generated information must NOT override doctor instructions.',
      );

      when(() => mockApiService.explainPrescription(any()))
          .thenAnswer((_) async => mockResponse);

      await tester.pumpWidget(
        MaterialApp(
          home: RepositoryProvider<ApiService>.value(
            value: mockApiService,
            child: const PrescriptionExplainerScreen(),
          ),
        ),
      );

      // Switch to text tab and enter prescription lines
      await tester.tap(find.text('Prescription Text'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byType(TextField),
        'Rx\n1. Tab. Metformin 500mg 1-0-1\n2. Tab. Amlodipine 5mg',
      );
      await tester.pumpAndSettle();

      // Tap explain button
      await tester.ensureVisible(find.text('Explain Prescription'));
      await tester.tap(find.text('Explain Prescription'));
      await tester.pumpAndSettle();

      // Verify removed elements are absent
      expect(find.text('Important Safety & Clinical Guidance'), findsNothing);
      expect(find.text('Prescribed Medication Schedule Table'), findsNothing);
      expect(find.text('Explain Prescription'), findsNothing); // Hidden in results

      // Verify medicine detail card fields exist
      expect(find.text('Medicine Name'), findsNWidgets(2));
      expect(find.text('Purpose'), findsNWidgets(2));
      expect(find.text('Dosage'), findsNWidgets(2));
      expect(find.text('Frequency'), findsNWidgets(2));

      // Verify row values
      expect(find.text('Metformin 500mg'), findsOneWidget);
      expect(find.text('Controls blood sugar levels in type 2 diabetes'),
          findsOneWidget);
      expect(find.text('500 mg'), findsOneWidget);
      expect(find.text('Twice daily after meals'), findsOneWidget);

      // Verify safety confirmation flag badge
      expect(find.text('Please confirm with pharmacist'), findsOneWidget);

      // Verify doctor notes card
      expect(find.text('Doctor Notes & Clinical Advice'), findsOneWidget);
      expect(
          find.text('Doctor Advice: Low salt diet and brisk walk daily'),
          findsOneWidget);

      // Verify questions for doctor card
      expect(find.text('Questions to Ask Your Doctor or Pharmacist'),
          findsOneWidget);
      expect(find.text('How long should I take this medication?'),
          findsOneWidget);

      // Verify Analyze Another Prescription button is present and resets view
      final analyzeAnotherFinder = find.text('Analyze Another Prescription');
      expect(analyzeAnotherFinder, findsOneWidget);
      await tester.ensureVisible(analyzeAnotherFinder);
      await tester.tap(analyzeAnotherFinder);
      await tester.pumpAndSettle();

      // Input view should be restored
      expect(find.text('Explain Prescription'), findsOneWidget);
      expect(find.text('Analyze Another Prescription'), findsNothing);
    });

    testWidgets('empty text validation shows error snackbar', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          home: RepositoryProvider<ApiService>.value(
            value: mockApiService,
            child: const PrescriptionExplainerScreen(),
          ),
        ),
      );

      await tester.tap(find.text('Prescription Text'));
      await tester.pumpAndSettle();

      await tester.tap(find.text('Explain Prescription'));
      await tester.pump();

      expect(find.text('Please enter prescription text.'), findsOneWidget);
    });

    testWidgets('error state displays failure card', (tester) async {
      tester.view.physicalSize = const Size(800, 1800);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() => tester.view.resetPhysicalSize());

      when(() => mockApiService.explainPrescription(any()))
          .thenThrow(Exception('Server connection failed: 500'));

      await tester.pumpWidget(
        MaterialApp(
          home: RepositoryProvider<ApiService>.value(
            value: mockApiService,
            child: const PrescriptionExplainerScreen(),
          ),
        ),
      );

      await tester.tap(find.text('Prescription Text'));
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byType(TextField),
        'Tab. Metformin 500mg 1-0-1',
      );
      await tester.pumpAndSettle();

      await tester.ensureVisible(find.text('Explain Prescription'));
      await tester.tap(find.text('Explain Prescription'));
      await tester.pumpAndSettle();

      expect(find.text('Unable to Process Prescription'), findsOneWidget);
      expect(find.textContaining('Server connection failed'), findsOneWidget);
    });
  });
}
