import 'package:flutter/material.dart';
import '../core/theme/app_colors.dart';
import '../models/reference/editable_measurement.dart';

/// Dialog for editing an existing measurement or adding a new one.
class MeasurementEditDialog extends StatefulWidget {
  final EditableMeasurement? measurement;
  final void Function(String testName, dynamic value, String? unit) onSave;

  const MeasurementEditDialog({
    super.key,
    this.measurement,
    required this.onSave,
  });

  @override
  State<MeasurementEditDialog> createState() => _MeasurementEditDialogState();
}

class _MeasurementEditDialogState extends State<MeasurementEditDialog> {
  final _formKey = GlobalKey<FormState>();
  late final TextEditingController _nameController;
  late final TextEditingController _valueController;
  late final TextEditingController _unitController;

  @override
  void initState() {
    super.initState();
    _nameController = TextEditingController(
      text: widget.measurement?.testName ?? '',
    );
    _valueController = TextEditingController(
      text: widget.measurement?.value?.toString() ?? '',
    );
    _unitController = TextEditingController(
      text: widget.measurement?.unit ?? '',
    );
  }

  @override
  void dispose() {
    _nameController.dispose();
    _valueController.dispose();
    _unitController.dispose();
    super.dispose();
  }

  void _submit() {
    if (_formKey.currentState?.validate() ?? false) {
      final name = _nameController.text.trim();
      final valStr = _valueController.text.trim();
      final unit = _unitController.text.trim();

      // Convert to number if numeric, else string
      dynamic parsedVal = double.tryParse(valStr) ?? valStr;

      widget.onSave(name, parsedVal, unit.isNotEmpty ? unit : null);
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final isEditing = widget.measurement != null;

    return AlertDialog(
      title: Row(
        children: [
          Icon(
            isEditing ? Icons.edit : Icons.add_circle_outline,
            color: AppColors.primary,
          ),
          const SizedBox(width: 8),
          Text(isEditing ? 'Edit Measurement' : 'Add Measurement'),
        ],
      ),
      content: SingleChildScrollView(
        child: Form(
          key: _formKey,
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              TextFormField(
                controller: _nameController,
                decoration: const InputDecoration(
                  labelText: 'Test / Analyte Name *',
                  hintText: 'e.g. Fasting Blood Glucose, Hemoglobin',
                  border: OutlineInputBorder(),
                ),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Test name is required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _valueController,
                decoration: const InputDecoration(
                  labelText: 'Observed Value *',
                  hintText: 'e.g. 126 or 14.5',
                  border: OutlineInputBorder(),
                ),
                keyboardType: const TextInputType.numberWithOptions(decimal: true),
                validator: (v) =>
                    (v == null || v.trim().isEmpty) ? 'Value is required' : null,
              ),
              const SizedBox(height: 12),
              TextFormField(
                controller: _unitController,
                decoration: const InputDecoration(
                  labelText: 'Unit of Measurement',
                  hintText: 'e.g. mg/dL, g/dL, %',
                  border: OutlineInputBorder(),
                ),
              ),
            ],
          ),
        ),
      ),
      actions: [
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cancel'),
        ),
        ElevatedButton(
          onPressed: _submit,
          child: Text(isEditing ? 'Save Changes' : 'Add'),
        ),
      ],
    );
  }
}
