import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../state/verification/verification_cubit.dart';
import '../../state/verification/verification_state.dart';
import '../../widgets/disclaimer_banner.dart';

class VerificationScreen extends StatelessWidget {
  const VerificationScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('User Verification Gate')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const DisclaimerBanner(),
              const SizedBox(height: 16),
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: AppColors.lowBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: AppColors.low),
                ),
                child: const Row(
                  children: [
                    Icon(Icons.security, color: AppColors.low),
                    SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Mandatory Safety Rule: You must verify all extracted values before the backend allows clinical analysis.',
                        style: TextStyle(
                          fontSize: 12,
                          color: AppColors.textPrimary,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 16),
              Expanded(
                child: BlocBuilder<VerificationCubit, VerificationState>(
                  builder: (context, state) {
                    if (state.measurements.isEmpty) {
                      return const Center(
                        child: Text(
                          'No measurements currently loaded for review.\nUpload a report or input test values.',
                          textAlign: TextAlign.center,
                          style: TextStyle(color: AppColors.textMuted),
                        ),
                      );
                    }

                    return ListView.builder(
                      itemCount: state.measurements.length,
                      itemBuilder: (context, index) {
                        final item = state.measurements[index];
                        return Card(
                          child: ListTile(
                            title: Text(item.testName),
                            subtitle: Text('${item.value ?? "N/A"} ${item.unit ?? ""}'),
                            trailing: Icon(
                              item.isUserVerified
                                  ? Icons.check_circle
                                  : Icons.pending_outlined,
                              color: item.isUserVerified
                                  ? AppColors.normal
                                  : AppColors.high,
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
              ),
              BlocBuilder<VerificationCubit, VerificationState>(
                builder: (context, state) {
                  return SizedBox(
                    width: double.infinity,
                    child: ElevatedButton.icon(
                      icon: const Icon(Icons.check),
                      label: Text(
                        state.isVerified
                            ? 'Verified (Ready for Analysis)'
                            : 'Confirm & Verify Extracted Data',
                      ),
                      onPressed: state.isVerified || state.measurements.isEmpty
                          ? null
                          : () {
                              context
                                  .read<VerificationCubit>()
                                  .confirmVerification();
                            },
                    ),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }
}
