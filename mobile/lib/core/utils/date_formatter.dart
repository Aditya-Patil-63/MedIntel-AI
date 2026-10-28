/// Utility functions for displaying patient-friendly dates and times in local timezone.
library;

const List<String> _kMonthNames = [
  'Jan',
  'Feb',
  'Mar',
  'Apr',
  'May',
  'Jun',
  'Jul',
  'Aug',
  'Sep',
  'Oct',
  'Nov',
  'Dec',
];

/// Formats a [DateTime] into standard user-facing format: "27 Oct 2026, 7:45 PM".
/// Always converts UTC or arbitrary timestamps into the device's local timezone.
String formatHistoryTimestamp(DateTime dateTime) {
  final local = dateTime.toLocal();
  final day = local.day;
  final month = (local.month >= 1 && local.month <= 12)
      ? _kMonthNames[local.month - 1]
      : 'Unknown';
  final year = local.year;

  final hour24 = local.hour;
  final minute = local.minute.toString().padLeft(2, '0');
  final period = hour24 >= 12 ? 'PM' : 'AM';
  final hour12 = hour24 == 0 ? 12 : (hour24 > 12 ? hour24 - 12 : hour24);

  return '$day $month $year, $hour12:$minute $period';
}

/// Formats a [DateTime] into a concise date only: "27 Oct 2026".
String formatHistoryDate(DateTime dateTime) {
  final local = dateTime.toLocal();
  final day = local.day;
  final month = (local.month >= 1 && local.month <= 12)
      ? _kMonthNames[local.month - 1]
      : 'Unknown';
  final year = local.year;
  return '$day $month $year';
}
