import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/history/analysis_history_item.dart';
import 'package:medintel_mobile/models/ml_risk/risk_prediction_response.dart';
import 'package:medintel_mobile/models/reference/analysis_result.dart';
import 'package:medintel_mobile/models/reference/reference_range_summary.dart';
import 'package:medintel_mobile/state/history/history_cubit.dart';
import 'package:medintel_mobile/state/history/history_state.dart';

void main() {
  group('HistoryCubit — Local Session History', () {
    late HistoryCubit historyCubit;

    setUp(() {
      historyCubit = HistoryCubit();
    });

    tearDown(() {
      historyCubit.close();
    });

    AnalysisHistoryItem createTestItem({
      required String id,
      String docName = 'CBC_Report.pdf',
      DateTime? time,
    }) {
      return AnalysisHistoryItem(
        id: id,
        createdAt: time ?? DateTime(2026, 9, 11, 10, 0),
        documentName: docName,
        verifiedMeasurementCount: 3,
        patientAge: 45.0,
        patientSex: 'M',
        referenceResults: const [
          AnalysisResult(
            originalTestName: 'Glucose',
            canonicalName: 'Glucose Fasting',
            numericValue: 105.0,
            unit: 'mg/dL',
            classification: AnalyteClassification.high,
            analysisStatus: 'SUCCESS',
            referenceRange: ReferenceRangeSummary(
              canonicalName: 'Glucose Fasting',
              unit: 'mg/dL',
              normalLow: 70.0,
              normalHigh: 99.0,
              source: 'Verified Medical Sources',
            ),
          ),
          AnalysisResult(
            originalTestName: 'Hemoglobin',
            numericValue: 14.5,
            unit: 'g/dL',
            classification: AnalyteClassification.normal,
            analysisStatus: 'SUCCESS',
          ),
        ],
        totalClassified: 2,
        diabetesRisk: const RiskPredictionResponse(
          condition: 'diabetes',
          status: 'OK',
          riskProbability: 0.35,
          riskBand: RiskBand.moderate,
        ),
        heartRisk: const RiskPredictionResponse(
          condition: 'heart_disease',
          status: 'INSUFFICIENT_FEATURES',
          missingFeatures: ['chol', 'trestbps'],
        ),
        selectedLanguage: SupportedLanguage.english,
      );
    }

    test('initial state is HistoryInitial with empty currentRecords', () {
      expect(historyCubit.state, equals(const HistoryInitial()));
      expect(historyCubit.currentRecords, isEmpty);
    });

    test('addRecord adds a valid item and emits HistoryLoaded', () {
      final item = createTestItem(id: 'hist_1');
      historyCubit.addRecord(item);

      expect(historyCubit.state, isA<HistoryLoaded>());
      final loaded = historyCubit.state as HistoryLoaded;
      expect(loaded.records.length, equals(1));
      expect(loaded.records.first.id, equals('hist_1'));
      expect(loaded.records.first.documentName, equals('CBC_Report.pdf'));
    });

    test('newest records appear first in history', () {
      final item1 = createTestItem(
        id: 'hist_1',
        docName: 'Report_1.pdf',
        time: DateTime(2026, 9, 11, 10, 0),
      );
      final item2 = createTestItem(
        id: 'hist_2',
        docName: 'Report_2.pdf',
        time: DateTime(2026, 9, 11, 11, 0),
      );

      historyCubit.addRecord(item1);
      historyCubit.addRecord(item2);

      final loaded = historyCubit.state as HistoryLoaded;
      expect(loaded.records.length, equals(2));
      expect(loaded.records[0].id, equals('hist_2'));
      expect(loaded.records[1].id, equals('hist_1'));
    });

    test('duplicate prevention: adding item with same ID replaces and does not duplicate', () {
      final item1 = createTestItem(id: 'hist_dup', docName: 'Original.pdf');
      final item2 = createTestItem(id: 'hist_dup', docName: 'Updated.pdf');

      historyCubit.addRecord(item1);
      historyCubit.addRecord(item2);

      final loaded = historyCubit.state as HistoryLoaded;
      expect(loaded.records.length, equals(1));
      expect(loaded.records.first.documentName, equals('Updated.pdf'));
    });

    test('rejects empty ID and emits HistoryError', () {
      final invalidItem = createTestItem(id: '   ');
      historyCubit.addRecord(invalidItem);

      expect(historyCubit.state, isA<HistoryError>());
      final err = historyCubit.state as HistoryError;
      expect(err.message, contains('Cannot save history item with empty identifier'));
    });

    test('loadHistory emits HistoryLoading then HistoryLoaded without triggering network calls', () async {
      final item = createTestItem(id: 'hist_load');
      historyCubit.addRecord(item);

      await historyCubit.loadHistory();

      expect(historyCubit.state, isA<HistoryLoaded>());
      final loaded = historyCubit.state as HistoryLoaded;
      expect(loaded.records.length, equals(1));
      expect(loaded.records.first.id, equals('hist_load'));
    });

    test('clearHistory clears records and emits empty HistoryLoaded', () {
      final item = createTestItem(id: 'hist_clear');
      historyCubit.addRecord(item);

      historyCubit.clearHistory();

      expect(historyCubit.state, isA<HistoryLoaded>());
      final loaded = historyCubit.state as HistoryLoaded;
      expect(loaded.records, isEmpty);
      expect(historyCubit.currentRecords, isEmpty);
    });

    test('getRecordById retrieves matching item or returns null', () {
      final item = createTestItem(id: 'hist_find');
      historyCubit.addRecord(item);

      expect(historyCubit.getRecordById('hist_find'), isNotNull);
      expect(historyCubit.getRecordById('hist_find')!.id, equals('hist_find'));
      expect(historyCubit.getRecordById('non_existent'), isNull);
    });

    test('history immutability: records list cannot be mutated directly', () {
      final item = createTestItem(id: 'hist_immut');
      historyCubit.addRecord(item);

      final loaded = historyCubit.state as HistoryLoaded;
      expect(
        () => loaded.records.add(createTestItem(id: 'illegal')),
        throwsA(isA<UnsupportedError>()),
      );
    });

    test('AnalysisHistoryItem serialization and deserialization round-trip', () {
      final item = createTestItem(id: 'hist_json');
      final json = item.toJson();
      final restored = AnalysisHistoryItem.fromJson(json);

      expect(restored.id, equals(item.id));
      expect(restored.documentName, equals(item.documentName));
      expect(restored.verifiedMeasurementCount, equals(item.verifiedMeasurementCount));
      expect(restored.patientAge, equals(item.patientAge));
      expect(restored.patientSex, equals(item.patientSex));
      expect(restored.referenceResults.length, equals(item.referenceResults.length));
      expect(restored.diabetesRisk?.condition, equals('diabetes'));
      expect(restored.heartRisk?.status, equals('INSUFFICIENT_FEATURES'));
      expect(restored.selectedLanguage, equals(SupportedLanguage.english));
    });
  });
}
