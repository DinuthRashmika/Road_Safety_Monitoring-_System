import '../core/api_client.dart';
import '../core/token_storage.dart';   // ✅ ADD THIS
import '../models/owner.dart';

class OwnerService {
  static Future<Owner> me() async {
    final res = await ApiClient.dio.get('/api/owners/me');
    return Owner.fromJson(res.data);
  }

  static Future<Owner> update({
    String? fullName,
    String? phone,
    String? address,
  }) async {
    final res = await ApiClient.dio.put('/api/owners/me', data: {
      'fullName': fullName,
      'phone': phone,
      'address': address,
    });
    return Owner.fromJson(res.data);
  }

  // ✅ ADD THIS METHOD (Fix for red underline)
  static Future<void> logout() async {
    await TokenStorage.clear();  // clear saved JWT token
  }
}