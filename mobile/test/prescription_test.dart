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
          home: RepositoryProvider<ApiService>.value(
            value: mockApiService,
            child: const PrescriptionExplainerScreen(),
          ),
        ),
      );

      expect(find.text('Prescription Explainer'), findsOneWidget);
      expect(find.text('OBJECTIVE 2'), findsOneWidget);
      expect(find.text('Understanding Prescriptions'), findsOneWidget);
      expect(find.text('Photo / PDF Upload'), findsOneWidget);
      expect(find.text('Prescription Text'), findsOneWidget);
      expect(find.text('Explain Prescription (Objective 2)'), findsOneWidget);
    });

    testWidgets('switching to text tab shows presets and text field',
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

      expect(find.text('Quick Demonstration Presets:'), findsOneWidget);
      expect(find.text('Chronic (BP/Diabetes)'), findsOneWidget);
      expect(find.text('Infection (Antibiotics)'), findsOneWidget);
      expect(find.text('Handwritten (Safety Flag)'), findsOneWidget);
    });

    testWidgets('tapping preset loads prescription text into field',
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

      // Tap preset 1
      await tester.tap(find.text('Chronic (BP/Diabetes)'));
      await tester.pumpAndSettle();

      final textField = tester.widget<TextField>(find.byType(TextField));
      expect(textField.controller?.text, contains('Metformin 500mg'));
      expect(textField.controller?.text, contains('Amlodipine 5mg'));
    });

    testWidgets(
        'submitting prescription renders structured 4-column table, safety banner, and doctor notes',
        (tester) async {
      tester.view.physicalSize = const Size(800, 1800);
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

      // Switch to text tab and select preset
      await tester.tap(find.text('Prescription Text'));
      await tester.pumpAndSettle();
      await tester.tap(find.text('Chronic (BP/Diabetes)'));
      await tester.pumpAndSettle();

      // Tap explain button
      await tester.ensureVisible(find.text('Explain Prescription (Objective 2)'));
      await tester.tap(find.text('Explain Prescription (Objective 2)'));
      await tester.pumpAndSettle();

      // Verify 4 exact table columns exist
      expect(find.text('Medicine Name'), findsOneWidget);
      expect(find.text('Purpose'), findsOneWidget);
      expect(find.text('Dosage'), findsOneWidget);
      expect(find.text('When to Take'), findsOneWidget);

      // Verify row values
      expect(find.text('Metformin 500mg'), findsOneWidget);
      expect(find.text('Controls blood sugar levels in type 2 diabetes'),
          findsOneWidget);
      expect(find.text('500 mg'), findsOneWidget);
      expect(find.text('Twice daily after meals'), findsOneWidget);

      // Verify safety confirmation flag badge
      expect(find.text('⚠️ Confirm with Pharmacist'), findsOneWidget);

      // Verify doctor notes card
      expect(find.text('Doctor Notes & Clinical Advice'), findsOneWidget);
      expect(
          find.text('Doctor Advice: Low salt diet and brisk walk daily'),
          findsOneWidget);

      // Verify safety disclaimer banner
      expect(
          find.text('Important Safety & Clinical Guidance'), findsOneWidget);
      expect(
          find.textContaining('Gemini-generated information must NOT override'),
          findsOneWidget);

      // Verify questions for doctor card
      expect(find.text('Questions to Ask Your Doctor or Pharmacist'),
          findsOneWidget);
      expect(find.text('How long should I take this medication?'),
          findsOneWidget);
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
      await tester.tap(find.text('Chronic (BP/Diabetes)'));
      await tester.pumpAndSettle();

      await tester.ensureVisible(find.text('Explain Prescription (Objective 2)'));
      await tester.tap(find.text('Explain Prescription (Objective 2)'));
      await tester.pumpAndSettle();

      expect(find.text('Unable to Process Prescription'), findsOneWidget);
      expect(find.textContaining('Server connection failed'), findsOneWidget);
    });
  });
}
