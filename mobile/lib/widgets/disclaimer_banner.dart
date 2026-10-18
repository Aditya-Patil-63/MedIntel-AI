import 'package:flutter/material.dart';
import '../core/constants/app_constants.dart';
import '../core/theme/app_colors.dart';

/// Prominent sticky non-diagnostic medical safety disclaimer.
///
/// Designed with a calm advisory tone and high readability to assure
/// patients without alarming them, complying with clinical ethics.
class DisclaimerBanner extends StatelessWidget {
  final String? customText;

  const DisclaimerBanner({super.key, this.customText});

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: AppColors.bannerBg,
        border: Border.all(color: AppColors.bannerBorder, width: 1),
        borderRadius: BorderRadius.circular(12),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.shield_outlined,
            color: AppColors.bannerText,
            size: 18,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              customText ?? AppConstants.mandatoryDisclaimer,
              style: const TextStyle(
                color: AppColors.bannerText,
                fontSize: 12,
                fontWeight: FontWeight.w500,
                height: 1.35,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
