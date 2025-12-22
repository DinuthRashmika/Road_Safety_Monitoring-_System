import 'package:dio/dio.dart';
import '../core/api_client.dart'; // Ensure this points to your configured Dio client
import '../models/notification_model.dart';

class NotificationService {
  
  // Fetch all notifications for the logged-in user
  static Future<List<NotificationModel>> getMyNotifications() async {
    try {
      final res = await ApiClient.dio.get('/api/notifications/');
      return (res.data as List)
          .map((e) => NotificationModel.fromJson(e))
          .toList();
    } on DioException catch (e) {
      throw Exception(e.response?.data['detail'] ?? 'Failed to fetch notifications');
    }
  }

  // Mark a specific notification as read
  static Future<void> markAsRead(String id) async {
    try {
      await ApiClient.dio.put('/api/notifications/$id/read');
    } catch (e) {
      // Handle error silently or log it
      print("Error marking as read: $e");
    }
  }
}