import 'package:equatable/equatable.dart';
import '../../models/prescription/prescription_model.dart';

/// Lifecycle states for Prescription Explainer (Objective 2).
abstract class PrescriptionState extends Equatable {
  const PrescriptionState();

  @override
  List<Object?> get props => [];
}

class PrescriptionInitial extends PrescriptionState {
  const PrescriptionInitial();
}

class PrescriptionLoading extends PrescriptionState {
  final String message;
  const PrescriptionLoading({this.message = 'Analyzing prescription...'});

  @override
  List<Object?> get props => [message];
}

class PrescriptionSuccess extends PrescriptionState {
  final PrescriptionExplainResponse response;
  final String? inputSource;

  const PrescriptionSuccess(this.response, {this.inputSource});

  @override
  List<Object?> get props => [response, inputSource];
}

class PrescriptionFailure extends PrescriptionState {
  final String errorMessage;

  const PrescriptionFailure(this.errorMessage);

  @override
  List<Object?> get props => [errorMessage];
}
