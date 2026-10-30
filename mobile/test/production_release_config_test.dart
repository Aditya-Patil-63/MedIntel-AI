import 'package:flutter_test/flutter_test.dart';
import 'package:medintel_mobile/core/constants/api_constants.dart';
import 'package:medintel_mobile/core/network/dio_client.dart';
import 'package:medintel_mobile/core/network/server_url_storage.dart';

void main() {
  setUp(() async {
    await ServerUrlStorage.clear();
    DioClient.resetRequestState();
  });

  tearDown(() async {
    await ServerUrlStorage.clear();
  });

  group('Production Release & Network Config Tests', () {
    test('ApiConstants productionUrl is the live Render backend', () {
      expect(
        ApiConstants.productionUrl,
        equals('https://medintel-backend-p0nf.onrender.com'),
      );
    });

    test('ApiConstants timeouts are generous for Render cold starts', () {
      expect(ApiConstants.coldStartTimeout.inSeconds, greaterThanOrEqualTo(90));
      expect(ApiConstants.geminiReceiveTimeout.inSeconds, greaterThanOrEqualTo(90));
      expect(ApiConstants.normalConnectTimeout.inSeconds, greaterThanOrEqualTo(10));
      expect(ApiConstants.normalReceiveTimeout.inSeconds, greaterThanOrEqualTo(30));
    });

    test('ServerUrlStorage correctly detects local vs cloud URLs', () {
      expect(ServerUrlStorage.isLocalUrl('http://127.0.0.1:8000'), isTrue);
      expect(ServerUrlStorage.isLocalUrl('http://localhost:8000'), isTrue);
      expect(ServerUrlStorage.isLocalUrl('http://10.0.2.2:8000'), isTrue);
      expect(ServerUrlStorage.isLocalUrl('http://10.20.43.105:8000'), isTrue);
      expect(ServerUrlStorage.isLocalUrl('http://192.168.1.10:8000'), isTrue);
      expect(ServerUrlStorage.isLocalUrl('https://medintel-backend-p0nf.onrender.com'), isFalse);
      expect(ServerUrlStorage.isLocalUrl('https://custom-domain.com'), isFalse);
    });

    test('ServerUrlStorage persists and retrieves custom cloud URLs', () async {
      await ServerUrlStorage.saveUrl('https://custom-medintel.example.com');
      final retrieved = ServerUrlStorage.getSavedUrlSync();
      expect(retrieved, equals('https://custom-medintel.example.com'));
    });

    test('DioClient initializes with effective activeBaseUrl', () {
      final client = DioClient();
      expect(client.dio.options.baseUrl, isNotEmpty);
      expect(client.dio.options.baseUrl, equals(DioClient.activeBaseUrl));
    });

    test('DioClient tracks first request and resets state correctly', () {
      expect(DioClient.hasSuccessfulRequest, isFalse);
      DioClient.resetRequestState();
      expect(DioClient.hasSuccessfulRequest, isFalse);
    });
  });
}
