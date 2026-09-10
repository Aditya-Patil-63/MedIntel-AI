import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/constants/app_constants.dart';
import '../../core/theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../state/verification/verification_cubit.dart';
import '../../state/verification/verification_state.dart';
import '../../widgets/disclaimer_banner.dart';
import '../../widgets/status_card.dart';
import '../history/history_screen.dart';
import '../results/results_screen.dart';
import '../upload/upload_screen.dart';
import '../verification/verification_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  String _backendStatus = 'Checking...';
  String _mlStatus = 'Checking...';
  String _genaiStatus = 'Checking...';
  bool _isBackendOk = false;
  bool _isMlOk = false;
  bool _isGenAiOk = false;

  @override
  void initState() {
    super.initState();
    _checkServices();
  }

  Future<void> _checkServices() async {
    final apiService = context.read<ApiService>();

    // 1. Health
    try {
      final health = await apiService.getHealth();
      if (mounted) {
        setState(() {
          _isBackendOk = health['status'] == 'ok';
          _backendStatus = health['status']?.toString() ?? 'online';
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isBackendOk = false;
          _backendStatus = 'offline';
        });
      }
    }

    // 2. ML Status
    try {
      final ml = await apiService.getMLStatus();
      if (mounted) {
        setState(() {
          _isMlOk = ml.status == 'OK';
          _mlStatus = ml.status;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isMlOk = false;
          _mlStatus = 'unavailable';
        });
      }
    }

    // 3. GenAI Status
    try {
      final genai = await apiService.getGenAIStatus();
      if (mounted) {
        setState(() {
          _isGenAiOk = genai.available;
          _genaiStatus = genai.status;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _isGenAiOk = false;
          _genaiStatus = 'unavailable';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(6),
              decoration: BoxDecoration(
                color: AppColors.primary,
                borderRadius: BorderRadius.circular(8),
              ),
              child: const Icon(
                Icons.medical_services_outlined,
                color: Colors.white,
                size: 20,
              ),
            ),
            const SizedBox(width: 10),
            const Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  AppConstants.appName,
                  style: TextStyle(
                    fontSize: 18,
                    fontWeight: FontWeight.bold,
                  ),
                ),
                Text(
                  'Phase 9 Mobile Client',
                  style: TextStyle(
                    fontSize: 11,
                    color: AppColors.textMuted,
                  ),
                ),
              ],
            ),
          ],
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Status',
            onPressed: _checkServices,
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 1. Mandatory Educational Disclaimer Banner
              const DisclaimerBanner(),
              const SizedBox(height: 16),

              // 2. Backend Subsystems Status Overview
              const Text(
                'Subsystem Status',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 8),
              Wrap(
                spacing: 8,
                runSpacing: 8,
                children: [
                  StatusCard(
                    title: 'Backend',
                    status: _backendStatus,
                    isOk: _isBackendOk,
                    onTap: _checkServices,
                  ),
                  StatusCard(
                    title: 'ML Models',
                    status: _mlStatus,
                    isOk: _isMlOk,
                    onTap: _checkServices,
                  ),
                  StatusCard(
                    title: 'GenAI',
                    status: _genaiStatus,
                    isOk: _isGenAiOk,
                    onTap: _checkServices,
                  ),
                ],
              ),
              const SizedBox(height: 24),

              // 3. Clinical Pipeline Actions
              const Text(
                'Clinical Pipeline',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.bold,
                  color: AppColors.textSecondary,
                ),
              ),
              const SizedBox(height: 12),
              _buildActionTile(
                icon: Icons.upload_file,
                title: 'Upload Report',
                subtitle: 'Select PDF or image medical report (<=10 MB)',
                color: AppColors.primary,
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const UploadScreen()),
                  );
                },
              ),
              BlocBuilder<VerificationCubit, VerificationState>(
                builder: (context, state) {
                  String sub = 'Confirm extracted lab values (mandatory)';
                  if (state.measurements.isNotEmpty) {
                    sub = state.isVerified
                        ? '${state.measurements.length} measurements verified'
                        : '${state.unverifiedCount} unverified measurements pending review';
                  }

                  return _buildActionTile(
                    icon: state.isVerified
                        ? Icons.verified
                        : Icons.verified_user_outlined,
                    title: 'User Verification Gate',
                    subtitle: sub,
                    color: state.isVerified
                        ? AppColors.normal
                        : AppColors.secondary,
                    trailingBadge: state.unverifiedCount > 0
                        ? Container(
                            padding: const EdgeInsets.symmetric(
                                horizontal: 8, vertical: 2),
                            decoration: BoxDecoration(
                              color: AppColors.highBg,
                              borderRadius: BorderRadius.circular(10),
                            ),
                            child: Text(
                              '${state.unverifiedCount} pending',
                              style: const TextStyle(
                                fontSize: 11,
                                fontWeight: FontWeight.bold,
                                color: AppColors.high,
                              ),
                            ),
                          )
                        : null,
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                            builder: (_) => const VerificationScreen()),
                      );
                    },
                  );
                },
              ),
              _buildActionTile(
                icon: Icons.analytics_outlined,
                title: 'Analysis & ML Risk',
                subtitle: 'Deterministic reference range & ML risk estimation',
                color: AppColors.high,
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const ResultsScreen()),
                  );
                },
              ),
              _buildActionTile(
                icon: Icons.history,
                title: 'Report History',
                subtitle: 'Review past reports and clinical summaries',
                color: AppColors.textSecondary,
                onTap: () {
                  Navigator.push(
                    context,
                    MaterialPageRoute(builder: (_) => const HistoryScreen()),
                  );
                },
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildActionTile({
    required IconData icon,
    required String title,
    required String subtitle,
    required Color color,
    Widget? trailingBadge,
    required VoidCallback onTap,
  }) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: ListTile(
        leading: Container(
          padding: const EdgeInsets.all(10),
          decoration: BoxDecoration(
            color: color.withValues(alpha: 0.1),
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, color: color),
        ),
        title: Text(
          title,
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 15),
        ),
        subtitle: Text(
          subtitle,
          style: const TextStyle(fontSize: 12, color: AppColors.textSecondary),
        ),
        trailing: trailingBadge ??
            const Icon(Icons.chevron_right, color: AppColors.textMuted),
        onTap: onTap,
      ),
    );
  }
}
