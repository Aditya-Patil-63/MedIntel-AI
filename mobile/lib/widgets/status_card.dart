import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';

/// Backend status indicator chip card.
class StatusCard extends StatelessWidget {
  final String title;
  final String status;
  final bool isOk;
  final VoidCallback? onTap;

  const StatusCard({
    super.key,
    required this.title,
    required this.status,
    required this.isOk,
    this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      elevation: 0,
      color: isOk ? AppColors.normalBg : const Color(0xFFF1F5F9),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(8),
        side: BorderSide(
          color: isOk ? AppColors.normal : AppColors.divider,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(8),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                isOk ? Icons.check_circle : Icons.radio_button_unchecked,
                size: 16,
                color: isOk ? AppColors.normal : AppColors.textMuted,
              ),
              const SizedBox(width: 6),
              Text(
                '$title: $status',
                style: TextStyle(
                  fontSize: 12,
                  fontWeight: FontWeight.w600,
                  color: isOk ? AppColors.normal : AppColors.textSecondary,
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
