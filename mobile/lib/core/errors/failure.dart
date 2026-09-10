import 'package:equatable/equatable.dart';

/// Presentation-layer failure abstraction.
abstract class Failure extends Equatable {
  final String message;
  const Failure(this.message);

  @override
  List<Object?> get props => [message];
}

class ServerFailure extends Failure {
  const ServerFailure(super.message);
}

class NetworkFailure extends Failure {
  const NetworkFailure(super.message);
}

class VerificationFailure extends Failure {
  const VerificationFailure(super.message);
}

class DocumentProcessingFailure extends Failure {
  const DocumentProcessingFailure(super.message);
}
