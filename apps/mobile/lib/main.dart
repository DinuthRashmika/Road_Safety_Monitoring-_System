import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'services/payment_service.dart';

// ... keep your other screen imports ...
import 'screens/splash_screen.dart';
import 'screens/login_screen.dart';
import 'screens/register_owner_screen.dart';
import 'screens/home_screen.dart';
import 'screens/profile_screen.dart';
import 'screens/vehicle_add_screen.dart';
import 'screens/vehicle_detail_screen.dart';
import 'screens/vehicles_screen.dart';
import 'screens/violations_screen.dart';

// ✅ add these (only)
import 'screens/start_trip_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Initialize Stripe with your PUBLISHABLE Key
  await PaymentService.initializeStripe(
    'pk_test_51ShA9KBSOx34RK9GubYkjaMDWdHtXrCzKOqkm0kJyDEw2x4P9toIzs2QwI0h9P3Cwau6uYbzY7uHQV5Dd4NEGhjD00XZwLgzVp',
  );

  runApp(const RoadGuruApp());
}

class RoadGuruApp extends StatelessWidget {
  const RoadGuruApp({super.key});

  @override
  Widget build(BuildContext context) {
    final theme = ThemeData(
      colorScheme: ColorScheme.fromSeed(
        seedColor: const Color(0xFF2563EB),
        primary: const Color(0xFF2563EB),
        secondary: const Color(0xFF1D4ED8),
      ),
      useMaterial3: true,
      inputDecorationTheme: const InputDecorationTheme(
        border: OutlineInputBorder(),
        filled: true,
        fillColor: Colors.white,
      ),
      appBarTheme: const AppBarTheme(
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        elevation: 0,
        centerTitle: false,
      ),
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
        '/vehicles': (context) => const VehiclesScreen(),
        '/violations': (context) => const ViolationsScreen(),
        '/forgot': (context) => Scaffold(
              appBar: AppBar(title: const Text('Reset Password')),
              body: const Center(child: Text('Password Reset Feature Coming Soon')),
            ),

        // ✅ NOW Home Live Monitoring button goes to StartTripScreen
        '/monitor': (context) => const StartTripScreen(),
      },
    );
  }
}