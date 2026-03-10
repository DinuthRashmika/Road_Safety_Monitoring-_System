import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/notification_model.dart';

class NotificationService {

  
  static Future<List<NotificationModel>> getMyNotifications() async {
    try {
      final res = await ApiClient.dio.get('/api/notifications/');
      final list = (res.data as List)
          .map((e) => NotificationModel.fromJson(e as Map<String, dynamic>))
          .toList();
      return list;
    } on DioException catch (e) {
      throw Exception(
        e.response?.data is Map<String, dynamic>
            ? e.response?.data['detail']?.toString() ?? 'Failed to fetch notifications'
            : 'Failed to fetch notifications',
      );
    }
  }

  static Future<List<NotificationModel>> getProtectiveAlerts() async {
    try {
      final res = await ApiClient.dio.get('/api/protective-alerts/');
      final list = (res.data as List)
          .map((e) => NotificationModel.fromJson(e))
          .toList();
      return list;
    } on DioException catch (e) {
      throw Exception(
        e.response?.data['detail']?.toString() ?? 'Failed to fetch protective alerts',
      );
    }
  }

  static Future<void> markProtectiveAsRead(String id) async {
    try {
      await ApiClient.dio.put('/api/protective-alerts/$id/read');
    } catch (_) {}
  }

  static Future<void> markAsRead(String id) async {
    try {
      await ApiClient.dio.put('/api/notifications/$id/read');
    } catch (_) {}
  }
}

