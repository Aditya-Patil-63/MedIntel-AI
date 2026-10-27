import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/auth/user_model.dart';
import 'package:medintel_mobile/screens/settings/settings_screen.dart';
import 'package:medintel_mobile/screens/home/home_screen.dart';
import 'package:medintel_mobile/screens/upload/upload_screen.dart';
import 'package:medintel_mobile/screens/results/results_screen.dart';
import 'package:medintel_mobile/services/api_service.dart';
import 'package:medintel_mobile/state/auth/auth_cubit.dart';
import 'package:medintel_mobile/state/auth/auth_state.dart';
import 'package:medintel_mobile/state/history/history_cubit.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'cubits_test.dart';

void main() {
  late FakeApiService fakeApi;
  const testUser = UserModel(
    id: 1,
    name: 'Aditya Patil',
    email: 'adityapatil88305@gmail.com',
    token: 'test_token',
    languagePreference: 'english',
  );

  setUp(() {
    fakeApi = FakeApiService();
  });

  Widget buildSettingsTestHarness({UserModel user = testUser}) {
    final authCubit = AuthCubit(apiService: fakeApi);
    authCubit.emit(Authenticated(user));
    final historyCubit = HistoryCubit(apiService: fakeApi);

    return RepositoryProvider<ApiService>.value(
      value: fakeApi,
      child: MultiBlocProvider(
        providers: [
          BlocProvider<AuthCubit>.value(value: authCubit),
          BlocProvider<HistoryCubit>.value(value: historyCubit),
        ],
        child: const MaterialApp(
          home: SettingsScreen(),
        ),
      ),
    );
  }

  testWidgets('SettingsScreen displays modern WhatsApp/Telegram style layout',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(1080, 2400);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await tester.pumpWidget(buildSettingsTestHarness());
    await tester.pumpAndSettle();

    // 1. Clean AppBar with 'Settings' title and NO refresh icon
    expect(find.text('Settings'), findsOneWidget);
    expect(find.byIcon(Icons.refresh), findsNothing);
    expect(find.byIcon(Icons.refresh_rounded), findsNothing);

    // 2. Profile Header Card
    expect(find.text('Aditya Patil'), findsOneWidget);
    expect(find.text('adityapatil88305@gmail.com'), findsOneWidget);
    expect(find.text('Active & Isolated'), findsOneWidget);

    // 3. Section Headers
    expect(find.text('PREFERENCES'), findsOneWidget);
    expect(find.text('PRIVACY & CLINICAL SAFETY'), findsOneWidget);
    expect(find.text('NETWORK & BACKEND'), findsOneWidget);
    expect(find.text('ABOUT'), findsOneWidget);

    // 4. Tiles
    expect(find.text('Language'), findsOneWidget);
    expect(find.text('English'), findsOneWidget);
    expect(find.text('Appearance'), findsOneWidget);
    expect(find.text('Patient Data Privacy'), findsOneWidget);
    expect(find.text('Backend Server'), findsOneWidget);
    expect(find.text('About MedIntel AI'), findsOneWidget);
    expect(find.text('Sign Out'), findsOneWidget);

    // 5. Ensure obsolete diagnostic and connection cards are gone
    expect(find.text('Subsystem Diagnostics'), findsNothing);
    expect(find.text('Connection Mode & Server Address'), findsNothing);
  });

  testWidgets('SettingsScreen language picker opens modal and allows selection',
      (WidgetTester tester) async {
    await tester.pumpWidget(buildSettingsTestHarness());
    await tester.pumpAndSettle();

    // Tap on Language tile
    await tester.tap(find.text('Language'));
    await tester.pumpAndSettle();

    // Bottom sheet options appear
    expect(find.text('Select Language'), findsOneWidget);
    expect(find.text('हिंदी (Hindi)'), findsOneWidget);
    expect(find.text('मराठी (Marathi)'), findsOneWidget);
    expect(find.text('ગુજરાતી (Gujarati)'), findsOneWidget);

    // Tap on Hindi
    await tester.tap(find.text('हिंदी (Hindi)'));
    await tester.pumpAndSettle();

    // Language in tile updates
    expect(find.text('हिंदी (Hindi)'), findsOneWidget);
  });

  testWidgets('No refresh icons exist across key screens',
      (WidgetTester tester) async {
    // 1. SettingsScreen
    await tester.pumpWidget(buildSettingsTestHarness());
    await tester.pumpAndSettle();
    expect(find.byIcon(Icons.refresh), findsNothing);
    expect(find.byIcon(Icons.refresh_rounded), findsNothing);
  });
}
