import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import 'core/theme/app_theme.dart';
import 'repositories/medical_repository.dart';
import 'screens/auth/login_screen.dart';
import 'screens/home/home_screen.dart';
import 'services/api_service.dart';
import 'state/analysis/analysis_cubit.dart';
import 'state/auth/auth_cubit.dart';
import 'state/auth/auth_state.dart';
import 'state/document/document_cubit.dart';
import 'state/history/history_cubit.dart';
import 'state/verification/verification_cubit.dart';

/// Root Application widget configuring BLoC dependencies, Theme,
/// and the primary navigation shell with authentication gateway.
class MedIntelApp extends StatelessWidget {
  final ApiService? apiService;
  final MedicalRepository? medicalRepository;
  final AuthState? initialAuthState;

  const MedIntelApp({
    super.key,
    this.apiService,
    this.medicalRepository,
    this.initialAuthState,
  });

  @override
  Widget build(BuildContext context) {
    final effectiveApiService = apiService ?? ApiServiceImpl();
    final effectiveRepo = medicalRepository ??
        MedicalRepository(apiService: effectiveApiService);

    return MultiRepositoryProvider(
      providers: [
        RepositoryProvider<ApiService>.value(value: effectiveApiService),
        RepositoryProvider<MedicalRepository>.value(value: effectiveRepo),
      ],
      child: MultiBlocProvider(
        providers: [
          BlocProvider<AuthCubit>(
            create: (_) => AuthCubit(
              apiService: effectiveApiService,
              initialState: initialAuthState,
            ),
          ),
          BlocProvider<DocumentCubit>(
            create: (_) => DocumentCubit(apiService: effectiveApiService),
          ),
          BlocProvider<VerificationCubit>(
            create: (_) => VerificationCubit(apiService: effectiveApiService),
          ),
          BlocProvider<AnalysisCubit>(
            create: (_) => AnalysisCubit(repository: effectiveRepo),
          ),
          BlocProvider<HistoryCubit>(
            create: (_) => HistoryCubit(apiService: effectiveApiService),
          ),
        ],
        child: MaterialApp(
          title: 'MedIntel AI',
          theme: AppTheme.lightTheme,
          debugShowCheckedModeBanner: false,
          home: BlocBuilder<AuthCubit, AuthState>(
            builder: (context, state) {
              if (state is Authenticated) {
                return const HomeScreen();
              }
              return const LoginScreen();
            },
          ),
        ),
      ),
    );
  }
}
