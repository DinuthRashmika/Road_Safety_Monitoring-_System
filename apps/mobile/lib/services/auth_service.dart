import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../core/token_storage.dart';
import '../models/token.dart';

class AuthService {
  // OAuth2PasswordRequestForm expects fields: username + password
  static Future<void> login({
    required String username, // email or NIC
    required String password,
  }) async {
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
    String? imagePath, // optional file path
  }) async {
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
