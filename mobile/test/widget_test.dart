import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/app.dart';
import 'package:medintel_mobile/models/auth/user_model.dart';
import 'package:medintel_mobile/screens/auth/login_screen.dart';
import 'package:medintel_mobile/screens/upload/upload_screen.dart';
import 'package:medintel_mobile/screens/verification/verification_screen.dart';
import 'package:medintel_mobile/screens/results/results_screen.dart';
import 'package:medintel_mobile/state/auth/auth_state.dart';
import 'cubits_test.dart';

void main() {
  late FakeApiService fakeApi;
  const testUser = UserModel(
    id: 1,
    name: 'Test Patient',
    email: 'patient@example.com',
    token: 'fake_jwt_token',
  );

  setUp(() {
    fakeApi = FakeApiService();
  });

  testWidgets('MedIntelApp displays LoginScreen on initial startup when unauthenticated',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MedIntelApp(apiService: fakeApi),
    );
    await tester.pumpAndSettle();

    // 1. Initial screen must be LoginScreen
    expect(find.byType(LoginScreen), findsOneWidget);
    expect(find.text('MedIntel AI'), findsOneWidget);
    expect(find.text('Sign In'), findsWidgets);
    expect(find.text('Create Account'), findsOneWidget);
  });

  testWidgets('MedIntelApp renders branding and navigation tiles when authenticated',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MedIntelApp(
        apiService: fakeApi,
        initialAuthState: const Authenticated(testUser),
      ),
    );
    await tester.pumpAndSettle();

    // 1. App Title & Branding
    expect(find.text('MedIntel AI'), findsOneWidget);
    expect(find.text('Welcome, Test Patient'), findsOneWidget);

    // 2. Clinical Pipeline Navigation Cards
    expect(find.text('Upload Report'), findsOneWidget);
    expect(find.text('User Verification Gate'), findsOneWidget);
    expect(find.text('Analysis & ML Risk'), findsOneWidget);
    expect(find.text('Report History'), findsOneWidget);
  });

  testWidgets('UploadScreen displays file constraints and browse button',
      (WidgetTester tester) async {
    await tester.pumpWidget(
      MedIntelApp(
        apiService: fakeApi,
        initialAuthState: const Authenticated(testUser),
      ),
    );
    await tester.pumpAndSettle();

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
      MedIntelApp(
        apiService: fakeApi,
        initialAuthState: const Authenticated(testUser),
      ),
    );
    await tester.pumpAndSettle();

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
      MedIntelApp(
        apiService: fakeApi,
        initialAuthState: const Authenticated(testUser),
      ),
    );
    await tester.pumpAndSettle();

    // Tap Analysis & ML Risk navigation tile
    await tester.tap(find.text('Analysis & ML Risk'));
    await tester.pumpAndSettle();

    expect(find.byType(ResultsScreen), findsOneWidget);
    expect(find.text('Statistical Disease Risk Indicators'), findsOneWidget);
    expect(find.textContaining('This is not a medical diagnosis'),
        findsWidgets);
  });
}
