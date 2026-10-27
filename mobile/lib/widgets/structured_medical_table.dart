import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/reference/analysis_result.dart';
import '../models/reference/patient_details.dart';

/// Structured Medical Report Results Dashboard Table (Objective 3, Section 5).
///
/// Implements the exact 9-column specification required by Objective 3:
/// 1. Patient Details
/// 2. Test Name
/// 3. Observed Value
/// 4. Unit
/// 5. Reference Range
/// 6. Status (LOW, NORMAL, HIGH, CRITICAL, REQUIRES REVIEW)
/// 7. Alert Message
/// 8. Possible Health Implications
/// 9. Precautions and Next Steps
class StructuredMedicalTable extends StatefulWidget {
  final PatientDetails? patientDetails;
  final List<AnalysisResult> results;
  final String? disclaimer;

  const StructuredMedicalTable({
    super.key,
    this.patientDetails,
    required this.results,
    this.disclaimer,
  });

  @override
  State<StructuredMedicalTable> createState() => _StructuredMedicalTableState();
}

class _StructuredMedicalTableState extends State<StructuredMedicalTable> {
  bool _isTableView = true;

  @override
  Widget build(BuildContext context) {
    if (widget.results.isEmpty) {
      return const SizedBox.shrink();
    }

    final pt = widget.patientDetails ?? const PatientDetails();

    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // 1. Patient Details Banner
        _buildPatientDetailsBanner(pt),
        const SizedBox(height: 14),

        // 2. Section Header & View Toggle
        Row(
          children: [
            Container(
              padding: const EdgeInsets.all(8),
              decoration: BoxDecoration(
                color: AppColors.primaryLight.withValues(alpha: 0.15),
                borderRadius: BorderRadius.circular(10),
              ),
              child: const Icon(
                Icons.table_chart_rounded,
                color: AppColors.primary,
                size: 20,
              ),
            ),
            const SizedBox(width: 10),
            const Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Structured Medical Parameters & Analysis',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.bold,
                      color: AppColors.textPrimary,
                      letterSpacing: -0.2,
                    ),
                  ),
                  Text(
                    'Extracted biomarkers, validated ranges, alerts, and implications',
                    style: TextStyle(
                      fontSize: 11,
                      color: AppColors.textSecondary,
                    ),
                  ),
                ],
              ),
            ),
            SegmentedButton<bool>(
              segments: const [
                ButtonSegment<bool>(
                  value: true,
                  icon: Icon(Icons.table_rows_rounded, size: 16),
                  label: Text('Table', style: TextStyle(fontSize: 11)),
                ),
                ButtonSegment<bool>(
                  value: false,
                  icon: Icon(Icons.view_agenda_rounded, size: 16),
                  label: Text('Cards', style: TextStyle(fontSize: 11)),
                ),
              ],
              selected: {_isTableView},
              onSelectionChanged: (Set<bool> newSelection) {
                setState(() {
                  _isTableView = newSelection.first;
                });
              },
              style: SegmentedButton.styleFrom(
                visualDensity: VisualDensity.compact,
                selectedForegroundColor: Colors.white,
                selectedBackgroundColor: AppColors.primary,
              ),
            ),
          ],
        ),
        const SizedBox(height: 12),

        // 3. Render Table or Card View
        if (_isTableView)
          _buildDataTable(context, pt)
        else
          _buildCardListView(context, pt),
      ],
    );
  }

  Widget _buildPatientDetailsBanner(PatientDetails pt) {
    return Container(
      width: double.infinity,
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: const Color(0xFFF8FAFC),
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: const Color(0xFFE2E8F0)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              const Icon(Icons.badge_outlined, size: 18, color: AppColors.primary),
              const SizedBox(width: 8),
              const Text(
                'Report & Patient Details',
                style: TextStyle(
                  fontWeight: FontWeight.bold,
                  fontSize: 13,
                  color: AppColors.primaryDark,
                ),
              ),
              const Spacer(),
              Container(
                padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                decoration: BoxDecoration(
                  color: const Color(0xFFE0F2FE),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: const Text(
                  'Objective 3 Spec',
                  style: TextStyle(
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF0369A1),
                  ),
                ),
              ),
            ],
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 16,
            runSpacing: 8,
            children: [
              _buildDetailItem(Icons.person_outline, 'Patient Name', pt.name),
              _buildDetailItem(Icons.cake_outlined, 'Age', pt.effectiveAgeDisplay),
              _buildDetailItem(Icons.wc_outlined, 'Gender', pt.gender),
              _buildDetailItem(Icons.calendar_today_outlined, 'Date', pt.date),
              _buildDetailItem(Icons.local_hospital_outlined, 'Lab / Facility', pt.labName),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildDetailItem(IconData icon, String label, String value) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: AppColors.textSecondary),
        const SizedBox(width: 4),
        Text(
          '$label: ',
          style: const TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: AppColors.textSecondary,
          ),
        ),
        Text(
          value,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.bold,
            color: value == 'Not Available'
                ? AppColors.textMuted
                : AppColors.textPrimary,
          ),
        ),
      ],
    );
  }

  Widget _buildDataTable(BuildContext context, PatientDetails pt) {
    return Container(
      width: double.infinity,
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: AppColors.cardBorder),
        boxShadow: const [
          BoxShadow(
            color: Color(0x0A000000),
            blurRadius: 8,
            offset: Offset(0, 2),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(14),
        child: SingleChildScrollView(
          scrollDirection: Axis.horizontal,
          child: DataTable(
            headingRowColor: WidgetStateProperty.all(const Color(0xFFF1F5F9)),
            headingTextStyle: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.bold,
              color: AppColors.textPrimary,
            ),
            dataTextStyle: const TextStyle(fontSize: 12, color: AppColors.textPrimary),
            columnSpacing: 20,
            horizontalMargin: 16,
            columns: const [
              DataColumn(label: Text('Patient Details')),
              DataColumn(label: Text('Test Name')),
              DataColumn(label: Text('Observed Value')),
              DataColumn(label: Text('Unit')),
              DataColumn(label: Text('Reference Range')),
              DataColumn(label: Text('Status')),
              DataColumn(label: Text('Alert Message')),
              DataColumn(label: Text('Possible Health Implications')),
              DataColumn(label: Text('Precautions and Next Steps')),
            ],
            rows: widget.results.map((item) {
              return _buildDataRow(item, pt);
            }).toList(),
          ),
        ),
      ),
    );
  }

  DataRow _buildDataRow(AnalysisResult item, PatientDetails pt) {
    final status = _resolveStatus(item);
    final valStr = item.numericValue != null
        ? (item.numericValue!.truncateToDouble() == item.numericValue
            ? item.numericValue!.toInt().toString()
            : item.numericValue.toString())
        : (item.originalValueText ?? 'Not Available');
    final unitStr = item.normalizedUnit ?? item.unit ?? 'Not Available';
    final refStr = _formatReferenceRange(item);
    final alertMsg = item.alertMessage ?? _defaultAlert(item, status);
    final implications = item.possibleHealthImplications ?? _defaultImplications(item, status);
    final precautions = item.precautionsAndNextSteps ?? _defaultPrecautions(item, status);
    final patientSummary = pt.summaryText;

    return DataRow(
      cells: [
        DataCell(
          SizedBox(
            width: 140,
            child: Text(
              patientSummary,
              style: const TextStyle(fontSize: 11, fontWeight: FontWeight.w500),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
        DataCell(
          SizedBox(
            width: 140,
            child: Text(
              item.canonicalName ?? item.originalTestName,
              style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 12),
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
        DataCell(
          Text(
            valStr,
            style: const TextStyle(fontWeight: FontWeight.w600, fontSize: 12),
          ),
        ),
        DataCell(Text(unitStr, style: const TextStyle(fontSize: 11))),
        DataCell(
          SizedBox(
            width: 120,
            child: Text(refStr, style: const TextStyle(fontSize: 11)),
          ),
        ),
        DataCell(_buildStatusBadge(status)),
        DataCell(
          SizedBox(
            width: 220,
            child: Text(
              alertMsg,
              style: const TextStyle(fontSize: 11),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
        DataCell(
          SizedBox(
            width: 240,
            child: Text(
              implications,
              style: const TextStyle(fontSize: 11),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
        DataCell(
          SizedBox(
            width: 240,
            child: Text(
              precautions,
              style: const TextStyle(fontSize: 11),
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ),
      ],
    );
  }

  Widget _buildCardListView(BuildContext context, PatientDetails pt) {
    return Column(
      children: widget.results.map((item) {
        final status = _resolveStatus(item);
        final valStr = item.numericValue != null
            ? item.numericValue.toString()
            : (item.originalValueText ?? 'Not Available');
        final unitStr = item.normalizedUnit ?? item.unit ?? 'Not Available';
        final refStr = _formatReferenceRange(item);
        final alertMsg = item.alertMessage ?? _defaultAlert(item, status);
        final implications = item.possibleHealthImplications ?? _defaultImplications(item, status);
        final precautions = item.precautionsAndNextSteps ?? _defaultPrecautions(item, status);

        return Card(
          margin: const EdgeInsets.only(bottom: 12),
          elevation: 0,
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(14),
            side: BorderSide(color: _statusBorderColor(status)),
          ),
          child: Padding(
            padding: const EdgeInsets.all(14),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            item.canonicalName ?? item.originalTestName,
                            style: const TextStyle(
                              fontSize: 14,
                              fontWeight: FontWeight.bold,
                              color: AppColors.textPrimary,
                            ),
                          ),
                          const SizedBox(height: 2),
                          Text(
                            'Observed: $valStr $unitStr • Reference: $refStr',
                            style: const TextStyle(
                              fontSize: 12,
                              color: AppColors.textSecondary,
                            ),
                          ),
                        ],
                      ),
                    ),
                    _buildStatusBadge(status),
                  ],
                ),
                const SizedBox(height: 10),
                const Divider(height: 1, color: Color(0xFFF1F5F9)),
                const SizedBox(height: 10),

                // Alert Message
                _buildCardSection(
                  Icons.notification_important_outlined,
                  'Alert Message',
                  alertMsg,
                  _statusTextColor(status),
                ),
                const SizedBox(height: 8),

                // Health Implications
                _buildCardSection(
                  Icons.info_outline,
                  'Possible Health Implications',
                  implications,
                  AppColors.textPrimary,
                ),
                const SizedBox(height: 8),

                // Precautions & Next Steps
                _buildCardSection(
                  Icons.health_and_safety_outlined,
                  'Precautions & Next Steps',
                  precautions,
                  AppColors.textPrimary,
                ),
              ],
            ),
          ),
        );
      }).toList(),
    );
  }

  Widget _buildCardSection(IconData icon, String title, String content, Color contentColor) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Row(
          children: [
            Icon(icon, size: 14, color: AppColors.primary),
            const SizedBox(width: 6),
            Text(
              title,
              style: const TextStyle(
                fontSize: 11,
                fontWeight: FontWeight.bold,
                color: AppColors.textSecondary,
              ),
            ),
          ],
        ),
        const SizedBox(height: 3),
        Padding(
          padding: const EdgeInsets.only(left: 20),
          child: Text(
            content,
            style: TextStyle(
              fontSize: 12,
              color: contentColor,
              height: 1.35,
            ),
          ),
        ),
      ],
    );
  }

  String _resolveStatus(AnalysisResult item) {
    if (item.classification != null) {
      return item.classification!.value;
    }
    if (item.analysisStatus != 'SUCCESS') {
      return 'REQUIRES REVIEW';
    }
    return 'NORMAL';
  }

  String _formatReferenceRange(AnalysisResult item) {
    if (item.referenceRange != null) {
      final ref = item.referenceRange!;
      if (ref.normalLow != null && ref.normalHigh != null) {
        return '${ref.normalLow} - ${ref.normalHigh} ${ref.unit}';
      }
    }
    return 'Not Available';
  }

  Widget _buildStatusBadge(String status) {
    final upper = status.toUpperCase();
    Color bg;
    Color text;
    IconData icon;

    switch (upper) {
      case 'CRITICAL':
        bg = const Color(0xFFFEE2E2);
        text = const Color(0xFFB91C1C);
        icon = Icons.warning_rounded;
        break;
      case 'HIGH':
        bg = const Color(0xFFFEF3C7);
        text = const Color(0xFFB45309);
        icon = Icons.arrow_upward_rounded;
        break;
      case 'LOW':
        bg = const Color(0xFFDBEAFE);
        text = const Color(0xFF1D4ED8);
        icon = Icons.arrow_downward_rounded;
        break;
      case 'NORMAL':
        bg = const Color(0xFFDCFCE7);
        text = const Color(0xFF15803D);
        icon = Icons.check_circle_outline;
        break;
      default:
        bg = const Color(0xFFEDE9FE);
        text = const Color(0xFF6D28D9);
        icon = Icons.help_outline_rounded;
        break;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: text),
          const SizedBox(width: 4),
          Text(
            upper,
            style: TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.bold,
              color: text,
            ),
          ),
        ],
      ),
    );
  }

  Color _statusBorderColor(String status) {
    final upper = status.toUpperCase();
    if (upper == 'CRITICAL') return const Color(0xFFFCA5A5);
    if (upper == 'HIGH') return const Color(0xFFFCD34D);
    if (upper == 'LOW') return const Color(0xFF93C5FD);
    if (upper == 'NORMAL') return const Color(0xFF86EFAC);
    return const Color(0xFFDDD6FE);
  }

  Color _statusTextColor(String status) {
    final upper = status.toUpperCase();
    if (upper == 'CRITICAL') return const Color(0xFFB91C1C);
    if (upper == 'HIGH') return const Color(0xFFB45309);
    if (upper == 'LOW') return const Color(0xFF1D4ED8);
    if (upper == 'NORMAL') return const Color(0xFF15803D);
    return const Color(0xFF6D28D9);
  }

  String _defaultAlert(AnalysisResult item, String status) {
    final name = item.canonicalName ?? item.originalTestName;
    if (status == 'CRITICAL') return 'CRITICAL ALERT: $name is significantly outside normal range.';
    if (status == 'HIGH') return 'Elevated: $name is above normal reference range.';
    if (status == 'LOW') return 'Low: $name is below normal reference range.';
    if (status == 'NORMAL') return '$name is within normal physiological limits.';
    return '$name requires clinical verification against laboratory reference ranges.';
  }

  String _defaultImplications(AnalysisResult item, String status) {
    final name = item.canonicalName ?? item.originalTestName;
    if (status == 'HIGH' || status == 'CRITICAL') {
      return 'Elevated $name levels may suggest metabolic, inflammatory, or physiological adjustments.';
    }
    if (status == 'LOW') {
      return 'Low $name may indicate reduced production, nutritional deficiency, or increased loss.';
    }
    if (status == 'NORMAL') {
      return 'Biomarker is within expected clinical reference parameters.';
    }
    return 'Clinical relevance requires confirmation with the testing laboratory.';
  }

  String _defaultPrecautions(AnalysisResult item, String status) {
    if (status == 'CRITICAL') {
      return 'Urgent medical attention recommended. Please consult your physician immediately.';
    }
    if (status == 'HIGH' || status == 'LOW') {
      return 'Consult your healthcare provider for clinical review and repeat testing if advised.';
    }
    return 'Continue standard healthy lifestyle habits and regular medical checkups.';
  }
}
