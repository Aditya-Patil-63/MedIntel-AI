import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../state/verification/verification_cubit.dart';
import '../../state/verification/verification_state.dart';
import '../../widgets/disclaimer_banner.dart';
import '../../widgets/verification_status_chip.dart';

/// Screen displaying the confirmed verified data state ready for Step 4 analysis.
class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Verified Report Summary')),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Mandatory Disclaimer Banner
              const DisclaimerBanner(),
              const SizedBox(height: 16),

              // 2. Verification Readiness Card
              BlocBuilder<VerificationCubit, VerificationState>(
                builder: (context, state) {
                  if (!state.isVerified) {
                    return Card(
                      color: AppColors.highBg,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(10),
                        side: const BorderSide(color: AppColors.high),
                      ),
                      child: const Padding(
                        padding: EdgeInsets.all(16),
                        child: Row(
                          children: [
                            Icon(Icons.warning_amber, color: AppColors.high),
                            SizedBox(width: 10),
                            Expanded(
                              child: Text(
                                'Data is unverified. Please return to the Verification Gate to confirm values.',
                                style: TextStyle(
                                  fontWeight: FontWeight.w600,
                                  fontSize: 13,
                                ),
                              ),
                            ),
                          ],
                        ),
                      ),
                    );
                  }

                  return Card(
                    color: AppColors.normalBg,
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(10),
                      side: const BorderSide(color: AppColors.normal),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Row(
                        children: [
                          const Icon(Icons.verified, color: AppColors.normal, size: 28),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                const Text(
                                  'User Verification Complete',
                                  style: TextStyle(
                                    fontWeight: FontWeight.bold,
                                    fontSize: 15,
                                    color: AppColors.normal,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  '${state.measurements.length} measurements confirmed. Ready for Reference Range & ML Risk Analysis.',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: AppColors.textPrimary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
              const SizedBox(height: 16),

              // 3. Patient Context Card
              BlocBuilder<VerificationCubit, VerificationState>(
                builder: (context, state) {
                  final ctx = state.patientContext;
                  return Card(
                    elevation: 0,
                    color: const Color(0xFFF8FAFC),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(8),
                      side: const BorderSide(color: AppColors.divider),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(12),
                      child: Row(
                        mainAxisAlignment: MainAxisAlignment.spaceAround,
                        children: [
                          Text(
                            'Age: ${ctx.age != null ? "${ctx.age!.toStringAsFixed(0)} yrs" : "Not specified"}',
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                          ),
                          Container(height: 16, width: 1, color: AppColors.divider),
                          Text(
                            'Sex: ${ctx.sex == "M" ? "Male" : ctx.sex == "F" ? "Female" : "Not specified"}',
                            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 13),
                          ),
                        ],
                      ),
                    ),
                  );
                },
              ),
              const SizedBox(height: 16),

              // 4. Verified Measurements Table/List
              const Text(
                'Verified Clinical Measurements',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 8),
              BlocBuilder<VerificationCubit, VerificationState>(
                builder: (context, state) {
                  return ListView.separated(
                    shrinkWrap: true,
                    physics: const NeverScrollableScrollPhysics(),
                    itemCount: state.measurements.length,
                    separatorBuilder: (_, _) => const SizedBox(height: 8),
                    itemBuilder: (context, index) {
                      final item = state.measurements[index];
                      return Card(
                        child: ListTile(
                          title: Text(
                            item.testName,
                            style: const TextStyle(fontWeight: FontWeight.bold),
                          ),
                          subtitle: Text('${item.value ?? "N/A"} ${item.unit ?? ""}'),
                          trailing: VerificationStatusChip(status: item.status),
                        ),
                      );
                    },
                  );
                },
              ),
              const SizedBox(height: 24),

              // 5. Phase 9 Step 4 Notice Card
              Card(
                elevation: 0,
                color: const Color(0xFFF1F5F9),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(8),
                  side: const BorderSide(color: AppColors.divider),
                ),
                child: const Padding(
                  padding: EdgeInsets.all(14),
                  child: Row(
                    children: [
                      Icon(Icons.hourglass_top, color: AppColors.secondary, size: 24),
                      SizedBox(width: 12),
                      Expanded(
                        child: Text(
                          'Downstream Reference Range Classification, ML Disease Risk, and GenAI Multilingual Explanations will be integrated in the upcoming Phase 9 steps.',
                          style: TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.3),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
