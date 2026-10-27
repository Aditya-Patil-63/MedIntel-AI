import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/errors/api_exception.dart';
import '../../models/auth/user_model.dart';
import '../../services/api_service.dart';
import 'auth_state.dart';

/// Cubit managing user authentication and active patient session state.
class AuthCubit extends Cubit<AuthState> {
  final ApiService apiService;

  AuthCubit({required this.apiService, AuthState? initialState})
      : super(initialState ?? const Unauthenticated());

  /// Returns the currently authenticated user, or null if unauthenticated.
  UserModel? get currentUser {
    if (state is Authenticated) {
      return (state as Authenticated).user;
    }
    return null;
  }

  /// Authenticate with email and password.
  Future<bool> login({
    required String email,
    required String password,
  }) async {
    final cleanEmail = email.trim();
    final cleanPassword = password.trim();

    if (cleanEmail.isEmpty || cleanPassword.isEmpty) {
      emit(const AuthError('Please enter both email address and password.'));
      return false;
    }

    emit(const AuthLoading(message: 'Signing in...'));

    try {
      final user = await apiService.login(
        email: cleanEmail,
        password: cleanPassword,
      );
      emit(Authenticated(user));
      return true;
    } on ApiException catch (e) {
      emit(AuthError(e.message));
      return false;
    } catch (e) {
      emit(AuthError('Failed to sign in. Please verify network connection.'));
      return false;
    }
  }

  /// Authenticate or register using a Google account.
  Future<bool> loginWithGoogle({
    required String email,
    String? name,
    String? googleId,
  }) async {
    final cleanEmail = email.trim();
    if (cleanEmail.isEmpty || !cleanEmail.contains('@')) {
      emit(const AuthError('Please provide a valid Google email address.'));
      return false;
    }

    emit(const AuthLoading(message: 'Signing in with Google...'));

    try {
      final user = await apiService.loginWithGoogle(
        email: cleanEmail,
        name: name,
        googleId: googleId,
      );
      emit(Authenticated(user));
      return true;
    } on ApiException catch (e) {
      emit(AuthError(e.message));
      return false;
    } catch (e) {
      emit(AuthError('Google sign-in failed. Please verify network connection.'));
      return false;
    }
  }

  /// Register a new user account.
  Future<bool> register({
    required String name,
    required String email,
    required String password,
    String? languagePreference,
  }) async {
    final cleanName = name.trim();
    final cleanEmail = email.trim();
    final cleanPassword = password.trim();

    if (cleanName.length < 2) {
      emit(const AuthError('Full name must be at least 2 characters.'));
      return false;
    }
    if (!cleanEmail.contains('@') || !cleanEmail.contains('.')) {
      emit(const AuthError('Please provide a valid email address.'));
      return false;
    }
    if (cleanPassword.length < 6) {
      emit(const AuthError('Password must be at least 6 characters.'));
      return false;
    }

    emit(const AuthLoading(message: 'Creating your account...'));

    try {
      final user = await apiService.register(
        name: cleanName,
        email: cleanEmail,
        password: cleanPassword,
        languagePreference: languagePreference,
      );
      emit(Authenticated(user));
      return true;
    } on ApiException catch (e) {
      emit(AuthError(e.message));
      return false;
    } catch (e) {
      emit(AuthError('Registration failed. Please check network connection.'));
      return false;
    }
  }

  /// Sign out the current user, clearing session tokens and history scoping.
  void logout() {
    apiService.setAuthToken(null);
    emit(const Unauthenticated(message: 'Signed out successfully.'));
  }
}
