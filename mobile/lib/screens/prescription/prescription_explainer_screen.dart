import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/history/prescription_history_item.dart';
import '../../models/prescription/prescription_model.dart';
import '../../services/api_service.dart';
import '../../state/history/history_cubit.dart';
import '../../state/prescription/prescription_cubit.dart';
import '../../state/prescription/prescription_state.dart';

/// Screen implementing Objective 2: Understanding Prescriptions.
///
/// Converts handwritten or printed doctor prescriptions into clear,
/// patient-friendly structured medicine cards featuring:
/// - Medicine Name & Generic Name
/// - Purpose
/// - Dosage
/// - Frequency
/// - Timing
/// - Duration
/// - Instructions
///
/// Enforces mandatory medical safety boundaries:
/// - Low-confidence or uncatalogued extractions flag pharmacist/doctor confirmation.
/// - Gemini-generated details never override doctor's instructions.
class PrescriptionExplainerScreen extends StatelessWidget {
  const PrescriptionExplainerScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return BlocProvider(
      create: (ctx) => PrescriptionCubit(apiService: ctx.read<ApiService>()),
      child: const _PrescriptionExplainerView(),
    );
  }
}

class _PrescriptionExplainerView extends StatefulWidget {
  const _PrescriptionExplainerView();

  @override
  State<_PrescriptionExplainerView> createState() =>
      _PrescriptionExplainerViewState();
}

class _PrescriptionExplainerViewState extends State<_PrescriptionExplainerView>
    with SingleTickerProviderStateMixin {
  late TabController _tabController;
  final TextEditingController _textController = TextEditingController();

  String _selectedLanguage = 'english';
  String? _selectedFilePath;
  String? _selectedFileName;
  String? _lastSavedRxId;

  void _autoSavePrescription(PrescriptionExplainResponse response) {
    if (response.medicines.isEmpty) return;
    final rxId =
        'rx_${response.medicines.map((m) => m.name).join("_").hashCode.abs()}';
    if (_lastSavedRxId == rxId) return;
    _lastSavedRxId = rxId;

    final historyItem = PrescriptionHistoryItem.fromResponse(
      id: rxId,
      response: response,
      documentName: _selectedFileName ?? 'Prescription Note',
      imageReference: _selectedFilePath,
    );

    try {
      context.read<HistoryCubit>().addPrescription(historyItem);
    } catch (_) {}
  }

  static const List<Map<String, String>> _languages = [
    {'code': 'english', 'label': 'English'},
    {'code': 'hindi', 'label': 'हिन्दी (Hindi)'},
    {'code': 'marathi', 'label': 'मराठी (Marathi)'},
    {'code': 'gujarati', 'label': 'ગુજરાતી (Gujarati)'},
  ];

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
  }

  @override
  void dispose() {
    _tabController.dispose();
    _textController.dispose();
    super.dispose();
  }

  Future<void> _pickPrescriptionFile() async {
    try {
      final result = await FilePicker.platform.pickFiles(
        type: FileType.custom,
        allowedExtensions: ['pdf', 'png', 'jpg', 'jpeg'],
      );

      if (result != null && result.files.single.path != null) {
        setState(() {
          _selectedFilePath = result.files.single.path;
          _selectedFileName = result.files.single.name;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('File selection error: $e')),
        );
      }
    }
  }

  void _onExplain() {
    if (_tabController.index == 0) {
      if (_selectedFilePath == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Please select a prescription file or switch to Text mode.'),
          ),
        );
        return;
      }
      context.read<PrescriptionCubit>().uploadAndExplainPrescriptionFile(
            _selectedFilePath!,
            language: _selectedLanguage,
          );
    } else {
      final text = _textController.text.trim();
      if (text.isEmpty) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please enter prescription text.')),
        );
        return;
      }
      context.read<PrescriptionCubit>().explainPrescriptionText(
            text,
            language: _selectedLanguage,
          );
    }
  }

  void _onLanguageChanged(String newLang, PrescriptionState state) {
    setState(() {
      _selectedLanguage = newLang;
    });

    if (state is PrescriptionSuccess) {
      if (_selectedFilePath != null) {
        context.read<PrescriptionCubit>().uploadAndExplainPrescriptionFile(
              _selectedFilePath!,
              language: newLang,
            );
      } else if (_textController.text.trim().isNotEmpty) {
        context.read<PrescriptionCubit>().explainPrescriptionText(
              _textController.text.trim(),
              language: newLang,
            );
      } else if (state.response.medicines.isNotEmpty) {
        context.read<PrescriptionCubit>().explainPrescriptionMedicines(
              state.response.medicines.map((m) => m.name).toList(),
              language: newLang,
            );
      }
    }
  }

  void _onReset() {
    setState(() {
      _selectedFilePath = null;
      _selectedFileName = null;
      _textController.clear();
      _lastSavedRxId = null;
    });
    context.read<PrescriptionCubit>().reset();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Prescription Explainer'),
      ),
      body: SafeArea(
        child: BlocConsumer<PrescriptionCubit, PrescriptionState>(
          listener: (context, state) {
            if (state is PrescriptionSuccess) {
              _autoSavePrescription(state.response);
            }
          },
          builder: (context, state) {
            return SingleChildScrollView(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  _buildLanguageSelector(state),
                  const SizedBox(height: 16),
                  if (state is PrescriptionSuccess)
                    _buildPrescriptionResults(state.response)
                  else ...[
                    _buildInputContainer(),
                    const SizedBox(height: 20),
                    _buildSubmitButton(state),
                    if (state is PrescriptionLoading ||
                        state is PrescriptionFailure) ...[
                      const SizedBox(height: 24),
                      _buildStateContent(state),
                    ],
                  ],
                ],
              ),
            );
          },
        ),
      ),
    );
  }

  Widget _buildLanguageSelector(PrescriptionState state) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          const Icon(Icons.translate_rounded, size: 20, color: AppColors.primary),
          const SizedBox(width: 10),
          const Text(
            'Language:',
            style: TextStyle(fontSize: 13, fontWeight: FontWeight.bold),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: DropdownButtonHideUnderline(
              child: DropdownButton<String>(
                value: _selectedLanguage,
                isDense: true,
                items: _languages.map((l) {
                  return DropdownMenuItem<String>(
                    value: l['code'],
                    child: Text(
                      l['label']!,
                      style: const TextStyle(fontSize: 13),
                    ),
                  );
                }).toList(),
                onChanged: (val) {
                  if (val != null && val != _selectedLanguage) {
                    _onLanguageChanged(val, state);
                  }
                },
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildInputContainer() {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: [
          TabBar(
            controller: _tabController,
            labelColor: AppColors.primary,
            unselectedLabelColor: AppColors.textSecondary,
            indicatorColor: AppColors.primary,
            indicatorWeight: 3,
            tabs: const [
              Tab(
                icon: Icon(Icons.document_scanner_rounded, size: 20),
                text: 'Photo / PDF Upload',
              ),
              Tab(
                icon: Icon(Icons.edit_note_rounded, size: 20),
                text: 'Prescription Text',
              ),
            ],
            onTap: (_) => setState(() {}),
          ),
          const Divider(height: 1, color: AppColors.divider),
          Padding(
            padding: const EdgeInsets.all(16),
            child: _tabController.index == 0
                ? _buildUploadTab()
                : _buildTextTab(),
          ),
        ],
      ),
    );
  }

  Widget _buildUploadTab() {
    return Column(
      children: [
        InkWell(
          onTap: _pickPrescriptionFile,
          borderRadius: BorderRadius.circular(12),
          child: Container(
            width: double.infinity,
            padding: const EdgeInsets.symmetric(vertical: 24, horizontal: 16),
            decoration: BoxDecoration(
              color: AppColors.background,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: _selectedFilePath != null
                    ? AppColors.primary
                    : AppColors.divider,
                style: BorderStyle.solid,
                width: _selectedFilePath != null ? 2 : 1,
              ),
            ),
            child: Column(
              children: [
                Icon(
                  _selectedFilePath != null
                      ? Icons.check_circle_rounded
                      : Icons.upload_file_rounded,
                  size: 44,
                  color: _selectedFilePath != null
                      ? AppColors.normal
                      : AppColors.primary,
                ),
                const SizedBox(height: 10),
                Text(
                  _selectedFileName ?? 'Upload Prescription Image or PDF',
                  style: TextStyle(
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                    color: _selectedFilePath != null
                        ? AppColors.textPrimary
                        : AppColors.primary,
                  ),
                  textAlign: TextAlign.center,
                ),
                const SizedBox(height: 4),
                const Text(
                  'Supports PDF, PNG, JPG, JPEG',
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTextTab() {
    return TextField(
      controller: _textController,
      minLines: 5,
      maxLines: 8,
      decoration: InputDecoration(
        hintText: 'Enter prescription details here...',
        hintStyle: const TextStyle(
          color: AppColors.textSecondary,
          fontSize: 13,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.divider),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: AppColors.primary, width: 1.5),
        ),
        contentPadding: const EdgeInsets.all(14),
      ),
      style: const TextStyle(fontSize: 13, height: 1.4),
    );
  }

  Widget _buildSubmitButton(PrescriptionState state) {
    final isLoading = state is PrescriptionLoading;

    return SizedBox(
      width: double.infinity,
      height: 48,
      child: ElevatedButton(
        onPressed: isLoading ? null : _onExplain,
        style: ElevatedButton.styleFrom(
          backgroundColor: AppColors.primary,
          foregroundColor: Colors.white,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(12),
          ),
          elevation: 0,
        ),
        child: isLoading
            ? const Row(
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  SizedBox(
                    width: 18,
                    height: 18,
                    child: CircularProgressIndicator(
                      strokeWidth: 2,
                      color: Colors.white,
                    ),
                  ),
                  SizedBox(width: 12),
                  Text('Deciphering & Analyzing...'),
                ],
              )
            : const Text(
                'Explain Prescription',
                style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
              ),
      ),
    );
  }

  Widget _buildStateContent(PrescriptionState state) {
    if (state is PrescriptionLoading) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Column(
            children: [
              const CircularProgressIndicator(color: AppColors.primary),
              const SizedBox(height: 14),
              Text(
                state.message,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
                textAlign: TextAlign.center,
              ),
              const SizedBox(height: 6),
              const Text(
                'Waking up the server, this can take up to a minute...',
                style: TextStyle(
                  fontSize: 12,
                  color: AppColors.textSecondary,
                  fontStyle: FontStyle.italic,
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      );
    }

    if (state is PrescriptionFailure) {
      return Container(
        width: double.infinity,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: AppColors.criticalBg,
          borderRadius: BorderRadius.circular(12),
          border: Border.all(color: AppColors.criticalBorder),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.error_outline_rounded,
                    color: AppColors.critical, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Unable to Process Prescription',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.bold,
                          color: AppColors.critical,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        state.errorMessage,
                        style: const TextStyle(
                            fontSize: 12, color: AppColors.textPrimary, height: 1.3),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 14),
            ElevatedButton.icon(
              icon: const Icon(Icons.refresh_rounded, size: 18),
              label: const Text('Retry'),
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.critical,
                foregroundColor: Colors.white,
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                ),
              ),
              onPressed: _onExplain,
            ),
          ],
        ),
      );
    }

    return const SizedBox.shrink();
  }

  Widget _buildPrescriptionResults(PrescriptionExplainResponse response) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Doctor Notes / Clinical Advice (if available and informative)
        if (response.doctorNotes != null &&
            response.doctorNotes!.isNotEmpty &&
            !response.doctorNotes!
                .toLowerCase()
                .contains('prescriptions reviewed and structured')) ...[
          _buildDoctorNotesCard(response.doctorNotes!),
          const SizedBox(height: 16),
        ],

        // Medicine Detail Cards (One responsive card per medicine)
        ...response.medicines.map(_buildMedicineCard),
        const SizedBox(height: 8),

        // Questions to Ask Your Doctor or Pharmacist
        if (response.questionsForDoctor.isNotEmpty) ...[
          _buildQuestionsCard(response.questionsForDoctor),
          const SizedBox(height: 16),
        ],

        // General Medication Guidelines
        if (response.generalGuidance.isNotEmpty) ...[
          _buildGuidanceCard(response.generalGuidance),
          const SizedBox(height: 16),
        ],

        // Subtle, unobtrusive educational disclaimer
        Padding(
          padding: const EdgeInsets.symmetric(horizontal: 4, vertical: 8),
          child: Text(
            response.disclaimer,
            style: const TextStyle(
              fontSize: 11,
              color: AppColors.textSecondary,
              height: 1.4,
            ),
            textAlign: TextAlign.center,
          ),
        ),
        const SizedBox(height: 16),

        // Analyze Another Prescription Action Button
        SizedBox(
          width: double.infinity,
          height: 48,
          child: OutlinedButton.icon(
            onPressed: _onReset,
            icon: const Icon(Icons.add_circle_outline_rounded, size: 20),
            label: const Text(
              'Analyze Another Prescription',
              style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
            ),
            style: OutlinedButton.styleFrom(
              foregroundColor: AppColors.primary,
              side: const BorderSide(color: AppColors.primary, width: 1.5),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(12),
              ),
            ),
          ),
        ),
        const SizedBox(height: 16),
      ],
    );
  }

  Widget _buildMedicineCard(PrescribedMedicineItem med) {
    final isFlagged = med.needsConfirmation;

    return Container(
      width: double.infinity,
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(
          color: isFlagged ? const Color(0xFFFCD34D) : AppColors.divider,
          width: isFlagged ? 1.5 : 1,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Medicine Icon + Name & Generic Name
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: isFlagged
                      ? const Color(0xFFFEF3C7)
                      : AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(8),
                ),
                child: Icon(
                  Icons.medication_rounded,
                  color: isFlagged ? const Color(0xFFD97706) : AppColors.primary,
                  size: 22,
                ),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Medicine Name',
                      style: const TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textSecondary,
                        letterSpacing: 0.5,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      med.displayMedicineName,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    if (med.genericName != null &&
                        med.genericName!.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        med.genericName!,
                        style: const TextStyle(
                          fontSize: 12,
                          color: AppColors.textSecondary,
                          fontStyle: FontStyle.italic,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ],
          ),

          // Pharmacist / Doctor confirmation badge when ambiguous
          if (isFlagged) ...[
            const SizedBox(height: 10),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
              decoration: BoxDecoration(
                color: const Color(0xFFFEF3C7),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFFF59E0B)),
              ),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Icon(Icons.warning_amber_rounded,
                      color: Color(0xFFB45309), size: 16),
                  const SizedBox(width: 6),
                  Expanded(
                    child: Text(
                      med.confidenceNote ??
                          '⚠️ Confirm with Pharmacist or Doctor before taking.',
                      style: const TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: Color(0xFF92400E),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],

          const SizedBox(height: 12),
          const Divider(height: 1, color: AppColors.divider),
          const SizedBox(height: 12),

          // Purpose
          _buildInfoRow('Purpose', med.purpose),
          const SizedBox(height: 10),

          // Dosage & Frequency
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _buildInfoRow('Dosage', med.displayDosage),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildInfoRow('Frequency', med.displayFrequency),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Timing & Duration
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Expanded(
                child: _buildInfoRow('When to Take / Timing', med.displayTiming),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: _buildInfoRow('Duration', med.displayDuration),
              ),
            ],
          ),
          const SizedBox(height: 10),

          // Instructions
          _buildInfoRow('Instructions', med.displayInstructions),

          if (med.precautions != null && med.precautions!.isNotEmpty) ...[
            const SizedBox(height: 10),
            _buildInfoRow('Precautions', med.precautions!),
          ],
        ],
      ),
    );
  }

  Widget _buildInfoRow(String label, String value) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          label,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.bold,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 2),
        Text(
          value.isEmpty ? 'Not specified' : value,
          style: const TextStyle(
            fontSize: 13,
            color: AppColors.textPrimary,
            height: 1.3,
          ),
        ),
      ],
    );
  }

  Widget _buildDoctorNotesCard(String doctorNotes) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF0FDF4),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFBBF7D0)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(Icons.medical_information_outlined,
              color: Color(0xFF16A34A), size: 20),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Doctor Notes & Clinical Advice',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF15803D),
                  ),
                ),
                const SizedBox(height: 4),
                Text(
                  doctorNotes,
                  style: const TextStyle(
                    fontSize: 12,
                    color: Color(0xFF166534),
                    height: 1.35,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildQuestionsCard(List<String> questions) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.help_outline_rounded,
                  color: AppColors.primary, size: 18),
              SizedBox(width: 8),
              Text(
                'Questions to Ask Your Doctor or Pharmacist',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          ...questions.map(
            (q) => Padding(
              padding: const EdgeInsets.only(bottom: 6),
              child: Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('• ',
                      style: TextStyle(
                          color: AppColors.primary,
                          fontWeight: FontWeight.bold)),
                  Expanded(
                    child: Text(
                      q,
                      style: const TextStyle(
                          fontSize: 12, color: AppColors.textSecondary),
                    ),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGuidanceCard(String guidance) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.info_outline_rounded,
                  color: AppColors.secondary, size: 18),
              SizedBox(width: 8),
              Text(
                'General Medication Guidelines',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textPrimary,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          Text(
            guidance,
            style: const TextStyle(
                fontSize: 12, color: AppColors.textSecondary, height: 1.4),
          ),
        ],
      ),
    );
  }
}
