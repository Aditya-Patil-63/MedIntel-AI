import 'package:file_picker/file_picker.dart';
import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/prescription/prescription_model.dart';
import '../../services/api_service.dart';
import '../../state/prescription/prescription_cubit.dart';
import '../../state/prescription/prescription_state.dart';

/// Screen implementing Objective 2: Understanding Prescriptions.
///
/// Converts handwritten or printed doctor prescriptions into a clear,
/// patient-friendly structured table featuring:
/// 1. Medicine Name
/// 2. Purpose
/// 3. Dosage
/// 4. When to Take
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

  void _loadPreset(int index) {
    setState(() {
      if (index == 1) {
        _textController.text =
            "Rx\n1. Tab. Metformin 500mg 1-0-1 after meals\n2. Tab. Amlodipine 5mg 1-0-0 morning\n3. Tab. Atorvastatin 20mg 0-0-1 bedtime";
      } else if (index == 2) {
        _textController.text =
            "Rx\n1. Cap. Amoxicillin 625mg 1-0-1 x 5 days\n2. Tab. Paracetamol 650mg SOS after meals\n3. Cap. Pantoprazole 40mg 1-0-0 before breakfast";
      } else {
        _textController.text =
            "Rx (Handwritten)\n1. Tab. Metformin 500mg\n2. Tab. UnidentifiedMed? 2ml dose unclear\n3. Tab. Levocetirizine 5mg at night";
      }
    });
  }

  void _onExplain() {
    if (_tabController.index == 0) {
      if (_selectedFilePath == null) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(content: Text('Please select a prescription file or switch to Text mode.')),
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
          const SnackBar(content: Text('Please enter prescription text or choose a preset.')),
        );
        return;
      }
      context.read<PrescriptionCubit>().explainPrescriptionText(
            text,
            language: _selectedLanguage,
          );
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Prescription Explainer'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Reset',
            onPressed: () {
              setState(() {
                _selectedFilePath = null;
                _selectedFileName = null;
                _textController.clear();
              });
              context.read<PrescriptionCubit>().reset();
            },
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              _buildHeaderCard(),
              const SizedBox(height: 16),
              _buildLanguageSelector(),
              const SizedBox(height: 16),
              _buildInputContainer(),
              const SizedBox(height: 20),
              _buildSubmitButton(),
              const SizedBox(height: 24),
              _buildStateContent(),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildHeaderCard() {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: AppColors.primarySurface,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.primaryContainer),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                decoration: BoxDecoration(
                  color: AppColors.primary,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text(
                  'OBJECTIVE 2',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 10,
                    fontWeight: FontWeight.bold,
                    letterSpacing: 0.5,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              const Text(
                'Understanding Prescriptions',
                style: TextStyle(
                  fontSize: 15,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primaryDark,
                ),
              ),
            ],
          ),
          const SizedBox(height: 8),
          const Text(
            'Upload a prescription photo or enter medicine names. MedIntel AI deciphers doctors\' handwriting, uses Gemini AI integration to explain each medicine, and organizes everything in a clear 4-column schedule table.',
            style: TextStyle(
              fontSize: 12,
              color: AppColors.textSecondary,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildLanguageSelector() {
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
                  if (val != null) {
                    setState(() {
                      _selectedLanguage = val;
                    });
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
                      : Icons.add_photo_alternate_rounded,
                  size: 40,
                  color: _selectedFilePath != null
                      ? AppColors.normal
                      : AppColors.primary,
                ),
                const SizedBox(height: 10),
                Text(
                  _selectedFileName ?? 'Tap to Select Prescription Image or PDF',
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
                  'Supports JPG, PNG, and PDF doctor prescriptions',
                  style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildTextTab() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        TextField(
          controller: _textController,
          maxLines: 4,
          decoration: InputDecoration(
            hintText: 'Enter prescription lines e.g.:\nTab. Metformin 500mg 1-0-1\nTab. Amlodipine 5mg',
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(10),
              borderSide: const BorderSide(color: AppColors.divider),
            ),
            contentPadding: const EdgeInsets.all(12),
          ),
          style: const TextStyle(fontSize: 13),
        ),
        const SizedBox(height: 10),
        const Text(
          'Quick Demonstration Presets:',
          style: TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.bold,
            color: AppColors.textSecondary,
          ),
        ),
        const SizedBox(height: 6),
        Wrap(
          spacing: 8,
          runSpacing: 6,
          children: [
            ActionChip(
              avatar: const Icon(Icons.favorite_outline, size: 14, color: AppColors.primary),
              label: const Text('Chronic (BP/Diabetes)', style: TextStyle(fontSize: 11)),
              onPressed: () => _loadPreset(1),
            ),
            ActionChip(
              avatar: const Icon(Icons.medication_outlined, size: 14, color: AppColors.secondary),
              label: const Text('Infection (Antibiotics)', style: TextStyle(fontSize: 11)),
              onPressed: () => _loadPreset(2),
            ),
            ActionChip(
              avatar: const Icon(Icons.warning_amber_rounded, size: 14, color: AppColors.warning),
              label: const Text('Handwritten (Safety Flag)', style: TextStyle(fontSize: 11)),
              onPressed: () => _loadPreset(3),
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildSubmitButton() {
    return BlocBuilder<PrescriptionCubit, PrescriptionState>(
      builder: (context, state) {
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
                : const Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.table_chart_rounded, size: 20),
                      SizedBox(width: 8),
                      Text(
                        'Explain Prescription (Objective 2)',
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.bold),
                      ),
                    ],
                  ),
          ),
        );
      },
    );
  }

  Widget _buildStateContent() {
    return BlocBuilder<PrescriptionCubit, PrescriptionState>(
      builder: (context, state) {
        if (state is PrescriptionLoading) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.symmetric(vertical: 32),
              child: Column(
                children: [
                  const CircularProgressIndicator(color: AppColors.primary),
                  const SizedBox(height: 14),
                  Text(
                    state.message,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
          );
        }

        if (state is PrescriptionFailure) {
          return Container(
            width: double.infinity,
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: AppColors.criticalBg,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: AppColors.criticalBorder),
            ),
            child: Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Icon(Icons.error_outline_rounded, color: AppColors.critical, size: 22),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Unable to Process Prescription',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.bold,
                          color: AppColors.critical,
                        ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        state.errorMessage,
                        style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          );
        }

        if (state is PrescriptionSuccess) {
          return _buildPrescriptionResults(state.response);
        }

        return const SizedBox.shrink();
      },
    );
  }

  Widget _buildPrescriptionResults(PrescriptionExplainResponse response) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Table Header Card
        Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
          decoration: BoxDecoration(
            color: AppColors.primaryDark,
            borderRadius: BorderRadius.circular(12),
          ),
          child: Row(
            children: [
              const Icon(Icons.medication_liquid_rounded, color: Colors.white, size: 20),
              const SizedBox(width: 8),
              const Expanded(
                child: Text(
                  'Prescribed Medication Schedule Table',
                  style: TextStyle(
                    color: Colors.white,
                    fontSize: 14,
                    fontWeight: FontWeight.bold,
                  ),
                ),
              ),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: Colors.white.withValues(alpha: 0.2),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Text(
                  '${response.medicines.length} Medicines',
                  style: const TextStyle(color: Colors.white, fontSize: 11),
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 12),

        // 4-Column Structured Table
        _buildStructuredTable(response.medicines),
        const SizedBox(height: 16),

        // Clinical Safety Notice Banner
        _buildSafetyDisclaimerBanner(response.disclaimer),
        const SizedBox(height: 16),

        // Questions for Doctor
        if (response.questionsForDoctor.isNotEmpty)
          _buildQuestionsCard(response.questionsForDoctor),
        const SizedBox(height: 16),

        // General Guidance
        if (response.generalGuidance.isNotEmpty)
          _buildGuidanceCard(response.generalGuidance),
      ],
    );
  }

  Widget _buildStructuredTable(List<PrescribedMedicineItem> medicines) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(12),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: ConstrainedBox(
            constraints: const BoxConstraints(minWidth: 600),
            child: DataTable(
              headingRowColor: WidgetStateProperty.all(AppColors.primarySurface),
              headingTextStyle: const TextStyle(
                fontWeight: FontWeight.bold,
                fontSize: 12,
                color: AppColors.primaryDark,
              ),
              dataRowMinHeight: 70,
              dataRowMaxHeight: 110,
              columnSpacing: 16,
              columns: const [
                DataColumn(
                  label: Text('Medicine Name'),
                  tooltip: 'The identified medicine name',
                ),
                DataColumn(
                  label: Text('Purpose'),
                  tooltip: 'A simple explanation of what the medicine is used for',
                ),
                DataColumn(
                  label: Text('Dosage'),
                  tooltip: 'The prescribed dose, such as 2 ml or 1 tablet',
                ),
                DataColumn(
                  label: Text('When to Take'),
                  tooltip: 'The prescribed timing, such as before meals, after meals, or at bedtime',
                ),
              ],
              rows: medicines.map((med) {
                final isFlagged = med.needsConfirmation;

                return DataRow(
                  color: WidgetStateProperty.resolveWith<Color?>(
                    (states) => isFlagged ? const Color(0xFFFFFBEB) : null,
                  ),
                  cells: [
                    // 1. Medicine Name
                    DataCell(
                      SizedBox(
                        width: 150,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              med.displayMedicineName,
                              style: const TextStyle(
                                fontWeight: FontWeight.bold,
                                fontSize: 13,
                                color: AppColors.textPrimary,
                              ),
                            ),
                            if (med.genericName != null &&
                                med.genericName!.isNotEmpty)
                              Text(
                                med.genericName!,
                                style: const TextStyle(
                                  fontSize: 10,
                                  color: AppColors.textSecondary,
                                ),
                                maxLines: 1,
                                overflow: TextOverflow.ellipsis,
                              ),
                            if (isFlagged)
                              Padding(
                                padding: const EdgeInsets.only(top: 4),
                                child: Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 6,
                                    vertical: 2,
                                  ),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFFEF3C7),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                      color: const Color(0xFFF59E0B),
                                    ),
                                  ),
                                  child: const Text(
                                    '⚠️ Confirm with Pharmacist',
                                    style: TextStyle(
                                      fontSize: 9,
                                      fontWeight: FontWeight.bold,
                                      color: Color(0xFFB45309),
                                    ),
                                  ),
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),

                    // 2. Purpose
                    DataCell(
                      SizedBox(
                        width: 170,
                        child: Text(
                          med.purpose,
                          style: const TextStyle(
                            fontSize: 12,
                            color: AppColors.textPrimary,
                            height: 1.3,
                          ),
                          maxLines: 4,
                          overflow: TextOverflow.ellipsis,
                        ),
                      ),
                    ),

                    // 3. Dosage
                    DataCell(
                      SizedBox(
                        width: 110,
                        child: Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 8,
                            vertical: 5,
                          ),
                          decoration: BoxDecoration(
                            color: AppColors.primarySurface,
                            borderRadius: BorderRadius.circular(6),
                            border: Border.all(color: AppColors.primaryContainer),
                          ),
                          child: Text(
                            med.displayDosage,
                            style: const TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: AppColors.primaryDark,
                            ),
                            textAlign: TextAlign.center,
                          ),
                        ),
                      ),
                    ),

                    // 4. When to Take
                    DataCell(
                      SizedBox(
                        width: 170,
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          mainAxisAlignment: MainAxisAlignment.center,
                          children: [
                            Text(
                              med.displayWhenToTake,
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.bold,
                                color: AppColors.textPrimary,
                              ),
                              maxLines: 3,
                              overflow: TextOverflow.ellipsis,
                            ),
                            if (med.instructions.isNotEmpty)
                              Padding(
                                padding: const EdgeInsets.only(top: 2),
                                child: Text(
                                  med.instructions,
                                  style: const TextStyle(
                                    fontSize: 10,
                                    color: AppColors.textSecondary,
                                  ),
                                  maxLines: 2,
                                  overflow: TextOverflow.ellipsis,
                                ),
                              ),
                          ],
                        ),
                      ),
                    ),
                  ],
                );
              }).toList(),
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildSafetyDisclaimerBanner(String disclaimer) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFFEFF6FF), // Calm Soft Blue Tint
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFFBFDBFE)),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.shield_outlined,
            color: Color(0xFF1D4ED8),
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text(
                  'Important Safety & Clinical Guidance',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.bold,
                    color: Color(0xFF1E3A8A),
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  disclaimer,
                  style: const TextStyle(
                    fontSize: 11,
                    color: Color(0xFF1E40AF),
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
              Icon(Icons.help_outline_rounded, color: AppColors.primary, size: 18),
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
                  const Text('• ', style: TextStyle(color: AppColors.primary, fontWeight: FontWeight.bold)),
                  Expanded(
                    child: Text(
                      q,
                      style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
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
              Icon(Icons.info_outline_rounded, color: AppColors.secondary, size: 18),
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
            style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
          ),
        ],
      ),
    );
  }
}
