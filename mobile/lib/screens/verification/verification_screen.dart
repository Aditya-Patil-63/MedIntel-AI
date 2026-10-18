import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../models/analysis/verified_snapshot.dart';
import '../../models/reference/editable_measurement.dart';
import '../../models/reference/patient_context.dart';
import '../../state/analysis/analysis_cubit.dart';
import '../../state/verification/verification_cubit.dart';
import '../../state/verification/verification_state.dart';
import '../../widgets/disclaimer_banner.dart';
import '../../widgets/measurement_edit_dialog.dart';
import '../../widgets/verification_status_chip.dart';
import '../results/results_screen.dart';

/// Redesigned medical verification gate enforcing clinician-guided patient verification.
///
/// Features a 3-step progress tracker, clean measurement cards, patient context,
/// and clear empty state guidance.
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
    context.read<AnalysisCubit>().invalidate();
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
          context.read<AnalysisCubit>().invalidate();
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
          context.read<AnalysisCubit>().invalidate();
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
            icon: const Icon(Icons.add_rounded),
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
                    const SizedBox(height: 14),

                    // 2. 3-Step Guided Progress Tracker
                    _buildStepTracker(currentStep: 2),
                    const SizedBox(height: 16),

                    // 3. Patient Demographic Context Card (Optional)
                    _buildPatientContextCard(),
                    const SizedBox(height: 16),

                    // 4. Verification State Summary Chips
                    BlocBuilder<VerificationCubit, VerificationState>(
                      builder: (context, state) {
                        if (state.isParsing) {
                          return Container(
                            width: double.infinity,
                            padding: const EdgeInsets.all(24),
                            decoration: BoxDecoration(
                              color: Colors.white,
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(color: AppColors.divider),
                            ),
                            child: const Column(
                              children: [
                                SizedBox(
                                  width: 32,
                                  height: 32,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 3,
                                    color: AppColors.primary,
                                  ),
                                ),
                                SizedBox(height: 12),
                                Text(
                                  'Parsing clinical measurements...',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                              ],
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
                              borderRadius: BorderRadius.circular(10),
                              border:
                                  Border.all(color: AppColors.criticalBorder),
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
                    const SizedBox(height: 14),

                    // 5. Interactive List of Measurements or Empty State
                    BlocBuilder<VerificationCubit, VerificationState>(
                      builder: (context, state) {
                        if (state.isParsing) return const SizedBox.shrink();

                        if (state.measurements.isEmpty) {
                          return _buildEmptyState(context);
                        }

                        return ListView.separated(
                          shrinkWrap: true,
                          physics: const NeverScrollableScrollPhysics(),
                          itemCount: state.measurements.length,
                          separatorBuilder: (_, _) =>
                              const SizedBox(height: 10),
                          itemBuilder: (context, index) {
                            final item = state.measurements[index];
                            return _buildMeasurementTile(context, item);
                          },
                        );
                      },
                    ),
                    const SizedBox(height: 16),
                  ],
                ),
              ),
            ),

            // 6. Sticky Bottom Action Bar
            _buildConfirmationBar(context),
          ],
        ),
      ),
    );
  }

  Widget _buildStepTracker({required int currentStep}) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        children: [
          _buildStepNode(
            step: 1,
            label: 'Upload',
            isActive: false,
            isCompleted: true,
          ),
          _buildStepDivider(isCompleted: true),
          _buildStepNode(
            step: 2,
            label: 'Review Values',
            isActive: true,
            isCompleted: false,
          ),
          _buildStepDivider(isCompleted: false),
          _buildStepNode(
            step: 3,
            label: 'Results',
            isActive: false,
            isCompleted: false,
          ),
        ],
      ),
    );
  }

  Widget _buildStepNode({
    required int step,
    required String label,
    required bool isActive,
    required bool isCompleted,
  }) {
    Color circleColor = const Color(0xFFF1F5F9);
    Color textColor = AppColors.textSecondary;
    Widget child = Text(
      '$step',
      style: const TextStyle(
        fontSize: 11,
        fontWeight: FontWeight.bold,
        color: AppColors.textSecondary,
      ),
    );

    if (isCompleted) {
      circleColor = AppColors.normalBg;
      textColor = AppColors.normal;
      child = const Icon(Icons.check, size: 14, color: AppColors.normal);
    } else if (isActive) {
      circleColor = AppColors.primary;
      textColor = AppColors.primaryDark;
      child = Text(
        '$step',
        style: const TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: Colors.white,
        ),
      );
    }

    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(
          width: 22,
          height: 22,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: circleColor,
            shape: BoxShape.circle,
          ),
          child: child,
        ),
        const SizedBox(width: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: isActive ? FontWeight.bold : FontWeight.w500,
            color: textColor,
          ),
        ),
      ],
    );
  }

  Widget _buildStepDivider({required bool isCompleted}) {
    return Expanded(
      child: Container(
        height: 2,
        margin: const EdgeInsets.symmetric(horizontal: 8),
        color: isCompleted ? AppColors.normal : AppColors.divider,
      ),
    );
  }

  Widget _buildPatientContextCard() {
    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Row(
            children: [
              Icon(Icons.person_outline_rounded,
                  size: 20, color: AppColors.primary),
              SizedBox(width: 8),
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
          const SizedBox(height: 6),
          const Text(
            'Age and sex help refine reference ranges and risk model predictions.',
            style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
          ),
          const SizedBox(height: 12),
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
                    contentPadding:
                        EdgeInsets.symmetric(horizontal: 12, vertical: 10),
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
                  isExpanded: true,
                  decoration: const InputDecoration(
                    labelText: 'Sex',
                    isDense: true,
                    contentPadding:
                        EdgeInsets.symmetric(horizontal: 10, vertical: 10),
                  ),
                  items: const [
                    DropdownMenuItem(
                      value: null,
                      child: Text('Unspecified',
                          overflow: TextOverflow.ellipsis),
                    ),
                    DropdownMenuItem(
                      value: 'M',
                      child: Text('Male (M)',
                          overflow: TextOverflow.ellipsis),
                    ),
                    DropdownMenuItem(
                      value: 'F',
                      child: Text('Female (F)',
                          overflow: TextOverflow.ellipsis),
                    ),
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
    );
  }

  Widget _buildSummaryChips(VerificationState state) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: AppColors.divider),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(
            '${state.measurements.length} Measurements',
            style: const TextStyle(
              fontWeight: FontWeight.bold,
              fontSize: 13,
              color: AppColors.textPrimary,
            ),
          ),
          Wrap(
            spacing: 6,
            children: [
              if (state.unverifiedCount > 0)
                _buildCountBadge(state.unverifiedCount, 'Needs Review',
                    AppColors.highBg, AppColors.high),
              if (state.correctedCount > 0)
                _buildCountBadge(state.correctedCount, 'Corrected',
                    AppColors.lowBg, AppColors.low),
              if (state.confirmedCount > 0)
                _buildCountBadge(state.confirmedCount, 'Confirmed',
                    AppColors.normalBg, AppColors.normal),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildCountBadge(int count, String label, Color bg, Color fg) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(12),
      ),
      child: Text(
        '$count $label',
        style: TextStyle(
          fontSize: 11,
          fontWeight: FontWeight.bold,
          color: fg,
        ),
      ),
    );
  }

  Widget _buildEmptyState(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(28),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(color: AppColors.divider),
      ),
      child: Column(
        children: [
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: AppColors.primarySurface,
              shape: BoxShape.circle,
            ),
            child: const Icon(
              Icons.content_paste_search_rounded,
              size: 48,
              color: AppColors.primary,
            ),
          ),
          const SizedBox(height: 16),
          const Text(
            "We couldn't find any medical test values in this report.",
            textAlign: TextAlign.center,
            style: TextStyle(
              fontSize: 15,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
          ),
          const SizedBox(height: 6),
          const Text(
            'The selected document might be a general file or unreadable scan. You can upload a different file or manually enter your test values below.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: AppColors.textSecondary,
              fontSize: 12,
              height: 1.4,
            ),
          ),
          const SizedBox(height: 20),
          Row(
            children: [
              Expanded(
                child: OutlinedButton(
                  onPressed: () => Navigator.pop(context),
                  child: const Text('Try Another Report'),
                ),
              ),
              const SizedBox(width: 10),
              Expanded(
                child: ElevatedButton.icon(
                  icon: const Icon(Icons.add, size: 18),
                  label: const Text('Add Manually'),
                  onPressed: () => _showAddDialog(context),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildMeasurementTile(
      BuildContext context, EditableMeasurement item) {
    final isManual = item.origin == MeasurementOrigin.manual;
    final isUnverified = item.status == VerificationItemStatus.unverified;

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(
          color: isUnverified
              ? AppColors.high.withValues(alpha: 0.3)
              : AppColors.divider,
        ),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header: Origin badge + Status chip
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Container(
                padding:
                    const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: isManual
                      ? const Color(0xFFEFF6FF)
                      : AppColors.primarySurface,
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      isManual
                          ? Icons.edit_outlined
                          : Icons.description_outlined,
                      size: 12,
                      color: isManual
                          ? const Color(0xFF2563EB)
                          : AppColors.primary,
                    ),
                    const SizedBox(width: 4),
                    Text(
                      isManual ? 'Added Manually' : 'Extracted from Report',
                      style: TextStyle(
                        fontSize: 10,
                        fontWeight: FontWeight.w600,
                        color: isManual
                            ? const Color(0xFF1D4ED8)
                            : AppColors.primaryDark,
                      ),
                    ),
                  ],
                ),
              ),
              VerificationStatusChip(status: item.status),
            ],
          ),
          const SizedBox(height: 10),

          // Test name & value display
          Text(
            item.testName,
            style: const TextStyle(
              fontSize: 16,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
              letterSpacing: -0.2,
            ),
          ),
          const SizedBox(height: 6),
          Row(
            crossAxisAlignment: CrossAxisAlignment.baseline,
            textBaseline: TextBaseline.alphabetic,
            children: [
              Text(
                '${item.value ?? "N/A"}',
                style: const TextStyle(
                  fontSize: 20,
                  fontWeight: FontWeight.bold,
                  color: AppColors.primary,
                ),
              ),
              if (item.unit != null && item.unit!.isNotEmpty) ...[
                const SizedBox(width: 6),
                Text(
                  item.unit!,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textSecondary,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),

          if (item.extractedReferenceRange != null &&
              item.extractedReferenceRange!.isNotEmpty) ...[
            const SizedBox(height: 6),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
              decoration: BoxDecoration(
                color: const Color(0xFFF8FAFC),
                borderRadius: BorderRadius.circular(6),
              ),
              child: Text(
                'Report Reference Range: ${item.extractedReferenceRange}',
                style: const TextStyle(
                  fontSize: 11,
                  color: AppColors.textSecondary,
                  fontWeight: FontWeight.w500,
                ),
              ),
            ),
          ],
          const Divider(height: 20),

          // Action row
          Row(
            children: [
              TextButton.icon(
                icon: const Icon(Icons.delete_outline,
                    size: 16, color: AppColors.critical),
                label: const Text(
                  'Remove',
                  style: TextStyle(
                    color: AppColors.critical,
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                  ),
                ),
                onPressed: () {
                  context.read<VerificationCubit>().removeMeasurement(item.id);
                  context.read<AnalysisCubit>().invalidate();
                },
              ),
              const Spacer(),
              OutlinedButton.icon(
                icon: const Icon(Icons.edit,
                    size: 14, color: AppColors.textSecondary),
                label: const Text(
                  'Edit',
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppColors.textPrimary,
                  ),
                ),
                style: OutlinedButton.styleFrom(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  visualDensity: VisualDensity.compact,
                ),
                onPressed: () => _showEditDialog(context, item),
              ),
              if (isUnverified) ...[
                const SizedBox(width: 8),
                ElevatedButton.icon(
                  icon: const Icon(Icons.check, size: 14),
                  label: const Text(
                    'Confirm',
                    style: TextStyle(fontSize: 12, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: AppColors.normalBg,
                    foregroundColor: AppColors.normal,
                    elevation: 0,
                    padding:
                        const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                    visualDensity: VisualDensity.compact,
                  ),
                  onPressed: () {
                    context
                        .read<VerificationCubit>()
                        .confirmSingleMeasurement(item.id);
                  },
                ),
              ],
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildConfirmationBar(BuildContext context) {
    return BlocBuilder<VerificationCubit, VerificationState>(
      builder: (context, state) {
        final canConfirm = state.measurements.isNotEmpty;
        final total = state.measurements.length;
        final confirmed = state.confirmedCount + state.correctedCount;

        return Container(
          width: double.infinity,
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
          decoration: BoxDecoration(
            color: Colors.white,
            boxShadow: [
              BoxShadow(
                color: Colors.black.withValues(alpha: 0.05),
                blurRadius: 10,
                offset: const Offset(0, -3),
              ),
            ],
          ),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              if (canConfirm)
                Padding(
                  padding: const EdgeInsets.only(bottom: 8),
                  child: Row(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Icon(
                        state.isVerified
                            ? Icons.check_circle_rounded
                            : Icons.verified_outlined,
                        color: state.isVerified
                            ? AppColors.normal
                            : AppColors.primary,
                        size: 16,
                      ),
                      const SizedBox(width: 6),
                      Text(
                        state.isVerified
                            ? 'All $total Measurements Confirmed & Verified'
                            : '$confirmed of $total Measurements Confirmed',
                        style: TextStyle(
                          color: state.isVerified
                              ? AppColors.normal
                              : AppColors.textSecondary,
                          fontWeight: FontWeight.w600,
                          fontSize: 12,
                        ),
                      ),
                    ],
                  ),
                )
              else
                const Padding(
                  padding: EdgeInsets.only(bottom: 8),
                  child: Text(
                    'At least 1 verified test measurement is required to run analysis.',
                    style: TextStyle(
                      fontSize: 11,
                      color: AppColors.textMuted,
                      fontWeight: FontWeight.w500,
                    ),
                  ),
                ),
              SizedBox(
                width: double.infinity,
                height: 48,
                child: ElevatedButton.icon(
                  icon: Icon(
                    state.isVerified
                        ? Icons.arrow_forward_rounded
                        : Icons.check_rounded,
                  ),
                  label: Text(
                    state.isVerified
                        ? 'Proceed to Results'
                        : 'Confirm & Analyze',
                    style: const TextStyle(
                        fontSize: 15, fontWeight: FontWeight.bold),
                  ),
                  style: ElevatedButton.styleFrom(
                    backgroundColor: state.isVerified
                        ? AppColors.secondary
                        : AppColors.primary,
                  ),
                  onPressed: canConfirm
                      ? () {
                          if (!state.isVerified) {
                            final success = context
                                .read<VerificationCubit>()
                                .confirmVerification();
                            if (!success) return;
                          }
                          final verifiedState =
                              context.read<VerificationCubit>().state;
                          final snapshot = VerifiedSnapshot(
                            measurements: verifiedState.measurements,
                            patientContext: verifiedState.patientContext,
                            isVerified: verifiedState.isVerified,
                          );
                          context
                              .read<AnalysisCubit>()
                              .runFullAnalysis(snapshot);
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
