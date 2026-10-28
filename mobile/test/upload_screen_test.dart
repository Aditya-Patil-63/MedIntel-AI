import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/extraction/document_extraction_result.dart';
import 'package:medintel_mobile/repositories/medical_repository.dart';
import 'package:medintel_mobile/screens/upload/upload_screen.dart';
import 'package:medintel_mobile/screens/verification/verification_screen.dart';
import 'package:medintel_mobile/state/analysis/analysis_cubit.dart';
import 'package:medintel_mobile/state/document/document_cubit.dart';
import 'package:medintel_mobile/state/document/document_state.dart';
import 'package:medintel_mobile/state/verification/verification_cubit.dart';
import 'cubits_test.dart';

void main() {
  group('Upload Medical Report Screen Simplification Tests', () {
    late FakeApiService fakeApi;
    late DocumentCubit documentCubit;
    late VerificationCubit verificationCubit;
    late AnalysisCubit analysisCubit;

    setUp(() {
      fakeApi = FakeApiService();
      documentCubit = DocumentCubit(apiService: fakeApi);
      verificationCubit = VerificationCubit(apiService: fakeApi);
      analysisCubit = AnalysisCubit(repository: MedicalRepository(apiService: fakeApi));
    });

    tearDown(() {
      documentCubit.close();
      verificationCubit.close();
      analysisCubit.close();
    });

    Widget createTestApp({Size size = const Size(390, 844)}) {
      return MultiBlocProvider(
        providers: [
          BlocProvider<DocumentCubit>.value(value: documentCubit),
          BlocProvider<VerificationCubit>.value(value: verificationCubit),
          BlocProvider<AnalysisCubit>.value(value: analysisCubit),
        ],
        child: MaterialApp(
          theme: ThemeData(useMaterial3: true),
          home: MediaQuery(
            data: MediaQueryData(size: size),
            child: const UploadScreen(),
          ),
        ),
      );
    }

    testWidgets('AppBar displays title and has no refresh icon button', (tester) async {
      await tester.pumpWidget(createTestApp());
      await tester.pumpAndSettle();

      expect(find.text('Upload Medical Report'), findsOneWidget);
      expect(find.byIcon(Icons.refresh), findsNothing);
      expect(find.byIcon(Icons.refresh_rounded), findsNothing);
      expect(find.byTooltip('Refresh'), findsNothing);
    });

    testWidgets('Prescription banner is removed from Upload Medical Report screen', (tester) async {
      await tester.pumpWidget(createTestApp());
      await tester.pumpAndSettle();

      expect(find.textContaining("Have a Doctor's Prescription Instead?"), findsNothing);
      expect(find.textContaining('decipher handwriting & view medicine timings'), findsNothing);
      expect(find.textContaining('(Objective 2)'), findsNothing);
    });

    testWidgets('Local server processing message is removed from upload card', (tester) async {
      await tester.pumpWidget(createTestApp());
      await tester.pumpAndSettle();

      expect(
        find.textContaining('Your file is processed safely on your local server'),
        findsNothing,
      );
      expect(
        find.textContaining('local server'),
        findsNothing,
      );
    });

    testWidgets('Renders all required simplified elements cleanly', (tester) async {
      await tester.pumpWidget(createTestApp());
      await tester.pumpAndSettle();

      // 1. Progress steps
      expect(find.text('Upload'), findsOneWidget);
      expect(find.text('Verify'), findsOneWidget);
      expect(find.text('Results'), findsOneWidget);

      // 2. Supported formats
      expect(
        find.text('Supported: PDF, PNG, JPG, JPEG • Maximum file size: 10 MB'),
        findsOneWidget,
      );

      // 3. Upload card heading and instruction
      expect(find.text('Select Medical Report'), findsOneWidget);
      expect(
        find.text('Upload a medical report to extract and analyze your test results.'),
        findsOneWidget,
      );
      expect(find.byIcon(Icons.upload_file_rounded), findsOneWidget);

      // 4. Browse Files button
      expect(find.text('Browse Files'), findsOneWidget);
      expect(find.byIcon(Icons.folder_open_rounded), findsOneWidget);

      // 5. Manual entry option
      expect(
        find.text("Don't have a report? Enter values manually →"),
        findsOneWidget,
      );

      // 6. Next step guidance
      expect(
        find.text('Next: You will review & confirm extracted values'),
        findsOneWidget,
      );
    });

    testWidgets('Tapping manual entry navigates to VerificationScreen', (tester) async {
      await tester.pumpWidget(createTestApp());
      await tester.pumpAndSettle();

      final manualBtn = find.text("Don't have a report? Enter values manually →");
      expect(manualBtn, findsOneWidget);

      await tester.tap(manualBtn);
      await tester.pumpAndSettle();

      expect(find.byType(VerificationScreen), findsOneWidget);
    });

    testWidgets('Renders properly without overflow on small device display (320x568)', (tester) async {
      await tester.pumpWidget(createTestApp(size: const Size(320, 568)));
      await tester.pumpAndSettle();

      expect(find.text('Upload Medical Report'), findsOneWidget);
      expect(find.text('Select Medical Report'), findsOneWidget);
      expect(find.text('Browse Files'), findsOneWidget);
      expect(tester.takeException(), isNull);
    });

    testWidgets('DocumentExtracted state renders simplified actions without (Instant) and (Optional) labels', (tester) async {
      await tester.pumpWidget(createTestApp(size: const Size(400, 1000)));
      await tester.pumpAndSettle();

      const sampleResult = DocumentExtractionResult(
        success: true,
        filename: 'Prathamesh-21C00150020141.pdf',
        sourceType: SourceType.digitalPdf,
        extractor: 'pdfplumber',
        totalPages: 2,
        fullText: 'PATIENT ID: 21C00150020141\nPATIENT NAME: Prathamesh Tukaram Chaudhari\nGLUCOSE: 95 mg/dL',
      );

      documentCubit.emit(const DocumentExtracted(
        result: sampleResult,
        filePath: '/mock/path/Prathamesh-21C00150020141.pdf',
      ));
      await tester.pumpAndSettle();

      // Report status card
      expect(find.text('Prathamesh-21C00150020141.pdf'), findsOneWidget);
      expect(find.text('2 pages processed • digital_pdf'), findsOneWidget);

      // Extracted text preview
      expect(find.text('Extracted Text Preview'), findsOneWidget);
      expect(find.textContaining('Prathamesh Tukaram Chaudhari'), findsOneWidget);

      // Primary button without (Instant)
      expect(find.text('Auto-Analyze Report'), findsOneWidget);
      expect(find.text('Auto-Analyze Report (Instant)'), findsNothing);
      expect(find.textContaining('(Instant)'), findsNothing);

      // Secondary button without (Optional)
      expect(find.text('Review & Verify Measurements'), findsOneWidget);
      expect(find.text('Review & Verify Measurements (Optional)'), findsNothing);
      expect(find.textContaining('(Optional)'), findsNothing);

      // Upload different report
      expect(find.text('Upload a Different Report'), findsOneWidget);

      // Verify no refresh icon and no prescription banner
      expect(find.byIcon(Icons.refresh), findsNothing);
      expect(find.textContaining("Have a Doctor's Prescription Instead?"), findsNothing);
    });

    testWidgets('Tapping Review & Verify Measurements navigates to VerificationScreen', (tester) async {
      await tester.pumpWidget(createTestApp(size: const Size(400, 1000)));
      await tester.pumpAndSettle();

      const sampleResult = DocumentExtractionResult(
        success: true,
        filename: 'Report.pdf',
        sourceType: SourceType.digitalPdf,
        extractor: 'pdfplumber',
        totalPages: 1,
        fullText: 'GLUCOSE: 100 mg/dL',
      );

      documentCubit.emit(const DocumentExtracted(
        result: sampleResult,
        filePath: '/mock/path/Report.pdf',
      ));
      await tester.pumpAndSettle();

      final reviewBtn = find.text('Review & Verify Measurements');
      expect(reviewBtn, findsOneWidget);
      await tester.tap(reviewBtn);
      await tester.pumpAndSettle();

      expect(find.byType(VerificationScreen), findsOneWidget);
    });
  });
}
