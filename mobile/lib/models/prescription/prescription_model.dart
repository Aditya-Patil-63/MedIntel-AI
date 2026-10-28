import 'package:equatable/equatable.dart';

/// Item in the Prescription Explanation Table (Objective 2).
/// Displays:
/// - Medicine Name: The identified medicine name
/// - Purpose: Simple explanation of what the medicine is used for
/// - Dosage: Prescribed dose (e.g. 2 ml, 1 tablet, 500 mg)
/// - When to Take: Prescribed timing (Before meals, after meals, at bedtime)
/// - Safety Flag: needsConfirmation (Requires Pharmacist/Doctor Confirmation)
class PrescribedMedicineItem extends Equatable {
  final String name;
  final String? medicineName;
  final String? genericName;
  final String? dosage;
  final String? frequency;
  final String? timing;
  final String? duration;
  final String purpose;
  final String? whenToTake;
  final String schedule;
  final String instructions;
  final String? precautions;
  final bool needsConfirmation;
  final String? confidenceNote;

  const PrescribedMedicineItem({
    required this.name,
    this.medicineName,
    this.genericName,
    this.dosage,
    this.frequency,
    this.timing,
    this.duration,
    required this.purpose,
    this.whenToTake,
    this.schedule = '',
    this.instructions = '',
    this.precautions,
    this.needsConfirmation = false,
    this.confidenceNote,
  });

  String get displayMedicineName =>
      (medicineName != null && medicineName!.isNotEmpty) ? medicineName! : name;

  String get displayDosage =>
      (dosage != null && dosage!.isNotEmpty && dosage != 'As prescribed')
          ? dosage!
          : (dosage == 'As prescribed' ? 'As prescribed' : 'Not specified');

  String get displayFrequency {
    if (frequency != null && frequency!.isNotEmpty) return frequency!;
    if (schedule.isNotEmpty) return schedule;
    return 'Not specified';
  }

  String get displayTiming {
    if (timing != null && timing!.isNotEmpty) return timing!;
    if (whenToTake != null && whenToTake!.isNotEmpty) return whenToTake!;
    return 'Not specified';
  }

  String get displayDuration {
    if (duration != null && duration!.isNotEmpty) return duration!;
    return 'Not specified';
  }

  String get displayInstructions {
    if (instructions.isNotEmpty) return instructions;
    return 'Not specified';
  }

  String get displayWhenToTake {
    if (whenToTake != null && whenToTake!.isNotEmpty) {
      return whenToTake!;
    }
    if (timing != null && timing!.isNotEmpty) {
      return timing!;
    }
    if (schedule.isNotEmpty) {
      return schedule;
    }
    return 'As advised by physician';
  }

  factory PrescribedMedicineItem.fromJson(Map<String, dynamic> json) {
    return PrescribedMedicineItem(
      name: json['name'] as String? ?? json['medicine_name'] as String? ?? '',
      medicineName: json['medicine_name'] as String? ?? json['name'] as String?,
      genericName: json['generic_name'] as String?,
      dosage: json['dosage'] as String?,
      frequency: json['frequency'] as String?,
      timing: json['timing'] as String?,
      duration: json['duration'] as String?,
      purpose: json['purpose'] as String? ?? '',
      whenToTake: json['when_to_take'] as String? ?? json['timing'] as String? ?? json['schedule'] as String?,
      schedule: json['schedule'] as String? ?? json['frequency'] as String? ?? '',
      instructions: json['instructions'] as String? ?? '',
      precautions: json['precautions'] as String?,
      needsConfirmation: json['needs_confirmation'] as bool? ?? false,
      confidenceNote: json['confidence_note'] as String?,
    );
  }

  Map<String, dynamic> toJson() => {
        'name': name,
        if (medicineName != null) 'medicine_name': medicineName,
        if (genericName != null) 'generic_name': genericName,
        if (dosage != null) 'dosage': dosage,
        if (frequency != null) 'frequency': frequency,
        if (timing != null) 'timing': timing,
        if (duration != null) 'duration': duration,
        'purpose': purpose,
        if (whenToTake != null) 'when_to_take': whenToTake,
        'schedule': schedule,
        'instructions': instructions,
        if (precautions != null) 'precautions': precautions,
        'needs_confirmation': needsConfirmation,
        if (confidenceNote != null) 'confidence_note': confidenceNote,
      };

  @override
  List<Object?> get props => [
        name,
        medicineName,
        genericName,
        dosage,
        frequency,
        timing,
        duration,
        purpose,
        whenToTake,
        schedule,
        instructions,
        precautions,
        needsConfirmation,
        confidenceNote,
      ];
}

/// Request model for prescription explanation.
class PrescriptionExplainRequest extends Equatable {
  final String? prescriptionText;
  final List<String>? medicines;
  final String language;
  final bool isUserVerified;

  const PrescriptionExplainRequest({
    this.prescriptionText,
    this.medicines,
    this.language = 'english',
    this.isUserVerified = true,
  });

  Map<String, dynamic> toJson() => {
        if (prescriptionText != null) 'prescription_text': prescriptionText,
        if (medicines != null) 'medicines': medicines,
        'language': language,
        'is_user_verified': isUserVerified,
      };

  @override
  List<Object?> get props => [
        prescriptionText,
        medicines,
        language,
        isUserVerified,
      ];
}

/// Patient-friendly prescription interpretation response.
class PrescriptionExplainResponse extends Equatable {
  final String? doctorNotes;
  final List<PrescribedMedicineItem> medicines;
  final String generalGuidance;
  final List<String> questionsForDoctor;
  final String language;
  final String disclaimer;

  const PrescriptionExplainResponse({
    this.doctorNotes,
    required this.medicines,
    required this.generalGuidance,
    required this.questionsForDoctor,
    required this.language,
    required this.disclaimer,
  });

  factory PrescriptionExplainResponse.fromJson(Map<String, dynamic> json) {
    final rawMedicines = json['medicines'] as List<dynamic>? ?? [];
    final items = rawMedicines
        .map((e) => PrescribedMedicineItem.fromJson(e as Map<String, dynamic>))
        .toList();

    final rawQuestions = json['questions_for_doctor'] as List<dynamic>? ?? [];
    final questions = rawQuestions.map((e) => e.toString()).toList();

    return PrescriptionExplainResponse(
      doctorNotes: json['doctor_notes'] as String?,
      medicines: items,
      generalGuidance: json['general_guidance'] as String? ?? '',
      questionsForDoctor: questions,
      language: json['language'] as String? ?? 'english',
      disclaimer: json['disclaimer'] as String? ??
          'This explanation is for educational purposes only. Always follow your prescribing doctor\'s instructions.',
    );
  }

  Map<String, dynamic> toJson() => {
        if (doctorNotes != null) 'doctor_notes': doctorNotes,
        'medicines': medicines.map((e) => e.toJson()).toList(),
        'general_guidance': generalGuidance,
        'questions_for_doctor': questionsForDoctor,
        'language': language,
        'disclaimer': disclaimer,
      };

  @override
  List<Object?> get props => [
        doctorNotes,
        medicines,
        generalGuidance,
        questionsForDoctor,
        language,
        disclaimer,
      ];
}
