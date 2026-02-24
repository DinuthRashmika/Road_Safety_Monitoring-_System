class NotificationModel {
  final String id;
  final String ownerId;
  final String vehiclePlate;
  final String violationId;
  final String message;
  final String location;

  // Detailed Info
  final String violationType;
  final double fineAmount;
  final String? violationImage; // Nullable to handle cases with no image

  final bool isRead;
  final DateTime createdAt;

  NotificationModel({
    required this.id,
    required this.ownerId,
    required this.vehiclePlate,
    required this.violationId,
    required this.message,
    required this.location,
    required this.violationType,
    required this.fineAmount,
    this.violationImage,
    required this.isRead,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      // MongoDB usually returns '_id', but we map it to 'id' for the app
      id: json['_id']?.toString() ?? json['id']?.toString() ?? '',

      ownerId: json['ownerId']?.toString() ?? '',
      vehiclePlate: json['vehiclePlate'] ?? '',
      violationId: json['violationId']?.toString() ?? '',

      message: json['message'] ?? '',
      location: json['location'] ?? 'Unknown Location',

      // Default to "Violation" if the type is missing
      violationType: json['violationType'] ?? 'Violation',

      // Safe double parsing
      fineAmount: (json['fineAmount'] is int)
          ? (json['fineAmount'] as int).toDouble()
          : (json['fineAmount'] ?? 0.0),

      // This will be the relative path (e.g., "detections/2026-02-23/img.jpg")
      violationImage: json['violationImage'],

      isRead: json['isRead'] ?? false,

      // specific date parsing to handle potentially different formats or nulls
      createdAt: json['createdAt'] != null
          ? DateTime.parse(json['createdAt'])
          : DateTime.now(),
    );
  }
}