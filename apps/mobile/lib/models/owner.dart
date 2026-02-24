class Owner {
  final String id;
  final String fullName;
  final String email;
  final String phone;
  final String address;
  final String nic;
  final String role;
  final String? imageUrl;

  Owner({
    required this.id,
    required this.fullName,
    required this.email,
    required this.phone,
    required this.address,
    required this.nic,
    required this.role,
    this.imageUrl,
  });

  factory Owner.fromJson(Map<String, dynamic> j) => Owner(
    id: j['id'],
    fullName: j['fullName'],
    email: j['email'],
    phone: j['phone'],
    address: j['address'],
    nic: j['nic'],
    role: j['role'],
    imageUrl: j['imageUrl'],
  );
}
