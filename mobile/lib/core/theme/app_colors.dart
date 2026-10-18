import 'package:flutter/material.dart';

/// Semantic clinical color palette for MedIntel AI.
///
/// Designed with healthcare-grade contrast, calm trustworthy tones,
/// and accessible classification indicators inspired by modern clinical systems.
class AppColors {
  AppColors._();

  // Primary Brand: Deep Medical Teal & Emerald Accents
  static const Color primary = Color(0xFF0F766E); // Deep Medical Teal
  static const Color primaryLight = Color(0xFF14B8A6); // Soft Teal
  static const Color primaryDark = Color(0xFF042F2E); // Dark Pine / Teal 900
  static const Color primarySurface = Color(0xFFF0FDFA); // Teal 50 tint
  static const Color primaryContainer = Color(0xFFCCFBF1); // Teal 100

  // Secondary & Accents: Clinical Slate Blue
  static const Color secondary = Color(0xFF0284C7); // Clinical Blue
  static const Color secondarySurface = Color(0xFFF0F9FF);
  static const Color accent = Color(0xFF0D9488);

  // Backgrounds & Neutrals: Cool Crisp Grays
  static const Color background = Color(0xFFF8FAFC); // Slate 50
  static const Color surface = Color(0xFFFFFFFF);
  static const Color surfaceElevated = Color(0xFFFFFFFF);
  static const Color card = Color(0xFFFFFFFF);
  static const Color cardSurface = Color(0xFFFFFFFF);
  static const Color divider = Color(0xFFE2E8F0); // Slate 200
  static const Color cardBorder = Color(0xFFE2E8F0);
  static const Color borderSubtle = Color(0xFFF1F5F9); // Slate 100

  // Text Hierarchy
  static const Color textPrimary = Color(0xFF0F172A); // Slate 900
  static const Color textSecondary = Color(0xFF475569); // Slate 600
  static const Color textMuted = Color(0xFF94A3B8); // Slate 400

  // Medical Classification Indicators
  // Normal / Safe: Subtle Emerald Green
  static const Color normal = Color(0xFF16A34A); // Green 600
  static const Color normalBg = Color(0xFFECFDF5); // Green 50
  static const Color normalBorder = Color(0xFFA7F3D0); // Green 200

  // Low / Sub-reference: Cool Medical Blue
  static const Color low = Color(0xFF0284C7); // Sky 600
  static const Color lowBg = Color(0xFFF0F9FF); // Sky 50
  static const Color lowBorder = Color(0xFFBAE6FD); // Sky 200

  // High / Warning: Soft Warm Amber
  static const Color high = Color(0xFFD97706); // Amber 600
  static const Color highBg = Color(0xFFFFFBEB); // Amber 50
  static const Color highBorder = Color(0xFFFDE68A); // Amber 200
  static const Color warning = Color(0xFFD97706);
  static const Color warningBg = Color(0xFFFFFBEB);

  // Critical / Out of Range: Restrained Clinical Red
  static const Color critical = Color(0xFFDC2626); // Red 600
  static const Color criticalBg = Color(0xFFFEF2F2); // Red 50
  static const Color criticalBorder = Color(0xFFFECACA); // Red 200

  // Medical Disclaimer Banner: Soft Calm Tint
  static const Color bannerBg = Color(0xFFFFFBEB); // Amber 50
  static const Color bannerBorder = Color(0xFFFDE68A); // Amber 200
  static const Color bannerText = Color(0xFF92400E); // Amber 800
}

/// Helper design styles for clean shadows and card elevation
class BoxStyle {
  BoxStyle._();

  static const BoxShadow cardShadow = BoxShadow(
    color: Color(0x0A0F172A),
    blurRadius: 10,
    offset: Offset(0, 2),
  );
}
