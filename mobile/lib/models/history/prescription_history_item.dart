import 'package:equatable/equatable.dart';
import '../../core/utils/date_formatter.dart';
import '../prescription/prescription_model.dart';

/// Strongly typed, immutable snapshot representing a viewed or analyzed prescription in history.
class PrescriptionHistoryItem extends Equatable {
  final String id;
  final DateTime createdAt;
  final DateTime? updatedAt;
  final String title;
  final String documentName;
  final String? doctorName;
  final String? hospitalName;
  final List<PrescribedMedicineItem> medicines;
  final String? doctorNotes;
  final String generalGuidance;
  final List<String> questionsForDoctor;
  final String language;
  final String disclaimer;
  final String? imageReference;

  PrescriptionHistoryItem({
    required this.id,
    required this.createdAt,
    this.updatedAt,
    required this.title,
    required this.documentName,
    this.doctorName,
    this.hospitalName,
    required List<PrescribedMedicineItem> medicines,
    this.doctorNotes,
    this.generalGuidance = '',
    required List<String> questionsForDoctor,
    this.language = 'english',
    this.disclaimer =
        'This explanation is for educational purposes only. Always follow your prescribing doctor\'s instructions.',
    this.imageReference,
  })  : medicines = List<PrescribedMedicineItem>.unmodifiable(medicines),
        questionsForDoctor = List<String>.unmodifiable(questionsForDoctor);

  /// Factory constructor to convert from PrescriptionExplainResponse.
  factory PrescriptionHistoryItem.fromResponse({
    required String id,
    required PrescriptionExplainResponse response,
    String? title,
    String? documentName,
    String? doctorName,
    String? hospitalName,
    String? imageReference,
    DateTime? createdAt,
    DateTime? updatedAt,
  }) {
    final now = DateTime.now();
    final defaultTitle = (response.medicines.isNotEmpty)
        ? 'Prescription - ${response.medicines.map((m) => m.displayMedicineName).take(2).join(', ')}'
        : 'Prescription Note';

    return PrescriptionHistoryItem(
      id: id,
      createdAt: createdAt ?? now,
      updatedAt: updatedAt ?? now,
      title: title ?? defaultTitle,
      documentName: documentName ?? 'Prescription Note',
      doctorName: doctorName,
      hospitalName: hospitalName,
      medicines: response.medicines,
      doctorNotes: response.doctorNotes,
      generalGuidance: response.generalGuidance,
      questionsForDoctor: response.questionsForDoctor,
      language: response.language,
      disclaimer: response.disclaimer,
      imageReference: imageReference,
    );
  }

  int get medicineCount => medicines.length;

  String get medicineNamesSummary {
    if (medicines.isEmpty) return 'No medications listed';
    final names = medicines.map((m) => m.displayMedicineName).take(3).toList();
    if (medicines.length > 3) {
      return '${names.join(', ')} +${medicines.length - 3} more';
    }
    return names.join(', ');
  }

  String get formattedDate => formatHistoryTimestamp(updatedAt ?? createdAt);

  Map<String, dynamic> toJson() => {
        'id': id,
        'type': 'prescription',
        'created_at': createdAt.toUtc().toIso8601String(),
        if (updatedAt != null) 'updated_at': updatedAt!.toUtc().toIso8601String(),
        'title': title,
        'document_name': documentName,
        if (doctorName != null) 'doctor_name': doctorName,
        if (hospitalName != null) 'hospital_name': hospitalName,
        'medicines': medicines.map((m) => m.toJson()).toList(),
        if (doctorNotes != null) 'doctor_notes': doctorNotes,
        'general_guidance': generalGuidance,
        'questions_for_doctor': questionsForDoctor,
        'language': language,
        'disclaimer': disclaimer,
        if (imageReference != null) 'image_reference': imageReference,
      };

  factory PrescriptionHistoryItem.fromJson(Map<String, dynamic> json) {
    final rawMedicines = json['medicines'] as List<dynamic>? ?? [];
    final items = rawMedicines
        .map((e) => PrescribedMedicineItem.fromJson(e as Map<String, dynamic>))
        .toList();

    final rawQuestions = json['questions_for_doctor'] as List<dynamic>? ?? [];
    final questions = rawQuestions.map((e) => e.toString()).toList();

    final createdStr = json['created_at'] as String? ?? '';
    final updatedStr = json['updated_at'] as String?;

    return PrescriptionHistoryItem(
      id: json['id'] as String? ?? '',
      createdAt: DateTime.tryParse(createdStr) ?? DateTime.now(),
      updatedAt: updatedStr != null ? DateTime.tryParse(updatedStr) : null,
      title: json['title'] as String? ?? 'Prescription',
      documentName: json['document_name'] as String? ?? 'Prescription Note',
      doctorName: json['doctor_name'] as String?,
      hospitalName: json['hospital_name'] as String?,
      medicines: items,
      doctorNotes: json['doctor_notes'] as String?,
      generalGuidance: json['general_guidance'] as String? ?? '',
      questionsForDoctor: questions,
      language: json['language'] as String? ?? 'english',
      disclaimer: json['disclaimer'] as String? ??
          'This explanation is for educational purposes only. Always follow your prescribing doctor\'s instructions.',
      imageReference: json['image_reference'] as String?,
    );
  }

  @override
  List<Object?> get props => [
        id,
        createdAt,
        updatedAt,
        title,
        documentName,
        doctorName,
        hospitalName,
        medicines,
        doctorNotes,
        generalGuidance,
        questionsForDoctor,
        language,
        disclaimer,
        imageReference,
      ];
}
