class NotificationModel {
  final String id;
  final String vehiclePlate;
  final String message;
  final String location;
  final bool isRead;
  final DateTime createdAt;
  final String violationId;
  
  // These fields come from the "detailed info" in your backend notification_doc
  // Note: Your GET /api/notifications endpoint needs to ensure these are passed 
  // or parsed from the message if not explicitly in the top-level JSON.
  // Based on your backend code, the GET endpoint returns specific fields. 
  // We might need to parse the message or rely on violationId to fetch details.
  
  // For this implementation, we will assume standard fields.

  NotificationModel({
    required this.id,
    required this.vehiclePlate,
    required this.message,
    required this.location,
    required this.isRead,
    required this.createdAt,
    required this.violationId,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: json['id'] ?? '',
      vehiclePlate: json['vehiclePlate'] ?? '',
      message: json['message'] ?? '',
      location: json['location'] ?? 'Unknown',
      isRead: json['isRead'] ?? false,
      createdAt: DateTime.tryParse(json['createdAt'] ?? '') ?? DateTime.now(),
      violationId: json['violationId'] ?? '',
    );
  }
}