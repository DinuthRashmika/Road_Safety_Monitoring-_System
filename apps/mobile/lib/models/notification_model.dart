class NotificationModel {
  final String id;
  final String message;
  final String vehiclePlate;
  final String location;
  final DateTime createdAt;
  final bool isRead;
  final String type;

  // violation details
  final String? violationType;
  final double? fineAmount;
  final String? violationImage;

  const NotificationModel({
    required this.id,
    required this.message,
    required this.vehiclePlate,
    required this.location,
    required this.createdAt,
    required this.isRead,
    required this.type,
    this.violationType,
    this.fineAmount,
    this.violationImage,
  });

  factory NotificationModel.fromJson(Map<String, dynamic> json) {
    return NotificationModel(
      id: (json['id'] ?? json['_id'] ?? '').toString(),
      message: (json['message'] ?? '').toString(),
      vehiclePlate: (json['vehiclePlate'] ?? json['plateNumber'] ?? '').toString(),
      location: (json['location'] ?? '').toString(),
      createdAt: DateTime.tryParse(
            (json['createdAt'] ?? json['detectionTime'] ?? '').toString(),
          ) ??
          DateTime.now(),
      isRead: json['isRead'] == true,
      type: (json['type'] ?? '').toString(),
      violationType: json['violationType']?.toString(),
      fineAmount: json['fineAmount'] == null
          ? null
          : double.tryParse(json['fineAmount'].toString()),
      violationImage: json['violationImage']?.toString(),
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'message': message,
      'vehiclePlate': vehiclePlate,
      'location': location,
      'createdAt': createdAt.toIso8601String(),
      'isRead': isRead,
      'type': type,
      'violationType': violationType,
      'fineAmount': fineAmount,
      'violationImage': violationImage,
    };
  }

  NotificationModel copyWith({
    String? id,
    String? message,
    String? vehiclePlate,
    String? location,
    DateTime? createdAt,
    bool? isRead,
    String? type,
    String? violationType,
    double? fineAmount,
    String? violationImage,
  }) {
    return NotificationModel(
      id: id ?? this.id,
      message: message ?? this.message,
      vehiclePlate: vehiclePlate ?? this.vehiclePlate,
      location: location ?? this.location,
      createdAt: createdAt ?? this.createdAt,
      isRead: isRead ?? this.isRead,
      type: type ?? this.type,
      violationType: violationType ?? this.violationType,
      fineAmount: fineAmount ?? this.fineAmount,
      violationImage: violationImage ?? this.violationImage,
    );
  }
}