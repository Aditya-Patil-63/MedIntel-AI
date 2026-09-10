import 'package:flutter/material.dart';

/// Semantic clinical color palette for MedIntel AI.
class AppColors {
  AppColors._();

  // Brand Primaries
  static const Color primary = Color(0xFF0F766E); // Deep Medical Teal
  static const Color primaryLight = Color(0xFF14B8A6);
  static const Color primaryDark = Color(0xFF115E59);
  static const Color secondary = Color(0xFF0284C7); // Clinical Blue
  static const Color accent = Color(0xFF06B6D4);

  // Backgrounds & Neutrals
  static const Color background = Color(0xFFF8FAFC);
  static const Color surface = Color(0xFFFFFFFF);
  static const Color card = Color(0xFFFFFFFF);
  static const Color divider = Color(0xFFE2E8F0);

  // Text
  static const Color textPrimary = Color(0xFF0F172A);
  static const Color textSecondary = Color(0xFF475569);
  static const Color textMuted = Color(0xFF94A3B8);

  // Classification & Risk Indicators (Phase 6 & Phase 7 standard)
  static const Color normal = Color(0xFF16A34A); // Green
  static const Color normalBg = Color(0xFFDCFCE7);
  static const Color low = Color(0xFF0284C7); // Blue
  static const Color lowBg = Color(0xFFE0F2FE);
  static const Color high = Color(0xFFD97706); // Amber / Orange
  static const Color highBg = Color(0xFFFEF3C7);
  static const Color critical = Color(0xFFDC2626); // Red
  static const Color criticalBg = Color(0xFFFEE2E2);

  // Disclaimer banner
  static const Color bannerBg = Color(0xFFFEF9C3);
  static const Color bannerBorder = Color(0xFFFDE047);
  static const Color bannerText = Color(0xFF713F12);
}
