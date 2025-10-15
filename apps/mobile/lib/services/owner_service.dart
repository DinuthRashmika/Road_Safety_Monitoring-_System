import '../core/api_client.dart';
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
}
