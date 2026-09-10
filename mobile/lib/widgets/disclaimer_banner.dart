import 'package:flutter/material.dart';
import '../core/constants/app_constants.dart';
import '../core/theme/app_colors.dart';

/// Prominent sticky non-diagnostic medical safety disclaimer.
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
        border: Border.all(color: AppColors.bannerBorder),
        borderRadius: BorderRadius.circular(8),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          const Icon(
            Icons.info_outline,
            color: AppColors.bannerText,
            size: 20,
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(
              customText ?? AppConstants.mandatoryDisclaimer,
              style: const TextStyle(
                color: AppColors.bannerText,
                fontSize: 12,
                fontWeight: FontWeight.w500,
                height: 1.3,
              ),
            ),
          ),
        ],
      ),
    );
  }
}
