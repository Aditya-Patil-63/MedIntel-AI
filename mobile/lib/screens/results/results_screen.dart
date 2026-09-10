import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../state/analysis/analysis_cubit.dart';
import '../../state/analysis/analysis_state.dart';
import '../../widgets/disclaimer_banner.dart';

class ResultsScreen extends StatelessWidget {
  const ResultsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Analysis & Risk Results')),
      body: SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              const DisclaimerBanner(),
              const SizedBox(height: 16),
              Expanded(
                child: BlocBuilder<AnalysisCubit, AnalysisState>(
                  builder: (context, state) {
                    if (state is AnalysisLoading) {
                      return Center(
                        child: Column(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const CircularProgressIndicator(),
                            const SizedBox(height: 12),
                            Text(state.stage),
                          ],
                        ),
                      );
                    }

                    if (state is AnalysisError) {
                      return Center(
                        child: Text(
                          state.message,
                          textAlign: TextAlign.center,
                          style: const TextStyle(color: Colors.red),
                        ),
                      );
                    }

                    return const Center(
                      child: Text(
                        'No analysis completed yet.\nVerify extracted data and tap Analyze.',
                        textAlign: TextAlign.center,
                        style: TextStyle(color: Colors.grey),
                      ),
                    );
                  },
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
