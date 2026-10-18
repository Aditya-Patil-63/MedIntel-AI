import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/history/analysis_history_item.dart';
import 'package:medintel_mobile/state/auth/auth_cubit.dart';
import 'package:medintel_mobile/state/auth/auth_state.dart';
import 'package:medintel_mobile/state/history/history_cubit.dart';
import 'package:medintel_mobile/state/history/history_state.dart';
import 'cubits_test.dart';

void main() {
  late FakeApiService fakeApi;
  late AuthCubit authCubit;
  late HistoryCubit historyCubit;

  setUp(() {
    fakeApi = FakeApiService();
    authCubit = AuthCubit(apiService: fakeApi);
    historyCubit = HistoryCubit(apiService: fakeApi);
  });

  tearDown(() {
    authCubit.close();
    historyCubit.close();
  });

  group('AuthCubit Lifecycle', () {
    test('initial state is Unauthenticated', () {
      expect(authCubit.state, isA<Unauthenticated>());
      expect(authCubit.currentUser, isNull);
    });

    test('login emits AuthLoading then Authenticated on success', () async {
      final success = await authCubit.login(
        email: 'patient@example.com',
        password: 'ValidPassword123',
      );

      expect(success, isTrue);
      expect(authCubit.state, isA<Authenticated>());
      final user = (authCubit.state as Authenticated).user;
      expect(user.email, equals('patient@example.com'));
      expect(fakeApi.currentAuthToken, equals('fake_test_jwt_token'));
    });

    test('login with empty credentials emits AuthError', () async {
      final success = await authCubit.login(email: '', password: '');
      expect(success, isFalse);
      expect(authCubit.state, isA<AuthError>());
    });

    test('register emits Authenticated on valid input', () async {
      final success = await authCubit.register(
        name: 'Jane Smith',
        email: 'jane.smith@example.com',
        password: 'Password123',
      );

      expect(success, isTrue);
      expect(authCubit.state, isA<Authenticated>());
      final user = (authCubit.state as Authenticated).user;
      expect(user.name, equals('Jane Smith'));
      expect(user.email, equals('jane.smith@example.com'));
    });

    test('register rejects short password and invalid email', () async {
      final badEmail = await authCubit.register(
        name: 'Jane',
        email: 'not-an-email',
        password: 'validpassword',
      );
      expect(badEmail, isFalse);
      expect(authCubit.state, isA<AuthError>());

      final shortPass = await authCubit.register(
        name: 'Jane',
        email: 'jane@example.com',
        password: '123',
      );
      expect(shortPass, isFalse);
      expect(authCubit.state, isA<AuthError>());
    });

    test('logout clears token and emits Unauthenticated', () async {
      await authCubit.login(
        email: 'patient@example.com',
        password: 'ValidPassword123',
      );
      expect(authCubit.state, isA<Authenticated>());

      authCubit.logout();
      expect(authCubit.state, isA<Unauthenticated>());
      expect(fakeApi.currentAuthToken, isNull);
    });
  });

  group('HistoryCubit User-Scoped Persistence', () {
    test('fetches user reports from backend when authenticated', () async {
      fakeApi.setAuthToken('user_token');
      final report = AnalysisHistoryItem(
        id: 'rep_101',
        createdAt: DateTime.now(),
        documentName: 'Blood_Test.pdf',
        verifiedMeasurementCount: 2,
        referenceResults: const [],
        totalClassified: 0,
      );
      await fakeApi.saveUserReport(report);

      await historyCubit.loadHistory();
      expect(historyCubit.state, isA<HistoryLoaded>());
      final loaded = (historyCubit.state as HistoryLoaded).records;
      expect(loaded.length, equals(1));
      expect(loaded.first.id, equals('rep_101'));
    });

    test('clearHistory wipes in-memory cache on user switch', () async {
      final report = AnalysisHistoryItem(
        id: 'rep_102',
        createdAt: DateTime.now(),
        documentName: 'Xray.pdf',
        verifiedMeasurementCount: 1,
        referenceResults: const [],
        totalClassified: 0,
      );
      historyCubit.addRecord(report);
      expect(historyCubit.currentRecords.length, equals(1));

      historyCubit.clearHistory();
      expect(historyCubit.currentRecords, isEmpty);
    });
  });
}
