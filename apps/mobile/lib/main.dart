import 'package:flutter/material.dart';
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_owner_screen.dart';
import 'screens/home_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/vehicle_add_screen.dart';
import 'screens/vehicle_detail_screen.dart';

void main() {
  runApp(const RoadGuruApp());
}

class RoadGuruApp extends StatelessWidget {
  const RoadGuruApp({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = ThemeData(
      colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2563EB)), // blue like your mockups
      useMaterial3: true,
      inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
    );

    return MaterialApp(
      title: 'Road Guru',
      theme: theme,
      debugShowCheckedModeBanner: false,
      initialRoute: '/',
      routes: {
        '/': (_) => const SplashScreen(),
        '/login': (_) => const LoginScreen(),
        '/register': (_) => const RegisterOwnerScreen(),
        '/home': (_) => const HomeScreen(),
        '/profile': (_) => const ProfileScreen(),
        '/vehicle-add': (_) => const VehicleAddScreen(),
        '/vehicle-detail': (_) => const VehicleDetailScreen(),
      },
    );
  }
}
