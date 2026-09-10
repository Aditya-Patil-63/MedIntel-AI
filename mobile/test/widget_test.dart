import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/app.dart';
import 'package:medintel_mobile/screens/upload/upload_screen.dart';
import 'package:medintel_mobile/screens/verification/verification_screen.dart';
import 'package:medintel_mobile/screens/results/results_screen.dart';
import 'cubits_test.dart';

void main() {
  late FakeApiService fakeApi;

  setUp(() {
    fakeApi = FakeApiService();
  });

  testWidgets('MedIntelApp renders branding, disclaimer banner, and navigation tiles',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MedIntelApp(apiService: fakeApi),
    );
    await tester.pump();

    // 1. App Title & Branding
    expect(find.text('MedIntel AI'), findsOneWidget);
    expect(find.text('Phase 9 Mobile Client'), findsOneWidget);

    // 2. Mandatory Educational Disclaimer Banner
    expect(
      find.text(
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
      ),
      findsOneWidget,
    );

    // 3. Clinical Pipeline Navigation Cards
    expect(find.text('Upload Report'), findsOneWidget);
    expect(find.text('User Verification Gate'), findsOneWidget);
    expect(find.text('Analysis & ML Risk'), findsOneWidget);
    expect(find.text('Report History'), findsOneWidget);
  });

  testWidgets('UploadScreen displays file constraints and browse button',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MedIntelApp(apiService: fakeApi),
    );
    await tester.pump();

    // Tap Upload Report navigation tile
    await tester.tap(find.text('Upload Report'));
    await tester.pumpAndSettle();

    // Verify UploadScreen constraints & buttons
    expect(find.byType(UploadScreen), findsOneWidget);
    expect(
      find.text('Supported: PDF, PNG, JPG, JPEG • Maximum file size: 10 MB'),
      findsOneWidget,
    );
    expect(find.text('Browse Files'), findsOneWidget);
  });

  testWidgets('VerificationScreen displays disclaimer, context card, and confirm button',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MedIntelApp(apiService: fakeApi),
    );
    await tester.pump();

    // Tap User Verification Gate navigation tile
    await tester.tap(find.text('User Verification Gate'));
    await tester.pumpAndSettle();

    expect(find.byType(VerificationScreen), findsOneWidget);
    expect(find.text('Patient Context (Optional)'), findsOneWidget);
    expect(find.text('Confirm & Analyze'), findsOneWidget);
  });

  testWidgets('ResultsScreen displays non-diagnostic notice and readiness card',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MedIntelApp(apiService: fakeApi),
    );
    await tester.pump();

    // Tap Analysis & ML Risk navigation tile
    await tester.tap(find.text('Analysis & ML Risk'));
    await tester.pumpAndSettle();

    expect(find.byType(ResultsScreen), findsOneWidget);
    expect(find.text('Statistical Disease Risk Indicators'), findsOneWidget);
    expect(find.textContaining('This is not a medical diagnosis'),
        findsWidgets);
  });
}
