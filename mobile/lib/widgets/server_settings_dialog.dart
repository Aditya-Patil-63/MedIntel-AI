import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../core/constants/api_constants.dart';
import '../core/theme/app_colors.dart';
import '../services/api_service.dart';

/// Interactive dialog for inspecting, switching, and testing the backend server URL.
class ServerSettingsDialog extends StatefulWidget {
  final VoidCallback? onSettingsSaved;

  const ServerSettingsDialog({super.key, this.onSettingsSaved});

  static Future<void> show(BuildContext context, {VoidCallback? onSaved}) {
    return showDialog(
      context: context,
      builder: (_) => ServerSettingsDialog(onSettingsSaved: onSaved),
    );
  }

  @override
  State<ServerSettingsDialog> createState() => _ServerSettingsDialogState();
}

class _ServerSettingsDialogState extends State<ServerSettingsDialog> {
  late final TextEditingController _controller;
  bool _isTesting = false;
  String? _testResult;
  bool _testSuccess = false;

  @override
  void initState() {
    super.initState();
    final apiService = context.read<ApiService>();
    _controller = TextEditingController(text: apiService.baseUrl);
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _testConnection(ApiService apiService) async {
    setState(() {
      _isTesting = true;
      _testResult = null;
    });

    try {
      final inputUrl = _controller.text.trim();
      apiService.updateBaseUrl(inputUrl);
      final health = await apiService.getHealth();
      final status = health['status']?.toString() ?? 'healthy';

      setState(() {
        _isTesting = false;
        _testSuccess = true;
        _testResult = 'Connection successful! Status: $status';
      });
      widget.onSettingsSaved?.call();
    } catch (e) {
      setState(() {
        _isTesting = false;
        _testSuccess = false;
        _testResult = 'Failed to connect: ${e.toString().split("\n").first}';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final apiService = context.read<ApiService>();

    return AlertDialog(
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      title: const Row(
        children: [
          Icon(Icons.settings_ethernet, color: AppColors.primary),
          SizedBox(width: 8),
          Expanded(
            child: Text(
              'Backend Connection',
              style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold),
            ),
          ),
        ],
      ),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            const Text(
              'Current Server Base URL:',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.w600,
                color: AppColors.textSecondary,
              ),
            ),
            const SizedBox(height: 6),
            TextFormField(
              controller: _controller,
              decoration: const InputDecoration(
                labelText: 'Server URL',
                hintText: 'http://127.0.0.1:8000',
                border: OutlineInputBorder(),
                isDense: true,
                prefixIcon: Icon(Icons.link, size: 20),
              ),
            ),
            const SizedBox(height: 12),
            const Text(
              'Select Connection Mode:',
              style: TextStyle(
                fontSize: 12,
                fontWeight: FontWeight.bold,
                color: AppColors.textPrimary,
              ),
            ),
            const SizedBox(height: 6),
            Wrap(
              spacing: 6,
              runSpacing: 6,
              children: [
                ActionChip(
                  avatar: const Icon(Icons.wifi, size: 16),
                  label: const Text('Wi-Fi LAN (Auto)'),
                  onPressed: () => setState(
                    () => _controller.text = ApiConstants.wifiLanUrl,
                  ),
                ),
                ActionChip(
                  avatar: const Icon(Icons.usb, size: 16),
                  label: const Text('USB Cable (Phone)'),
                  onPressed: () => setState(
                    () => _controller.text = ApiConstants.usbDeviceUrl,
                  ),
                ),
                ActionChip(
                  avatar: const Icon(Icons.devices, size: 16),
                  label: const Text('Android Emulator'),
                  onPressed: () => setState(
                    () => _controller.text = ApiConstants.emulatorUrl,
                  ),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(6),
                border: Border.all(color: AppColors.divider),
              ),
              child: const Text(
                'Wi-Fi LAN connects directly to your computer.\n'
                'USB Cable requires running on PC:\n'
                'adb reverse tcp:8000 tcp:8000',
                style: TextStyle(fontSize: 11, color: AppColors.textSecondary),
              ),
            ),
            if (_testResult != null) ...[
              const SizedBox(height: 10),
              Text(
                _testResult!,
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: _testSuccess ? AppColors.normal : AppColors.critical,
                ),
              ),
            ],
          ],
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.pop(context),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _isTesting ? null : () => _testConnection(apiService),
          child: _isTesting
              ? const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                )
              : const Text('Save & Test'),
        ),
      ],
    );
  }
}
