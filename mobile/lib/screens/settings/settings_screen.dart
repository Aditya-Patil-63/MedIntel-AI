import 'package:flutter/material.dart';
import 'package:flutter_bloc/flutter_bloc.dart';
import '../../core/theme/app_colors.dart';
import '../../services/api_service.dart';
import '../../state/auth/auth_cubit.dart';
import '../../state/history/history_cubit.dart';
import '../../widgets/server_settings_dialog.dart';

/// Redesigned clean, modern Settings screen inspired by WhatsApp and Telegram.
///
/// Features a minimal layout with clear section headers, aligned settings items,
/// simple icons, readable text, and subtle dividers. Backend connection runs
/// automatically in the background without dedicated status or refresh clutter.
class SettingsScreen extends StatefulWidget {
  const SettingsScreen({super.key});

  @override
  State<SettingsScreen> createState() => _SettingsScreenState();
}

class _SettingsScreenState extends State<SettingsScreen> {
  // Supported languages
  static const Map<String, String> _languages = {
    'english': 'English',
    'hindi': 'हिंदी (Hindi)',
    'marathi': 'मराठी (Marathi)',
    'gujarati': 'ગુજરાતી (Gujarati)',
  };

  void _showLanguagePicker(BuildContext context) {
    final authCubit = context.read<AuthCubit>();
    final currentLang = authCubit.currentUser?.languagePreference.toLowerCase() ?? 'english';

    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.symmetric(vertical: 20, horizontal: 16),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.language_rounded, color: AppColors.primary, size: 22),
                    SizedBox(width: 10),
                    Text(
                      'Select Language',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 6),
                const Text(
                  'Choose your preferred language for report analysis, explanations, and advice.',
                  style: TextStyle(fontSize: 13, color: AppColors.textSecondary),
                ),
                const SizedBox(height: 16),
                ..._languages.entries.map((entry) {
                  final isSelected = currentLang == entry.key;
                  return InkWell(
                    onTap: () {
                      authCubit.updateLanguage(entry.key);
                      Navigator.pop(sheetContext);
                      ScaffoldMessenger.of(context).showSnackBar(
                        SnackBar(
                          content: Text('Language preference set to ${entry.value}'),
                          duration: const Duration(seconds: 2),
                          backgroundColor: AppColors.primaryDark,
                        ),
                      );
                      setState(() {});
                    },
                    borderRadius: BorderRadius.circular(10),
                    child: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
                      margin: const EdgeInsets.only(bottom: 6),
                      decoration: BoxDecoration(
                        color: isSelected ? AppColors.primary.withValues(alpha: 0.08) : Colors.transparent,
                        borderRadius: BorderRadius.circular(10),
                        border: isSelected ? Border.all(color: AppColors.primary.withValues(alpha: 0.3)) : null,
                      ),
                      child: Row(
                        children: [
                          Expanded(
                            child: Text(
                              entry.value,
                              style: TextStyle(
                                fontSize: 15,
                                fontWeight: isSelected ? FontWeight.bold : FontWeight.w500,
                                color: isSelected ? AppColors.primaryDark : AppColors.textPrimary,
                              ),
                            ),
                          ),
                          if (isSelected)
                            const Icon(Icons.check_circle_rounded, color: AppColors.primary, size: 20),
                        ],
                      ),
                    ),
                  );
                }),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showAppearanceInfo(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.palette_outlined, color: Color(0xFF4F46E5), size: 22),
                    SizedBox(width: 10),
                    Text(
                      'Appearance',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                ListTile(
                  contentPadding: EdgeInsets.zero,
                  leading: const Icon(Icons.wb_sunny_outlined, color: AppColors.primary),
                  title: const Text('Clinical Teal Light Mode', style: TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: const Text('Optimized for medical clarity, high legibility, and eye comfort'),
                  trailing: const Icon(Icons.check_circle, color: AppColors.primary),
                ),
                const Divider(),
                const SizedBox(height: 6),
                const Text(
                  'Dark Mode support is scheduled for an upcoming release.',
                  style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showPrivacyInfo(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.shield_outlined, color: AppColors.normal, size: 22),
                    SizedBox(width: 10),
                    Text(
                      'Patient Data Privacy',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                _buildBulletPoint(
                  Icons.person_pin_circle_outlined,
                  'Account-Scoped Isolation',
                  'All uploaded reports and risk analyses are strictly isolated to your user account.',
                ),
                const SizedBox(height: 10),
                _buildBulletPoint(
                  Icons.verified_outlined,
                  'Deterministic Safety',
                  'Laboratory reference intervals are verified against clinical reference standards.',
                ),
                const SizedBox(height: 10),
                _buildBulletPoint(
                  Icons.lock_outline,
                  'Encrypted Local Storage',
                  'Session data and tokens are held securely in private application memory.',
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  Widget _buildBulletPoint(IconData icon, String title, String desc) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 18, color: AppColors.primary),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w600,
                  color: AppColors.textPrimary,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                desc,
                style: const TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.3),
              ),
            ],
          ),
        ),
      ],
    );
  }

  void _showDisclaimerSheet(BuildContext context) {
    showModalBottomSheet(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (sheetContext) {
        return SafeArea(
          child: Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Row(
                  children: [
                    Icon(Icons.health_and_safety_outlined, color: AppColors.critical, size: 22),
                    SizedBox(width: 10),
                    Text(
                      'Medical Safety Advisory',
                      style: TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.bold,
                        color: AppColors.textPrimary,
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(10),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: const Text(
                    'MedIntel AI is an educational health intelligence assistant. It does not provide medical diagnoses, treatment decisions, or change medication dosages. Always consult a qualified physician for any medical concerns.',
                    style: TextStyle(fontSize: 13, color: Color(0xFF991B1B), height: 1.4),
                  ),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  void _showAboutDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Row(
            children: [
              Icon(Icons.info_outline, color: AppColors.primary),
              SizedBox(width: 8),
              Text('About MedIntel AI', style: TextStyle(fontSize: 17, fontWeight: FontWeight.bold)),
            ],
          ),
          content: const Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                'MedIntel AI — Intelligent Medical Report Analyzer',
                style: TextStyle(fontWeight: FontWeight.bold, fontSize: 13),
              ),
              SizedBox(height: 6),
              Text(
                'Version 0.1.0 (Build 2026.10)\nAcademic Capstone & Healthcare AI Architecture',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary),
              ),
              SizedBox(height: 10),
              Text(
                'Features OCR document extraction, deterministic laboratory reference range verification, statistical machine learning risk prediction for diabetes, heart disease, and kidney disease, and Gemini generative AI explanations.',
                style: TextStyle(fontSize: 12, color: AppColors.textSecondary, height: 1.4),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Close'),
            ),
          ],
        );
      },
    );
  }

  void _confirmSignOut(BuildContext context) {
    showDialog(
      context: context,
      builder: (dialogContext) {
        return AlertDialog(
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text('Sign Out?'),
          content: const Text(
            'Are you sure you want to sign out? Your current session and private cache will be closed.',
            style: TextStyle(fontSize: 14, color: AppColors.textSecondary),
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(dialogContext),
              child: const Text('Cancel', style: TextStyle(color: AppColors.textSecondary)),
            ),
            ElevatedButton(
              style: ElevatedButton.styleFrom(
                backgroundColor: AppColors.critical,
                foregroundColor: Colors.white,
              ),
              onPressed: () {
                Navigator.pop(dialogContext);
                context.read<AuthCubit>().logout();
                context.read<HistoryCubit>().clearHistory();
                Navigator.of(context).popUntil((route) => route.isFirst);
              },
              child: const Text('Sign Out'),
            ),
          ],
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    final user = context.watch<AuthCubit>().currentUser;
    final apiService = context.watch<ApiService>();
    final currentLangKey = user?.languagePreference.toLowerCase() ?? 'english';
    final currentLangName = _languages[currentLangKey] ?? 'English';

    return Scaffold(
      backgroundColor: AppColors.background,
      appBar: AppBar(
        title: const Text('Settings'),
        elevation: 0,
      ),
      body: SafeArea(
        child: ListView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
          children: [
            // 1. Profile Header Card
            _buildProfileCard(user),
            const SizedBox(height: 20),

            // 2. Preferences Group
            _buildSectionHeader('PREFERENCES'),
            _buildGroupCard([
              _buildSettingsTile(
                icon: Icons.translate_rounded,
                iconColor: const Color(0xFF0284C7),
                iconBg: const Color(0xFFE0F2FE),
                title: 'Language',
                subtitle: currentLangName,
                onTap: () => _showLanguagePicker(context),
              ),
              _buildDivider(),
              _buildSettingsTile(
                icon: Icons.palette_outlined,
                iconColor: const Color(0xFF4F46E5),
                iconBg: const Color(0xFFEEF2FF),
                title: 'Appearance',
                subtitle: 'Light Theme (Medical Teal)',
                onTap: () => _showAppearanceInfo(context),
              ),
            ]),
            const SizedBox(height: 20),

            // 3. Privacy & Clinical Safety Group
            _buildSectionHeader('PRIVACY & CLINICAL SAFETY'),
            _buildGroupCard([
              _buildSettingsTile(
                icon: Icons.verified_user_outlined,
                iconColor: const Color(0xFF059669),
                iconBg: const Color(0xFFECFDF5),
                title: 'Patient Data Privacy',
                subtitle: 'Reports are isolated to your account',
                onTap: () => _showPrivacyInfo(context),
              ),
              _buildDivider(),
              _buildSettingsTile(
                icon: Icons.health_and_safety_outlined,
                iconColor: const Color(0xFFD97706),
                iconBg: const Color(0xFFFEF3C7),
                title: 'Medical Disclaimer',
                subtitle: 'Educational risk indicators • Not a diagnosis',
                onTap: () => _showDisclaimerSheet(context),
              ),
            ]),
            const SizedBox(height: 20),

            // 4. Network & Server Group
            _buildSectionHeader('NETWORK & BACKEND'),
            _buildGroupCard([
              _buildSettingsTile(
                icon: Icons.dns_outlined,
                iconColor: const Color(0xFF475569),
                iconBg: const Color(0xFFF1F5F9),
                title: 'Backend Server',
                subtitle: '${apiService.baseUrl} (Tap to change)',
                onTap: () {
                  ServerSettingsDialog.show(
                    context,
                    onSaved: () => setState(() {}),
                  );
                },
              ),
            ]),
            const SizedBox(height: 20),

            // 5. About Group
            _buildSectionHeader('ABOUT'),
            _buildGroupCard([
              _buildSettingsTile(
                icon: Icons.info_outline,
                iconColor: const Color(0xFF0F766E),
                iconBg: const Color(0xFFCCFBF1),
                title: 'About MedIntel AI',
                subtitle: 'Version 0.1.0 • Final-Year Research Capstone',
                onTap: () => _showAboutDialog(context),
              ),
            ]),
            const SizedBox(height: 24),

            // 6. Sign Out Button
            _buildGroupCard([
              _buildSettingsTile(
                icon: Icons.logout_rounded,
                iconColor: AppColors.critical,
                iconBg: const Color(0xFFFEE2E2),
                title: 'Sign Out',
                subtitle: 'End current patient session',
                titleColor: AppColors.critical,
                onTap: () => _confirmSignOut(context),
              ),
            ]),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }

  Widget _buildProfileCard(dynamic user) {
    final name = user?.name ?? 'Patient';
    final email = user?.email ?? 'patient@medintel.ai';
    final initial = name.isNotEmpty ? name[0].toUpperCase() : 'P';

    return Container(
      padding: const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: AppColors.divider.withValues(alpha: 0.6)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Row(
        children: [
          CircleAvatar(
            radius: 28,
            backgroundColor: AppColors.primary.withValues(alpha: 0.12),
            child: Text(
              initial,
              style: const TextStyle(
                fontSize: 22,
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
                  name,
                  style: const TextStyle(
                    fontSize: 17,
                    fontWeight: FontWeight.bold,
                    color: AppColors.textPrimary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 2),
                Text(
                  email,
                  style: const TextStyle(
                    fontSize: 13,
                    color: AppColors.textSecondary,
                  ),
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                ),
                const SizedBox(height: 6),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                      decoration: BoxDecoration(
                        color: AppColors.normalBg,
                        borderRadius: BorderRadius.circular(6),
                      ),
                      child: const Row(
                        mainAxisSize: MainAxisSize.min,
                        children: [
                          Icon(Icons.shield_outlined, size: 12, color: AppColors.normal),
                          SizedBox(width: 4),
                          Text(
                            'Active & Isolated',
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
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildSectionHeader(String title) {
    return Padding(
      padding: const EdgeInsets.only(left: 4, bottom: 8),
      child: Text(
        title,
        style: const TextStyle(
          fontSize: 12,
          fontWeight: FontWeight.w700,
          letterSpacing: 0.8,
          color: AppColors.textSecondary,
        ),
      ),
    );
  }

  Widget _buildGroupCard(List<Widget> children) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.divider.withValues(alpha: 0.6)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withValues(alpha: 0.02),
            blurRadius: 6,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: children,
      ),
    );
  }

  Widget _buildDivider() {
    return Padding(
      padding: const EdgeInsets.only(left: 56),
      child: Divider(
        height: 1,
        thickness: 0.5,
        color: AppColors.divider.withValues(alpha: 0.5),
      ),
    );
  }

  Widget _buildSettingsTile({
    required IconData icon,
    required Color iconColor,
    required Color iconBg,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
    Color? titleColor,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 12),
        child: Row(
          children: [
            Container(
              width: 36,
              height: 36,
              decoration: BoxDecoration(
                color: iconBg,
                borderRadius: BorderRadius.circular(10),
              ),
              child: Icon(icon, color: iconColor, size: 20),
            ),
            const SizedBox(width: 14),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    title,
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w600,
                      color: titleColor ?? AppColors.textPrimary,
                    ),
                  ),
                  const SizedBox(height: 2),
                  Text(
                    subtitle,
                    style: const TextStyle(
                      fontSize: 13,
                      color: AppColors.textSecondary,
                    ),
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            const Icon(
              Icons.chevron_right,
              size: 20,
              color: Color(0xFF94A3B8),
            ),
          ],
        ),
      ),
    );
  }
}
