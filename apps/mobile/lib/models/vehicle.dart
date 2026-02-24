class Vehicle {
  final String id;
  final String ownerId;
  final String vehicleType;
  final String vehicleModel;
  final String registrationDate;
  final String plateNo;
  final Map<String, dynamic> images;

  Vehicle({
    required this.id,
    required this.ownerId,
    required this.vehicleType,
    required this.vehicleModel,
    required this.registrationDate,
    required this.plateNo,
    required this.images,
  });

  factory Vehicle.fromJson(Map<String, dynamic> j) => Vehicle(
    id: j['id'],
    ownerId: j['ownerId'],
    vehicleType: j['vehicleType'],
    vehicleModel: j['vehicleModel'],
    registrationDate: j['registrationDate'],
    plateNo: j['plateNo'],
    images: Map<String, dynamic>.from(j['images'] ?? {}),
  );
}
