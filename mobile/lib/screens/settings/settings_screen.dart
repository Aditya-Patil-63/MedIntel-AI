import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/constants/api_constants.dart';
import '../../core/theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../state/auth/auth_cubit.dart';
import '../../state/history/history_cubit.dart';
import '../../widgets/disclaimer_banner.dart';

/// Clean Settings & Connection Diagnostics screen for MedIntel AI.
///
/// Keeps technical network configuration accessible and intuitive without
/// cluttering patient-facing dashboards.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  late final TextEditingController _urlController;
  bool _isTesting = false;
  String? _testMessage;
  bool _isSuccess = false;

  // Subsystem health state
  bool _isLoadingDiagnostics = false;
  String _backendStatus = 'Checking...';
  bool _backendOk = false;
  String _mlStatus = 'Checking...';
  bool _mlOk = false;
  String _genaiStatus = 'Checking...';
  bool _genaiOk = false;

  @override
  void initState() {
    super.initState();
    final apiService = context.read<ApiService>();
    String currentUrl = ApiConstants.baseUrl;
    try {
      if (apiService is ApiServiceImpl) {
        currentUrl = apiService.baseUrl;
      }
    } catch (_) {}
    _urlController = TextEditingController(text: currentUrl);
    _loadDiagnostics();
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _loadDiagnostics() async {
    if (!mounted) return;
    setState(() => _isLoadingDiagnostics = true);
    final apiService = context.read<ApiService>();

    // 1. Backend health
    try {
      final health = await apiService.getHealth();
      final status = health['status']?.toString().toLowerCase() ?? 'healthy';
      if (mounted) {
        setState(() {
          _backendOk = status == 'healthy' || status == 'ok';
          _backendStatus = health['status']?.toString() ?? 'healthy';
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _backendOk = false;
          _backendStatus = 'offline';
        });
      }
    }

    // 2. ML status
    try {
      final ml = await apiService.getMLStatus();
      if (mounted) {
        setState(() {
          _mlOk = ml.status == 'OK';
          _mlStatus = ml.status;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _mlOk = false;
          _mlStatus = 'unavailable';
        });
      }
    }

    // 3. GenAI status
    try {
      final genai = await apiService.getGenAIStatus();
      if (mounted) {
        setState(() {
          _genaiOk = genai.available;
          _genaiStatus = genai.status;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _genaiOk = false;
          _genaiStatus = 'unavailable';
        });
      }
    }

    if (mounted) {
      setState(() => _isLoadingDiagnostics = false);
    }
  }

  Future<void> _saveAndTest() async {
    setState(() {
      _isTesting = true;
      _testMessage = null;
    });

    final apiService = context.read<ApiService>();
    final newUrl = _urlController.text.trim();

    try {
      apiService.updateBaseUrl(newUrl);
      final health = await apiService.getHealth();
      final statusVal = health['status']?.toString().toLowerCase();
      final isHealthy = statusVal == 'healthy' || statusVal == 'ok';

      setState(() {
        _isTesting = false;
        _isSuccess = isHealthy;
        _testMessage = isHealthy
            ? 'Connected successfully to backend ($newUrl)'
            : 'Connected, but received unexpected status: ${health["status"]}';
      });

      _loadDiagnostics();
    } catch (e) {
      setState(() {
        _isTesting = false;
        _isSuccess = false;
        _testMessage = 'Connection failed: ${e.toString().split("\n").first}';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Settings & Connection'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            tooltip: 'Refresh Diagnostics',
            onPressed: _isLoadingDiagnostics ? null : _loadDiagnostics,
          ),
        ],
      ),
      body: SafeArea(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // 0. User Account Card
              _buildAccountCard(),
              const SizedBox(height: 16),

              // 1. Connection Status Card
              _buildConnectionCard(),
              const SizedBox(height: 16),

              // 2. Server Configuration Card
              _buildServerConfigCard(),
              const SizedBox(height: 16),

              // 3. Subsystem Health & Diagnostics Card
              _buildDiagnosticsCard(),
              const SizedBox(height: 16),

              // 4. Clinical Safety Advisory
              const DisclaimerBanner(),
              const SizedBox(height: 16),

              // 5. About Card
              _buildAboutCard(),
              const SizedBox(height: 24),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildAccountCard() {
    final user = context.watch<AuthCubit>().currentUser;
    if (user == null) return const SizedBox.shrink();

    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.03),
            blurRadius: 10,
            offset: const Offset(0, 3),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              CircleAvatar(
                radius: 24,
                backgroundColor: AppColors.primary.withValues(alpha: 0.12),
                child: Text(
                  user.name.isNotEmpty ? user.name[0].toUpperCase() : 'U',
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.bold,
                    color: AppColors.primary,
                  ),
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      user.name,
                      style: const TextStyle(
                        fontSize: 16,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      user.email,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppColors.textSecondary,
                      ),
                    ),
                  ],
                ),
              ),
              OutlinedButton.icon(
                icon: const Icon(Icons.logout_rounded, size: 16, color: AppColors.critical),
                label: const Text(
                  'Sign Out',
                  style: TextStyle(color: AppColors.critical, fontSize: 13),
                ),
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: AppColors.critical),
                  padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                  ),
                ),
                onPressed: () {
                  context.read<AuthCubit>().logout();
                  context.read<HistoryCubit>().clearHistory();
                  Navigator.of(context).popUntil((route) => route.isFirst);
                },
              ),
            ],
          ),
          const SizedBox(height: 12),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
            decoration: BoxDecoration(
              color: AppColors.normalBg,
              borderRadius: BorderRadius.circular(8),
            ),
            child: const Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Icon(Icons.shield_outlined, size: 14, color: AppColors.normal),
                SizedBox(width: 6),
                Text(
                  'User Isolation: Reports are private to this account',
                  style: TextStyle(
                    fontSize: 11,
                    fontWeight: FontWeight.w600,
                    color: AppColors.normal,
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildConnectionCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: _backendOk ? AppColors.normalBg : AppColors.criticalBg,
                shape: BoxShape.circle,
              ),
              child: Icon(
                _backendOk ? Icons.cloud_done : Icons.cloud_off,
                color: _backendOk ? AppColors.normal : AppColors.critical,
                size: 28,
              ),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _backendOk ? 'Backend Connected' : 'Backend Offline',
                    style: TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.bold,
                      color: _backendOk
                          ? AppColors.normal
                          : AppColors.critical,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    _urlController.text,
                    style: const TextStyle(
                      fontSize: 12,
                      color: AppColors.textSecondary,
                      fontFamily: 'monospace',
                    ),
                  ),
                ],
              ),
            ),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: _backendOk ? AppColors.normalBg : AppColors.criticalBg,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                _backendStatus.toUpperCase(),
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: FontWeight.bold,
                  color: _backendOk ? AppColors.normal : AppColors.critical,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildServerConfigCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Row(
              children: [
                Icon(Icons.tune, color: AppColors.primary, size: 20),
                SizedBox(width: 8),
                Text(
                  'Connection Mode & Server Address',
                  style: TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 12),
            TextFormField(
              controller: _urlController,
              decoration: const InputDecoration(
                labelText: 'Base URL',
                hintText: 'http://10.62.199.105:8000',
                prefixIcon: Icon(Icons.link, size: 20),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Quick Presets:',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                ActionChip(
                  avatar: const Icon(Icons.wifi, size: 16),
                  label: const Text('Wi-Fi LAN (Recommended)'),
                  onPressed: () {
                    setState(() {
                      _urlController.text = ApiConstants.wifiLanUrl;
                    });
                  },
                ),
                ActionChip(
                  avatar: const Icon(Icons.usb, size: 16),
                  label: const Text('USB Cable'),
                  onPressed: () {
                    setState(() {
                      _urlController.text = ApiConstants.usbDeviceUrl;
                    });
                  },
                ),
                ActionChip(
                  avatar: const Icon(Icons.devices, size: 16),
                  label: const Text('Emulator'),
                  onPressed: () {
                    setState(() {
                      _urlController.text = ApiConstants.emulatorUrl;
                    });
                  },
                ),
              ],
            ),
            const SizedBox(height: 12),
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: AppColors.divider),
              ),
              child: const Text(
                '• Wi-Fi LAN: Connects directly across your local network without USB cables.\n'
                '• USB Cable: Requires running "adb reverse tcp:8000 tcp:8000" on your computer.',
                style: TextStyle(fontSize: 11, color: AppColors.textSecondary, height: 1.4),
              ),
            ),
            if (_testMessage != null) ...[
              const SizedBox(height: 12),
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: _isSuccess ? AppColors.normalBg : AppColors.criticalBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(
                    color: _isSuccess ? AppColors.normal : AppColors.critical,
                  ),
                ),
                child: Text(
                  _testMessage!,
                  style: TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w500,
                    color: _isSuccess ? AppColors.normal : AppColors.critical,
                  ),
                ),
              ),
            ],
            const SizedBox(height: 16),
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                icon: _isTesting
                    ? const SizedBox(
                        width: 16,
                        height: 16,
                        child: CircularProgressIndicator(
                          strokeWidth: 2,
                          color: Colors.white,
                        ),
                      )
                    : const Icon(Icons.check_circle_outline),
                label: Text(_isTesting ? 'Connecting...' : 'Test & Save Connection'),
                onPressed: _isTesting ? null : _saveAndTest,
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDiagnosticsCard() {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                const Row(
                  children: [
                    Icon(Icons.analytics_outlined, color: AppColors.primary, size: 20),
                    SizedBox(width: 8),
                    Text(
                      'Subsystem Diagnostics',
                      style: TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
                if (_isLoadingDiagnostics)
                  const SizedBox(
                    width: 14,
                    height: 14,
                    child: CircularProgressIndicator(strokeWidth: 2),
                  ),
              ],
            ),
            const Divider(height: 20),
            _buildDiagnosticRow(
              'FastAPI Backend',
              _backendStatus,
              _backendOk,
              'Core orchestrator & document parser',
            ),
            const SizedBox(height: 12),
            _buildDiagnosticRow(
              'ML Risk Models',
              _mlStatus,
              _mlOk,
              'Diabetes, Heart, and Kidney risk estimators',
            ),
            const SizedBox(height: 12),
            _buildDiagnosticRow(
              'GenAI Subsystem',
              _genaiStatus,
              _genaiOk,
              'Plain-language educational summary',
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildDiagnosticRow(
      String title, String status, bool isOk, String desc) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(
          isOk ? Icons.check_circle : Icons.cancel,
          size: 18,
          color: isOk ? AppColors.normal : AppColors.critical,
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              Text(
                desc,
                style: const TextStyle(
                  fontSize: 11,
                  color: AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
          decoration: BoxDecoration(
            color: isOk ? AppColors.normalBg : AppColors.criticalBg,
            borderRadius: BorderRadius.circular(6),
          ),
          child: Text(
            status.toUpperCase(),
            style: TextStyle(
              fontSize: 10,
              fontWeight: FontWeight.bold,
              color: isOk ? AppColors.normal : AppColors.critical,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildAboutCard() {
    return Card(
      elevation: 0,
      color: const Color(0xFFF8FAFC),
      child: const Padding(
        padding: EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'MedIntel AI — Intelligent Medical Report Analyzer',
              style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
            ),
            SizedBox(height: 4),
            Text(
              'Version 0.1.0 • Academic Capstone & Healthcare Research Architecture',
              style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
            ),
            SizedBox(height: 8),
            Text(
              'Combines deterministic clinical reference ranges with statistical machine learning and generative AI for plain-language patient education.',
              style: TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
            ),
          ],
        ),
      ),
    );
  }
}
