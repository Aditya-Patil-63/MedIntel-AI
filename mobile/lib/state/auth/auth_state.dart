import 'package:equatable/equatable.dart';
import '../../models/auth/user_model.dart';

/// Authentication state hierarchy.
abstract class AuthState extends Equatable {
  const AuthState();

  @override
  List<Object?> get props => [];
}

/// Initial state before any authentication check.
class AuthInitial extends AuthState {
  const AuthInitial();
}

/// State while an authentication request (login, register, check) is underway.
class AuthLoading extends AuthState {
  final String? message;
  const AuthLoading({this.message});

  @override
  List<Object?> get props => [message];
}

/// State when a user is successfully authenticated with a valid session.
class Authenticated extends AuthState {
  final UserModel user;
  const Authenticated(this.user);

  @override
  List<Object?> get props => [user];
}

/// State when no active authenticated session exists.
class Unauthenticated extends AuthState {
  final String? message;
  const Unauthenticated({this.message});

  @override
  List<Object?> get props => [message];
}

/// State when an authentication operation fails with an error message.
class AuthError extends AuthState {
  final String message;
  const AuthError(this.message);

  @override
  List<Object?> get props => [message];
}
