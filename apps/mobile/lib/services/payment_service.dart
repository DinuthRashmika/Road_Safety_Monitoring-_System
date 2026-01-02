import 'package:flutter/material.dart';
import 'package:flutter_stripe/flutter_stripe.dart';
import 'package:dio/dio.dart';
import '../core/api_client.dart'; // Keep your existing import

class PaymentService {
  
  static Future<void> initializeStripe(String publishableKey) async {
    Stripe.publishableKey = publishableKey;
    //await Stripe.instance.applySettings();
  }

  static Future<String> createPaymentIntent(double amount) async {
    try {
      // API Client handles the base URL (http://10.0.2.2:8000 or similar)
      final response = await ApiClient.dio.post(
        '/api/payments/create-payment-intent',
        data: {
          'amount': amount,
          'currency': 'lkr',
        },
      );
      
      final clientSecret = response.data['clientSecret'];
      if (clientSecret == null) throw Exception('Client Secret is null');
      return clientSecret;
    } catch (e) {
      throw Exception('Failed to create payment intent: $e');
    }
  }

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

      // 3. Display the Payment Sheet
      await Stripe.instance.presentPaymentSheet();
      
      // If we reach here, payment was successful
      return true; 
    } on StripeException catch (e) {
      // User cancelled or card failed
      if (e.error.code == FailureCode.Canceled) {
         print("Payment Cancelled");
      } else {
         print('Stripe Error: ${e.error.localizedMessage}');
      }
      return false; 
    } catch (e) {
      print('General Error: $e');
      return false;
    }
  }

  static Future<void> markViolationAsPaid(String violationId) async {
    try {
      await ApiClient.dio.put('/api/payments/confirm-violation-payment/$violationId');
    } catch (e) {
      print("Error marking as paid in DB: $e");
      // Throwing so the UI knows it failed
      throw Exception("Database update failed");
    }
  }
}