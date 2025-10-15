import 'package:dio/dio.dart';
import '../core/api_client.dart';
import '../models/vehicle.dart';

class VehicleService {
  static Future<List<Vehicle>> mine() async {
    final res = await ApiClient.dio.get('/api/vehicles/mine');
    return (res.data as List).map((e) => Vehicle.fromJson(e)).toList();
  }

  static Future<Vehicle> create({
    required String vehicleType,
    required String vehicleModel,
    required String registrationDate, // YYYY-MM-DD
    required String plateNo,
    String? imageFront,
    String? imageBack,
    String? imageRight,
    String? imageLeft,
    String? imagePlate,
  }) async {
    final form = FormData.fromMap({
      'vehicleType': vehicleType,
      'vehicleModel': vehicleModel,
      'registrationDate': registrationDate,
      'plateNo': plateNo,
      if (imageFront != null)
        'image_front': await MultipartFile.fromFile(imageFront, filename: 'front.jpg'),
      if (imageBack != null)
        'image_back': await MultipartFile.fromFile(imageBack, filename: 'back.jpg'),
      if (imageRight != null)
        'image_right': await MultipartFile.fromFile(imageRight, filename: 'right.jpg'),
      if (imageLeft != null)
        'image_left': await MultipartFile.fromFile(imageLeft, filename: 'left.jpg'),
      if (imagePlate != null)
        'image_plate': await MultipartFile.fromFile(imagePlate, filename: 'plate.jpg'),
    });

    final res = await ApiClient.dio.post('/api/vehicles', data: form);
    return Vehicle.fromJson(res.data);
  }

  static Future<Vehicle> byId(String id) async {
    final res = await ApiClient.dio.get('/api/vehicles/$id');
    return Vehicle.fromJson(res.data);
  }
}
