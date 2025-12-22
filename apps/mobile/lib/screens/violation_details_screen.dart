import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/notification_model.dart';
import '../services/payment_service.dart';

class ViolationDetailsScreen extends StatefulWidget {
  final NotificationModel notification;

  const ViolationDetailsScreen({super.key, required this.notification});

  @override
  State<ViolationDetailsScreen> createState() => _ViolationDetailsScreenState();
}

class _ViolationDetailsScreenState extends State<ViolationDetailsScreen> {
  // State to track if payment is successful
  bool _isPaid = false; 
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    // Optional: Check if notification model already has a "paid" status passed in
    // _isPaid = widget.notification.isPaid; 
  }

  // Extract Fine Amount (Number) from String
  double _getFineAmountValue() {
    final regex = RegExp(r'([0-9]+)');
    final match = regex.firstMatch(widget.notification.message); // Looks for numbers
    if (match != null) {
      return double.tryParse(match.group(1)!) ?? 1000.0;
    }
    return 1000.0; // Default fallback
  }

  // Extract Display String
  String _extractFineDisplay() {
    final regex = RegExp(r'LKR\s*([0-9.,]+)');
    final match = regex.firstMatch(widget.notification.message);
    return match != null ? 'LKR ${match.group(1)}' : 'LKR -';
  }

  String _extractType() {
    if (widget.notification.message.contains("'")) {
      final start = widget.notification.message.indexOf("'") + 1;
      final end = widget.notification.message.lastIndexOf("'");
      if (start > 0 && end > start) {
        return widget.notification.message.substring(start, end).toUpperCase();
      }
    }
    return "VIOLATION";
  }

  Future<void> _handlePayment() async {
    setState(() => _isLoading = true);

    final amount = _getFineAmountValue();

    // --- CHANGED HERE ---
    // We use the boolean return from makePayment instead of try/catch
    bool success = await PaymentService.makePayment(
      amount,
      widget.notification.vehiclePlate,
    );

    if (success) {
      try {
        // Payment successful, now update backend
        await PaymentService.markViolationAsPaid(widget.notification.violationId);

        // Update UI
        setState(() {
          _isPaid = true;
        });

        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Payment Successful!'),
              backgroundColor: Colors.green,
            ),
          );
        }
      } catch (e) {
        // Backend update failed
        if (mounted) {
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(content: Text('Error updating database: $e')),
          );
        }
      }
    } else {
      // Payment failed or cancelled
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('Payment Cancelled or Failed'),
            backgroundColor: Colors.red,
          ),
        );
      }
    }
    // --- END CHANGE ---

    if (mounted) setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    final fineAmount = _extractFineDisplay();
    final type = _extractType();

    // COLOR LOGIC: Green if paid, Red/Pink if unpaid
    final statusColor = _isPaid ? const Color(0xFF16A34A) : const Color(0xFFDC2626);
    final statusBgColor = _isPaid ? const Color(0xFFDCFCE7) : const Color(0xFFFEE2E2);
    final statusText = _isPaid ? 'PAID' : 'UNPAID';

    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        title: const Text(
          'Violation Details',
          style: TextStyle(fontWeight: FontWeight.w800, fontSize: 20, color: Colors.black87),
        ),
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Violation Header
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE6E9EF)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Expanded(
                        child: Text(
                          type,
                          style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Colors.black87),
                        ),
                      ),
                      // DYNAMIC BADGE
                      Container(
                        padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                        decoration: BoxDecoration(
                          color: statusBgColor,
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: Text(
                          statusText,
                          style: TextStyle(color: statusColor, fontSize: 12, fontWeight: FontWeight.w600),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    '${widget.notification.vehiclePlate} • ${DateFormat('MMM d, yyyy • h:mm a').format(widget.notification.createdAt.toLocal())}',
                    style: const TextStyle(color: Colors.black54, fontSize: 14),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    widget.notification.location,
                    style: const TextStyle(color: Colors.black54, fontSize: 14),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Message Body
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE6E9EF)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text("Official Notice", style: TextStyle(fontWeight: FontWeight.bold)),
                  const SizedBox(height: 8),
                  Text(
                    widget.notification.message,
                    style: const TextStyle(fontSize: 16, height: 1.5, color: Colors.black87),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Fine Information
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE6E9EF)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    fineAmount,
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Colors.black87),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      const Icon(Icons.fingerprint_outlined, size: 14, color: Colors.black54),
                      const SizedBox(width: 4),
                      Text(
                        'Ref ID: ${widget.notification.id.substring(0, 8).toUpperCase()}',
                        style: const TextStyle(fontSize: 14, color: Colors.black54),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 20),

            // Action Buttons
            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                // Disable button if already paid
                onPressed: (_isPaid || _isLoading) ? null : _handlePayment,
                
                icon: _isLoading 
                    ? const SizedBox(width: 20, height: 20, child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2)) 
                    : Icon(_isPaid ? Icons.check_circle : Icons.payment_outlined, color: Colors.white),
                    
                label: Text(
                  _isPaid ? 'Fine Paid Successfully' : 'Pay Fine Now', 
                  style: const TextStyle(color: Colors.white)
                ),
                
                style: ElevatedButton.styleFrom(
                  backgroundColor: _isPaid ? const Color(0xFF16A34A) : const Color(0xFF2563EB),
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                  disabledBackgroundColor: _isPaid ? const Color(0xFF16A34A).withOpacity(0.8) : Colors.grey,
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}