import 'package:dio/dio.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/models/common/enums.dart';
import 'package:medintel_mobile/models/ml_risk/diabetes_risk_request.dart';
import 'package:medintel_mobile/models/reference/batch_analysis.dart';
import 'package:medintel_mobile/models/reference/measurement_input.dart';
import 'package:medintel_mobile/services/api_service.dart';

void main() {
  late Dio dio;
  late ApiService apiService;

  setUp(() {
    dio = Dio(BaseOptions(baseUrl: 'http://test-server:8000'));
    // Interceptor to unwrap exceptions
    dio.interceptors.add(
      InterceptorsWrapper(
        onError: (e, handler) {
          handler.next(e);
        },
      ),
    );
    apiService = ApiServiceImpl(dio: dio);
  });

  group('ApiService & DioClient Error Mapping', () {
    test('Health check parses response successfully', () async {
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            handler.resolve(
              Response(
                requestOptions: options,
                data: {'status': 'ok', 'app': 'MedIntel AI'},
                statusCode: 200,
              ),
            );
          },
        ),
      );

      final health = await apiService.getHealth();
      expect(health['status'], 'ok');
      expect(health['app'], 'MedIntel AI');
    });

    test('Batch analysis sends structured measurements', () async {
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            expect(options.path, '/api/v1/reference/analyze');
            expect(options.contentType, 'application/json');
            handler.resolve(
              Response(
                requestOptions: options,
                data: {
                  'success': true,
                  'total_submitted': 1,
                  'total_classified': 1,
                  'results': [
                    {
                      'original_test_name': 'Glucose',
                      'classification': 'NORMAL',
                      'analysis_status': 'SUCCESS',
                    }
                  ],
                },
                statusCode: 200,
              ),
            );
          },
        ),
      );

      final response = await apiService.analyzeBatch(
        const BatchAnalysisRequest(
          measurements: [
            MeasurementInput(testName: 'Glucose', value: 95.0, isUserVerified: true),
          ],
        ),
      );

      expect(response.success, true);
      expect(response.totalClassified, 1);
      expect(response.results.first.classification, AnalyteClassification.normal);
    });

    test('predictDiabetesRisk sends features and receives prediction', () async {
      dio.interceptors.add(
        InterceptorsWrapper(
          onRequest: (options, handler) {
            expect(options.path, '/api/v1/ml/diabetes-risk');
            handler.resolve(
              Response(
                requestOptions: options,
                data: {
                  'condition': 'diabetes',
                  'status': 'OK',
                  'risk_probability': 0.22,
                  'risk_band': 'LOW',
                  'model_name': 'rf_diabetes',
                  'supplied_features_count': 8,
                  'required_features_count': 8,
                },
                statusCode: 200,
              ),
            );
          },
        ),
      );

      final pred = await apiService.predictDiabetesRisk(
        const DiabetesRiskRequest(
          glucose: 95,
          isUserVerified: true,
        ),
      );

      expect(pred.condition, 'diabetes');
      expect(pred.riskBand, RiskBand.low);
      expect(pred.riskProbability, 0.22);
    });
  });
}
