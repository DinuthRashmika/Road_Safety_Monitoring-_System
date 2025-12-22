// lib/services/payment_service.dart
import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:dio/dio.dart';
import '../core/api_client.dart'; // Ensure this path matches your project structure

class PaymentService {
  static Future<void> initializeStripe(String publishableKey) async {
    Stripe.publishableKey = publishableKey;
    //await Stripe.instance.applySettings();
  }

  static Future<String> createPaymentIntent(double amount) async {
    try {
      final response = await ApiClient.dio.post(
        '/api/payments/create-payment-intent',
        data: {
          'amount': amount,
          'currency': 'lkr',
        },
      );
      
      final clientSecret = response.data?['clientSecret'];
      if (clientSecret == null) throw Exception('Client Secret is null');
      return clientSecret;
    } catch (e) {
      throw Exception('Failed to create payment intent: $e');
    }
  }

  // RENAMED to makePayment to reflect that it shows the sheet
  static Future<bool> makePayment(double amount, String vehicleDetails) async {
    try {
      // 1. Get Client Secret from Backend
      final clientSecret = await createPaymentIntent(amount);

      // 2. Initialize the Payment Sheet
      await Stripe.instance.initPaymentSheet(
        paymentSheetParameters: SetupPaymentSheetParameters(
          paymentIntentClientSecret: clientSecret,
          merchantDisplayName: 'Road Guru App',
          style: ThemeMode.light,
          appearance: const PaymentSheetAppearance(
            colors: PaymentSheetAppearanceColors(
              primary: Color(0xFF2563EB),
            ),
          ),
        ),
      );

      // 3. DISPLAY The Payment Sheet (This was missing!)
      await Stripe.instance.presentPaymentSheet();
      
      return true; // Payment successful
    } on StripeException catch (e) {
      // User cancelled or card failed
      print('Stripe Error: ${e.error.localizedMessage}');
      return false; 
    } catch (e) {
      print('General Error: $e');
      return false;
    }
  }

  static Future<void> markViolationAsPaid(String violationId) async {
    await ApiClient.dio.put('/api/payments/confirm-violation-payment/$violationId');
  }
}