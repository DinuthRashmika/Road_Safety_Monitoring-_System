// lib/services/auth_service.dart

import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/token_storage.dart';
import '../models/token.dart';

class AuthService {
  
  // 1. Define the URL here temporarily
  static const String _baseUrl = 'http://192.168.1.60:8000';

  static Future<void> login({
    required String username, 
    required String password,
  }) async {
    
    // 2. Override the base URL for this request
    ApiClient.dio.options.baseUrl = _baseUrl; 

    final res = await ApiClient.dio.post(
      '/api/auth/login',
      data: FormData.fromMap({
        'username': username,
        'password': password,
      }),
      options: Options(contentType: Headers.formUrlEncodedContentType),
    );
    final token = TokenOut.fromJson(res.data);
    await TokenStorage.save(token.accessToken);
  }

  static Future<void> logout() => TokenStorage.clear();

  static Future<void> registerOwner({
    required String fullName,
    required String email,
    required String phone,
    required String address,
    required String nic,
    required String password,
    String? imagePath, 
  }) async {
    
    // 3. Override the base URL here too
    ApiClient.dio.options.baseUrl = _baseUrl;

    final form = FormData.fromMap({
      'fullName': fullName,
      'email': email,
      'phone': phone,
      'address': address,
      'nic': nic,
      'password': password,
      if (imagePath != null)
        'image': await MultipartFile.fromFile(imagePath, filename: 'owner.jpg'),
    });
    await ApiClient.dio.post('/api/auth/register-owner', data: form);
  }
}