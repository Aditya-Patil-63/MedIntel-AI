import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/reference/editable_measurement.dart';
import '../../models/reference/patient_context.dart';
import '../../state/verification/verification_cubit.dart';
import '../../state/verification/verification_state.dart';
import '../../widgets/disclaimer_banner.dart';
import '../../widgets/measurement_edit_dialog.dart';
import '../../widgets/verification_status_chip.dart';
import '../results/results_screen.dart';

/// Accessible screen for reviewing, editing, and verifying clinical measurements.
class VerificationScreen extends StatefulWidget {
  const VerificationScreen({super.key});

  @override
  State<VerificationScreen> createState() => _VerificationScreenState();
}

class _VerificationScreenState extends State<VerificationScreen> {
  late final TextEditingController _ageController;
  String? _selectedSex;

  @override
  void initState() {
    super.initState();
    final currentCtx = context.read<VerificationCubit>().state.patientContext;
    _ageController = TextEditingController(
      text: currentCtx.age != null ? currentCtx.age!.toString() : '',
    );
    _selectedSex = currentCtx.sex;
  }

  @override
  void dispose() {
    _ageController.dispose();
    super.dispose();
  }

  void _onContextChanged() {
    final ageVal = double.tryParse(_ageController.text.trim());
    final newCtx = PatientContext(age: ageVal, sex: _selectedSex);
    context.read<VerificationCubit>().updatePatientContext(newCtx);
  }

  void _showAddDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (_) => MeasurementEditDialog(
        onSave: (name, val, unit) {
          context.read<VerificationCubit>().addMeasurement(
                testName: name,
                value: val,
                unit: unit,
              );
        },
      ),
    );
  }

  void _showEditDialog(BuildContext context, EditableMeasurement item) {
    showDialog(
      context: context,
      builder: (_) => MeasurementEditDialog(
        measurement: item,
        onSave: (name, val, unit) {
          context.read<VerificationCubit>().updateMeasurement(
                item.id,
                testName: name,
                value: val,
                unit: unit,
              );
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('User Verification Gate'),
        actions: [
          IconButton(
            icon: const Icon(Icons.add),
            tooltip: 'Add Measurement',
            onPressed: () => _showAddDialog(context),
          ),
        ],
      ),
      body: SafeArea(
        child: Column(
          children: [
            Expanded(
              child: SingleChildScrollView(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // 1. Mandatory Educational Disclaimer Banner
                    const DisclaimerBanner(),
                    const SizedBox(height: 12),

                    // 2. Patient Context Demographic Input Card
                    _buildPatientContextCard(),
                    const SizedBox(height: 16),

                    // 3. Verification State & Summary
                    BlocBuilder<VerificationCubit, VerificationState>(
                      builder: (context, state) {
                        if (state.isParsing) {
                          return const Card(
                            child: Padding(
                              padding: EdgeInsets.all(24),
                              child: Center(
                                child: Column(
                                  children: [
                                    CircularProgressIndicator(),
                                    SizedBox(height: 12),
                                    Text('Parsing clinical measurements...'),
                                  ],
                                ),
                              ),
                            ),
                          );
                        }

                        if (state.errorMessage != null) {
                          return Container(
                            width: double.infinity,
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: AppColors.criticalBg,
                              borderRadius: BorderRadius.circular(8),
                              border: Border.all(color: AppColors.critical),
                            ),
                            child: Text(
                              state.errorMessage!,
                              style: const TextStyle(
                                color: AppColors.critical,
                                fontSize: 13,
                                fontWeight: FontWeight.w500,
                              ),
                            ),
                          );
                        }

                        return _buildSummaryChips(state);
                      },
                    ),
                    const SizedBox(height: 12),

                    // 4. Interactive List of Editable Measurements
                    BlocBuilder<VerificationCubit, VerificationState>(
                      builder: (context, state) {
                        if (state.isParsing) return const SizedBox.shrink();

                        if (state.measurements.isEmpty) {
                          return Center(
                            child: Padding(
                              padding: const EdgeInsets.symmetric(vertical: 40),
                              child: Column(
                                children: [
                                  const Icon(Icons.playlist_add,
                                      size: 48, color: AppColors.textMuted),
                                  const SizedBox(height: 12),
                                  const Text(
                                    'No measurements found in report.',
                                    style: TextStyle(
                                        fontSize: 15,
                                        fontWeight: FontWeight.bold),
                                  ),
                                  const SizedBox(height: 6),
                                  const Text(
                                    'Tap below to add a measurement manually.',
                                    style: TextStyle(
                                        color: AppColors.textSecondary,
                                        fontSize: 13),
                                  ),
                                  const SizedBox(height: 16),
                                  ElevatedButton.icon(
                                    icon: const Icon(Icons.add),
                                    label: const Text('Add Measurement'),
                                    onPressed: () => _showAddDialog(context),
                                  ),
                                ],
                              ),
                            ),
                          );
                        }

                        return ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: state.measurements.length,
                          separatorBuilder: (_, _) => const SizedBox(height: 8),
                          itemBuilder: (context, index) {
                            final item = state.measurements[index];
                            return _buildMeasurementTile(context, item);
                          },
                        );
                      },
                    ),
                  ],
                ),
              ),
            ),

            // 5. Sticky Confirmation Action Bar
            _buildConfirmationBar(context),
          ],
        ),
      ),
    );
  }

  Widget _buildPatientContextCard() {
    return Card(
      elevation: 0,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(10),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.person_outline, size: 18, color: AppColors.primary),
                SizedBox(width: 6),
                Text(
                  'Patient Context (Optional)',
                  style: TextStyle(
                    fontWeight: FontWeight.bold,
                    fontSize: 14,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Row(
              children: [
                Expanded(
                  flex: 2,
                  child: TextFormField(
                    controller: _ageController,
                    decoration: const InputDecoration(
                      labelText: 'Age (years)',
                      hintText: 'e.g. 45',
                      isDense: true,
                      border: OutlineInputBorder(),
                    ),
                    keyboardType:
                        const TextInputType.numberWithOptions(decimal: true),
                    onChanged: (_) => _onContextChanged(),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  flex: 2,
                  child: DropdownButtonFormField<String>(
                    initialValue: _selectedSex,
                    decoration: const InputDecoration(
                      labelText: 'Sex',
                      isDense: true,
                      border: OutlineInputBorder(),
                    ),
                    items: const [
                      DropdownMenuItem(value: null, child: Text('Unspecified')),
                      DropdownMenuItem(value: 'M', child: Text('Male (M)')),
                      DropdownMenuItem(value: 'F', child: Text('Female (F)')),
                    ],
                    onChanged: (val) {
                      setState(() => _selectedSex = val);
                      _onContextChanged();
                    },
                  ),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildSummaryChips(VerificationState state) {
    return Card(
      elevation: 0,
      color: const Color(0xFFF8FAFC),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: const BorderSide(color: AppColors.divider),
      ),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
        child: Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          children: [
            Text(
              '${state.measurements.length} Measurements',
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            Row(
              children: [
                if (state.unverifiedCount > 0)
                  _buildCountBadge(
                      state.unverifiedCount, 'Unverified', AppColors.highBg, AppColors.high),
                if (state.correctedCount > 0)
                  _buildCountBadge(
                      state.correctedCount, 'Corrected', AppColors.lowBg, AppColors.low),
                if (state.confirmedCount > 0)
                  _buildCountBadge(
                      state.confirmedCount, 'Confirmed', AppColors.normalBg, AppColors.normal),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildCountBadge(int count, String label, Color bg, Color fg) {
    return Container(
      margin: const EdgeInsets.only(left: 6),
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(4),
      ),
      child: Text(
        '$count $label',
        style: TextStyle(fontSize: 11, fontWeight: FontWeight.w600, color: fg),
      ),
    );
  }

  Widget _buildMeasurementTile(BuildContext context, EditableMeasurement item) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    item.testName,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                    ),
                  ),
                ),
                VerificationStatusChip(status: item.status),
              ],
            ),
            const SizedBox(height: 8),
            Row(
              children: [
                Text(
                  'Value: ${item.value ?? "N/A"}',
                  style: const TextStyle(fontSize: 14, fontWeight: FontWeight.w600),
                ),
                if (item.unit != null && item.unit!.isNotEmpty) ...[
                  const SizedBox(width: 6),
                  Text(
                    item.unit!,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ],
            ),
            if (item.extractedReferenceRange != null) ...[
              const SizedBox(height: 4),
              Text(
                'Report Range: ${item.extractedReferenceRange}',
                style: const TextStyle(fontSize: 11, color: AppColors.textMuted),
              ),
            ],
            const Divider(height: 16),
            Row(
              mainAxisAlignment: MainAxisAlignment.end,
              children: [
                TextButton.icon(
                  icon: const Icon(Icons.delete_outline, size: 18, color: AppColors.critical),
                  label: const Text('Remove', style: TextStyle(color: AppColors.critical)),
                  onPressed: () =>
                      context.read<VerificationCubit>().removeMeasurement(item.id),
                ),
                const SizedBox(width: 8),
                TextButton.icon(
                  icon: const Icon(Icons.edit, size: 18, color: AppColors.primary),
                  label: const Text('Edit Value'),
                  onPressed: () => _showEditDialog(context, item),
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildConfirmationBar(BuildContext context) {
    return BlocBuilder<VerificationCubit, VerificationState>(
      builder: (context, state) {
        final canConfirm = state.measurements.isNotEmpty;

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.all(16),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 10,
                offset: const Offset(0, -2),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (state.isVerified)
                const Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(Icons.check_circle, color: AppColors.normal, size: 18),
                      SizedBox(width: 6),
                      Text(
                        'Verified & Confirmed by User',
                        style: TextStyle(
                          color: AppColors.normal,
                          fontWeight: FontWeight.bold,
                          fontSize: 13,
                        ),
                      ),
                    ],
                  ),
                ),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  icon: Icon(
                    state.isVerified ? Icons.arrow_forward : Icons.check,
                  ),
                  label: Text(
                    state.isVerified
                        ? 'Proceed to Results'
                        : 'Confirm & Analyze',
                    style: const TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor:
                        state.isVerified ? AppColors.secondary : AppColors.primary,
                  ),
                  onPressed: canConfirm
                      ? () {
                          if (!state.isVerified) {
                            final success = context
                                .read<VerificationCubit>()
                                .confirmVerification();
                            if (!success) return;
                          }
                          // Navigate to ResultsScreen
                          Navigator.push(
                            context,
                            MaterialPageRoute(
                              builder: (_) => const ResultsScreen(),
                            ),
                          );
                        }
                      : null,
                ),
              ),
            ],
          ),
        );
      },
    );
  }
}
