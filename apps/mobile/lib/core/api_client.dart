import 'package:dio/dio.dart';
import 'config.dart';
import 'token_storage.dart';

class ApiClient {
  static final Dio _dio = Dio(
    BaseOptions(
      baseUrl: AppConfig.baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 30),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ),
  )..interceptors.addAll([
    InterceptorsWrapper(
      onRequest: (options, handler) async {
        print('🌐 Making request to: ${options.baseUrl}${options.path}');
        final token = await TokenStorage.read();
        if (token != null) {
          options.headers['Authorization'] = 'Bearer $token';
        }
        handler.next(options);
      },
      onError: (DioException error, handler) async {
        print('❌ API Error: ${error.type}');
        print('❌ URL: ${error.requestOptions.uri}');
        print('❌ Message: ${error.message}');
        print('❌ Response: ${error.response?.data}');
        handler.next(error);
      },
    ),
    LogInterceptor(
      request: true,
      requestHeader: true,
      requestBody: true,
      responseHeader: true,
      responseBody: true,
      logPrint: (object) => print('📡 $object'),
    ),
  ]);

  static Dio get dio => _dio;

  // Helper method to test connection
  static Future<bool> testConnection() async {
    try {
      final response = await _dio.get('/');
      return response.statusCode == 200;
    } catch (e) {
      print('Connection test failed: $e');
      return false;
    }
  }
}