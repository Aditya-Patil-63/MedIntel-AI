import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/core/utils/date_formatter.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/history/analysis_history_item.dart';
import 'package:medintel_mobile/models/history/prescription_history_item.dart';
import 'package:medintel_mobile/models/history/unified_history_item.dart';
import 'package:medintel_mobile/models/prescription/prescription_model.dart';
import 'package:medintel_mobile/models/reference/analysis_result.dart';
import 'package:medintel_mobile/screens/history/history_detail_screen.dart';
import 'package:medintel_mobile/screens/history/history_screen.dart';
import 'package:medintel_mobile/screens/history/prescription_history_detail_screen.dart';
import 'package:medintel_mobile/state/history/history_cubit.dart';
import 'cubits_test.dart';

void main() {
  group('Date Formatter Tests', () {
    test('formatHistoryTimestamp formats standard date correctly', () {
      final dt = DateTime(2026, 10, 27, 19, 45); // 7:45 PM
      final formatted = formatHistoryTimestamp(dt);
      expect(formatted, contains('27 Oct 2026'));
      expect(formatted, contains('7:45 PM'));
    });

    test('formatHistoryTimestamp handles morning AM timestamps', () {
      final dt = DateTime(2026, 1, 5, 9, 5); // 9:05 AM
      final formatted = formatHistoryTimestamp(dt);
      expect(formatted, contains('5 Jan 2026'));
      expect(formatted, contains('9:05 AM'));
    });
  });

  group('PrescriptionHistoryItem & UnifiedHistoryItem Model Tests', () {
    test('PrescriptionHistoryItem serialization and helper getters', () {
      final item = PrescriptionHistoryItem(
        id: 'rx_test_1',
        createdAt: DateTime(2026, 10, 27, 18, 30),
        title: 'Diabetes Rx',
        documentName: 'Prescription_DrSharma.jpg',
        doctorName: 'Dr. Sharma',
        hospitalName: 'City Hospital',
        medicines: const [
          PrescribedMedicineItem(
            name: 'Metformin',
            purpose: 'Blood sugar control',
            dosage: '500 mg',
            whenToTake: 'Twice daily after meals',
          ),
          PrescribedMedicineItem(
            name: 'Glimepiride',
            purpose: 'Stimulates insulin secretion',
            dosage: '1 mg',
            whenToTake: 'Morning before breakfast',
          ),
        ],
        generalGuidance: 'Monitor blood sugar weekly.',
        questionsForDoctor: const ['Can dosage be reduced?'],
      );

      expect(item.medicineCount, equals(2));
      expect(item.medicineNamesSummary, equals('Metformin, Glimepiride'));
      expect(item.formattedDate, contains('27 Oct 2026'));

      final json = item.toJson();
      final restored = PrescriptionHistoryItem.fromJson(json);
      expect(restored.id, equals(item.id));
      expect(restored.doctorName, equals('Dr. Sharma'));
      expect(restored.hospitalName, equals('City Hospital'));
      expect(restored.medicines.length, equals(2));
      expect(restored.generalGuidance, equals('Monitor blood sugar weekly.'));
    });

    test('UnifiedHistoryItem wraps report and prescription and sorts newest first', () {
      final report = AnalysisHistoryItem(
        id: 'rep_1',
        createdAt: DateTime(2026, 10, 27, 10, 0),
        documentName: 'Blood_Report.pdf',
        verifiedMeasurementCount: 3,
        totalClassified: 3,
        referenceResults: const [],
      );

      final rx = PrescriptionHistoryItem(
        id: 'rx_1',
        createdAt: DateTime(2026, 10, 27, 15, 0),
        title: 'Prescription',
        documentName: 'Rx_DrRao.pdf',
        doctorName: 'Dr. Rao',
        medicines: const [
          PrescribedMedicineItem(
            name: 'Paracetamol',
            purpose: 'Pain relief',
            dosage: '650 mg',
          ),
        ],
        questionsForDoctor: const [],
      );

      final uReport = UnifiedHistoryItem.fromReport(report);
      final uRx = UnifiedHistoryItem.fromPrescription(rx);

      expect(uReport.isReport, isTrue);
      expect(uReport.isPrescription, isFalse);
      expect(uRx.isPrescription, isTrue);
      expect(uRx.isReport, isFalse);

      final list = [uReport, uRx];
      list.sort((a, b) => b.timestamp.compareTo(a.timestamp));

      // Newest first: rx (15:00) should be first, report (10:00) should be second
      expect(list.first.id, equals('rx_1'));
      expect(list.last.id, equals('rep_1'));
    });
  });

  group('HistoryScreen UI & Redesign Widget Tests', () {
    late FakeApiService fakeApi;
    late HistoryCubit historyCubit;

    setUp(() {
      fakeApi = FakeApiService();
      historyCubit = HistoryCubit(apiService: fakeApi);
    });

    tearDown(() {
      historyCubit.close();
    });

    Widget createTestApp(Widget child) {
      return MaterialApp(
        theme: ThemeData(useMaterial3: true),
        home: BlocProvider<HistoryCubit>.value(
          value: historyCubit,
          child: child,
        ),
      );
    }

    testWidgets('History screen has title "History" and NOT "Report History"', (tester) async {
      await tester.pumpWidget(createTestApp(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.text('History'), findsWidgets);
      expect(find.text('Report History'), findsNothing);
    });

    testWidgets('Removed banners are NOT present on HistoryScreen', (tester) async {
      await tester.pumpWidget(createTestApp(const HistoryScreen()));
      await tester.pumpAndSettle();

      // Banner 1: Medical disclaimer banner removed from History screen
      expect(
        find.textContaining('This is not a medical diagnosis. Please consult a qualified healthcare professional.'),
        findsNothing,
      );

      // Banner 2: Session history note removed from History screen
      expect(
        find.textContaining('Session History: Records are saved locally for this session'),
        findsNothing,
      );
      expect(
        find.textContaining('saved locally for this session'),
        findsNothing,
      );
    });

    testWidgets('Displays 3 tabs: All, Reports, Prescriptions', (tester) async {
      await tester.pumpWidget(createTestApp(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.text('All'), findsOneWidget);
      expect(find.text('Reports'), findsOneWidget);
      expect(find.text('Prescriptions'), findsOneWidget);
    });

    testWidgets('Empty state is displayed when history is empty', (tester) async {
      await tester.pumpWidget(createTestApp(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.text('No History Records Yet'), findsOneWidget);
      expect(
        find.text('Upload a medical report or analyze a prescription to see your health history here.'),
        findsOneWidget,
      );
    });

    testWidgets('Displays reports and prescriptions under "All" and filters under tabs', (tester) async {
      final sampleReport = AnalysisHistoryItem(
        id: 'rep_100',
        createdAt: DateTime(2026, 10, 27, 10, 0),
        documentName: 'CBC_Analysis.pdf',
        verifiedMeasurementCount: 4,
        totalClassified: 4,
        referenceResults: const [
          AnalysisResult(
            originalTestName: 'Hemoglobin',
            numericValue: 13.5,
            classification: AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
          ),
        ],
      );

      final sampleRx = PrescriptionHistoryItem(
        id: 'rx_200',
        createdAt: DateTime(2026, 10, 27, 11, 0),
        title: 'Prescription - Dr. Patel',
        documentName: 'Rx_DrPatel.pdf',
        doctorName: 'Dr. Patel',
        medicines: const [
          PrescribedMedicineItem(
            name: 'Metformin',
            purpose: 'Type 2 Diabetes',
            dosage: '500 mg',
            whenToTake: 'With meals',
          ),
        ],
        questionsForDoctor: const [],
      );

      historyCubit.addRecord(sampleReport);
      historyCubit.addPrescription(sampleRx);

      await tester.pumpWidget(createTestApp(const HistoryScreen()));
      await tester.pumpAndSettle();

      // Under "All" tab: both are visible
      expect(find.text('CBC_Analysis.pdf'), findsOneWidget);
      expect(find.textContaining('Dr. Patel'), findsWidgets);
      expect(find.text('Metformin'), findsOneWidget);

      // Switch to "Reports" tab
      await tester.tap(find.text('Reports'));
      await tester.pumpAndSettle();

      expect(find.text('CBC_Analysis.pdf'), findsOneWidget);
      expect(find.textContaining('Dr. Patel'), findsNothing);

      // Switch to "Prescriptions" tab
      await tester.tap(find.text('Prescriptions'));
      await tester.pumpAndSettle();

      expect(find.textContaining('Dr. Patel'), findsWidgets);
      expect(find.text('Metformin'), findsOneWidget);
      expect(find.text('CBC_Analysis.pdf'), findsNothing);
    });

    testWidgets('Tapping a report opens read-only HistoryDetailScreen', (tester) async {
      final sampleReport = AnalysisHistoryItem(
        id: 'rep_read_only',
        createdAt: DateTime(2026, 10, 27, 10, 0),
        documentName: 'Lipid_Panel.pdf',
        verifiedMeasurementCount: 2,
        totalClassified: 2,
        patientAge: 52,
        patientSex: 'M',
        referenceResults: const [],
      );

      historyCubit.addRecord(sampleReport);

      await tester.pumpWidget(createTestApp(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.text('Lipid_Panel.pdf'), findsOneWidget);

      await tester.tap(find.text('View Snapshot'));
      await tester.pumpAndSettle();

      // Opens HistoryDetailScreen in read-only mode
      expect(find.byType(HistoryDetailScreen), findsOneWidget);
      expect(find.text('Historical Analysis'), findsOneWidget);
    });

    testWidgets('Tapping a prescription opens read-only PrescriptionHistoryDetailScreen', (tester) async {
      final sampleRx = PrescriptionHistoryItem(
        id: 'rx_read_only',
        createdAt: DateTime(2026, 10, 27, 12, 0),
        title: 'Prescription - Dr. Mehta',
        documentName: 'Rx_DrMehta.pdf',
        doctorName: 'Dr. Mehta',
        hospitalName: 'Apex Clinic',
        medicines: const [
          PrescribedMedicineItem(
            name: 'Amlodipine',
            purpose: 'Blood pressure control',
            dosage: '5 mg',
            whenToTake: 'Once daily in morning',
          ),
        ],
        generalGuidance: 'Check BP regularly.',
        questionsForDoctor: const ['Should I follow a low sodium diet?'],
      );

      historyCubit.addPrescription(sampleRx);

      await tester.pumpWidget(createTestApp(const HistoryScreen()));
      await tester.pumpAndSettle();

      expect(find.textContaining('Dr. Mehta'), findsWidgets);

      await tester.tap(find.text('View Prescription'));
      await tester.pumpAndSettle();

      // Opens PrescriptionHistoryDetailScreen in read-only mode
      expect(find.byType(PrescriptionHistoryDetailScreen), findsOneWidget);
      expect(find.text('Prescription Details'), findsOneWidget);
      expect(find.text('Dr. Mehta'), findsWidgets);
      expect(find.text('Apex Clinic'), findsWidgets);
      expect(find.text('Amlodipine'), findsWidgets);
      expect(find.text('Check BP regularly.'), findsOneWidget);
    });
  });
}
