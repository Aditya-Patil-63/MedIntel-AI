import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/reference/editable_measurement.dart';

/// Accessible chip displaying measurement verification status with both icon and text.
class VerificationStatusChip extends StatelessWidget {
  final VerificationItemStatus status;

  const VerificationStatusChip({super.key, required this.status});

  @override
  Widget build(BuildContext context) {
    Color bg;
    Color fg;
    IconData icon;
    String label;

    switch (status) {
      case VerificationItemStatus.unverified:
        bg = AppColors.highBg;
        fg = AppColors.high;
        icon = Icons.pending_outlined;
        label = 'UNVERIFIED';
        break;
      case VerificationItemStatus.confirmed:
        bg = AppColors.normalBg;
        fg = AppColors.normal;
        icon = Icons.check_circle_outline;
        label = 'CONFIRMED';
        break;
      case VerificationItemStatus.corrected:
        bg = AppColors.lowBg;
        fg = AppColors.low;
        icon = Icons.edit_note;
        label = 'CORRECTED';
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
        border: Border.all(color: fg.withValues(alpha: 0.4)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: fg),
          const SizedBox(width: 4),
          Text(
            label,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: fg,
            ),
          ),
        ],
      ),
    );
  }
}
