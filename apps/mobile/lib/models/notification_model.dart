class NotificationModel {
  final String id;
  final String vehiclePlate;
  final String violationId;
  final String message;
  final String location;

  /// NEW: "violation_alert" | "protective_alert" | fallback
  final String type;

  /// Optional extra fields (your backend may or may not return these)
  final String violationType;
  final double fineAmount;
  final String? violationImage;

  final bool isRead;
  final DateTime createdAt;

  NotificationModel({
    required this.id,
    required this.vehiclePlate,
    required this.violationId,
    required this.message,
    required this.location,
    required this.type,
    required this.violationType,
    required this.fineAmount,
    this.violationImage,
    required this.isRead,
    required this.createdAt,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    // safe fine parsing
    final fine = (json['fineAmount'] is int)
        ? (json['fineAmount'] as int).toDouble()
        : (json['fineAmount'] is double)
            ? (json['fineAmount'] as double)
            : double.tryParse('${json['fineAmount']}') ?? 0.0;

    // type fallback if backend does not return it
    String t = (json['type'] ?? '').toString().trim();
    if (t.isEmpty) {
      final msg = (json['message'] ?? '').toString().toLowerCase();
      if (msg.contains('protective alert') || fine == 0.0) {
        t = 'protective_alert';
      } else {
        t = 'violation_alert';
      }
    }

    return NotificationModel(
      id: json['_id']?.toString() ?? json['id']?.toString() ?? '',
      vehiclePlate: json['vehiclePlate']?.toString() ?? '',
      violationId: json['violationId']?.toString() ?? '',
      message: json['message']?.toString() ?? '',
      location: json['location']?.toString() ?? 'Unknown Location',
      type: t,
      violationType: json['violationType']?.toString() ?? 'Unknown',
      fineAmount: fine,
      violationImage: json['violationImage']?.toString(),
      isRead: json['isRead'] == true,
      createdAt: json['createdAt'] != null
          ? DateTime.tryParse(json['createdAt'].toString()) ?? DateTime.now()
          : DateTime.now(),
    );
  }

  bool get isProtective => type == 'protective_alert';
}