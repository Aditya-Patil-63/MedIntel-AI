import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/app.dart';
import 'cubits_test.dart';

void main() {
  testWidgets('MedIntelApp renders branding, disclaimer banner, and navigation tiles',
      (WidgetTester tester) async {
    final fakeApi = FakeApiService();

    await tester.pumpWidget(
      MedIntelApp(apiService: fakeApi),
    );

    // Initial pump
    await tester.pump();

    // 1. Verify App Title & Branding
    expect(find.text('MedIntel AI'), findsOneWidget);
    expect(find.text('Phase 9 Mobile Client'), findsOneWidget);

    // 2. Verify Mandatory Educational Disclaimer Banner
    expect(
      find.text(
        'This is not a medical diagnosis. Please consult a qualified healthcare professional.',
      ),
      findsOneWidget,
    );

    // 3. Verify Clinical Pipeline Navigation Cards
    expect(find.text('Upload Report'), findsOneWidget);
    expect(find.text('User Verification Gate'), findsOneWidget);
    expect(find.text('Analysis & ML Risk'), findsOneWidget);
    expect(find.text('Report History'), findsOneWidget);

    // 4. Verify Subsystems Header
    expect(find.text('Subsystem Status'), findsOneWidget);
  });
}
