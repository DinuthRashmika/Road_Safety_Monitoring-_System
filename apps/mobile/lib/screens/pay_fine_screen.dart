import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/notification_model.dart';

class PayFineScreen extends StatefulWidget {
  final NotificationModel notification;
  final double amount;

  const PayFineScreen({
    super.key,
    required this.notification,
    required this.amount,
  });

  @override
  State<PayFineScreen> createState() => _PayFineScreenState();
}

class _PayFineScreenState extends State<PayFineScreen> {
  bool _rememberCard = false;
  bool _isLoading = false;

  // Controllers
  final _nameController = TextEditingController(text: "John Doe");
  final _numberController = TextEditingController();
  final _expiryController = TextEditingController();
  final _cvvController = TextEditingController();

  // ✅ Dummy success popup
  Future<void> _showPaymentSuccessDialog(String totalDisplay) async {
    return showDialog(
      context: context,
      barrierDismissible: false,
      builder: (ctx) {
        return AlertDialog(
          backgroundColor: Colors.grey.shade900,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
          title: const Text(
            "Payment Successful",
            style: TextStyle(color: Colors.white, fontWeight: FontWeight.w800),
          ),
          content: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.check_circle, color: Color(0xFF22C55E), size: 64),
              const SizedBox(height: 12),
              Text(
                "Your fine has been paid successfully.\nTotal: $totalDisplay",
                textAlign: TextAlign.center,
                style: TextStyle(color: Colors.grey.shade300),
              ),
            ],
          ),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx),
              child: const Text(
                "OK",
                style: TextStyle(color: Color(0xFF60A5FA), fontWeight: FontWeight.w700),
              ),
            ),
          ],
        );
      },
    );
  }

  // ✅ Dummy payment process
  Future<void> _processPayment() async {
    setState(() => _isLoading = true);

    // total for popup
    final currencyFormat = NumberFormat("#,##0", "en_US");
    final serviceFee = 500.0;
    final totalDisplay = "LKR ${currencyFormat.format(widget.amount + serviceFee)}";

    // ✅ simulate short delay (dummy)
    await Future.delayed(const Duration(seconds: 1));

    if (!mounted) return;

    // ✅ show success popup
    await _showPaymentSuccessDialog(totalDisplay);

    if (!mounted) return;

    // ✅ go back + tell previous screen payment success
    Navigator.pop(context, true);

    if (mounted) setState(() => _isLoading = false);
  }

  @override
  Widget build(BuildContext context) {
    // Format fine amount for display
    final currencyFormat = NumberFormat("#,##0", "en_US");
    final fineDisplay = "LKR ${currencyFormat.format(widget.amount)}";
    final serviceFee = 500.0;
    final totalDisplay = "LKR ${currencyFormat.format(widget.amount + serviceFee)}";

    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        elevation: 0,
        centerTitle: true,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new, color: Colors.white, size: 20),
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Pay Fine',
          style: TextStyle(color: Colors.white, fontWeight: FontWeight.w700, fontSize: 18),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.help_outline, color: Colors.white),
            onPressed: () {},
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.all(20),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // 1. Summary Card
            Container(
              width: double.infinity,
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.grey.shade900,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.grey.shade800),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      Text(
                        "Speeding",
                        style: TextStyle(color: Colors.grey.shade400, fontSize: 14),
                      ),
                      Text(
                        "Due in 2 days",
                        style: TextStyle(
                          color: Colors.red.shade400,
                          fontSize: 12,
                          fontWeight: FontWeight.bold,
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  Text(
                    widget.notification.vehiclePlate,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Colors.white),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    "${DateFormat('MMM d, yyyy').format(widget.notification.createdAt)} • ${widget.notification.location}",
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                  ),
                  const SizedBox(height: 16),
                  Text(
                    fineDisplay,
                    style: const TextStyle(fontSize: 24, fontWeight: FontWeight.w800, color: Colors.white),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    "Fine: LKR ${currencyFormat.format(widget.amount)} • Service Fee: LKR 500",
                    style: TextStyle(color: Colors.grey.shade400, fontSize: 12),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 30),

            // 2. Payment Method Tabs
            const Text(
              "Payment Method",
              style: TextStyle(fontSize: 16, fontWeight: FontWeight.w700, color: Colors.white),
            ),
            const SizedBox(height: 16),
            Row(
              children: [
                _buildTab("Card", isActive: true),
                const SizedBox(width: 20),
                _buildTab("Saved Cards", isActive: false),
                const SizedBox(width: 20),
                _buildTab("Mobile/UPI", isActive: false),
              ],
            ),
            const Divider(height: 1, color: Color(0xFF333333)),
            const SizedBox(height: 24),

            // 3. Card Form
            Container(
              padding: const EdgeInsets.all(20),
              decoration: BoxDecoration(
                color: Colors.grey.shade900,
                borderRadius: BorderRadius.circular(20),
                border: Border.all(color: Colors.grey.shade800),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.credit_card, color: Colors.grey.shade400),
                      const SizedBox(width: 10),
                      Container(width: 24, height: 16, color: Colors.grey.shade600),
                      const SizedBox(width: 10),
                      Container(width: 24, height: 16, color: Colors.grey.shade600),
                    ],
                  ),
                  const SizedBox(height: 20),

                  _buildLabel("Cardholder Name*"),
                  _buildTextField(hint: "John Doe", controller: _nameController),
                  const SizedBox(height: 16),

                  _buildLabel("Card Number*"),
                  _buildTextField(
                    hint: "0000 0000 0000 0000",
                    controller: _numberController,
                    suffixIcon: Icons.credit_card,
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildLabel("Expiry*"),
                            _buildTextField(hint: "MM/YY", controller: _expiryController),
                          ],
                        ),
                      ),
                      const SizedBox(width: 16),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            _buildLabel("CVV*"),
                            _buildTextField(
                              hint: "•••",
                              controller: _cvvController,
                              suffixIcon: Icons.visibility_off_outlined,
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 16),

                  Row(
                    children: [
                      SizedBox(
                        height: 24,
                        width: 24,
                        child: Checkbox(
                          value: _rememberCard,
                          activeColor: const Color(0xFF2563EB),
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(4)),
                          onChanged: (val) => setState(() => _rememberCard = val!),
                        ),
                      ),
                      const SizedBox(width: 8),
                      Text(
                        "Remember this card",
                        style: TextStyle(fontSize: 14, fontWeight: FontWeight.w500, color: Colors.grey.shade300),
                      ),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // 4. Total and Action
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: Colors.grey.shade800),
              ),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    "Total Payable",
                    style: TextStyle(fontSize: 14, fontWeight: FontWeight.w600, color: Colors.grey),
                  ),
                  Text(
                    totalDisplay,
                    style: const TextStyle(fontSize: 18, fontWeight: FontWeight.w800, color: Color(0xFF60A5FA)),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 24),

            // Pay Now Button
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                onPressed: _isLoading ? null : _processPayment,
                icon: _isLoading
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const Icon(Icons.credit_card, color: Colors.white),
                label: Text(
                  _isLoading ? "Processing..." : "Pay Now",
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Colors.white),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: const Color(0xFF2563EB),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
                  elevation: 0,
                ),
              ),
            ),
            const SizedBox(height: 16),

            SizedBox(
              width: double.infinity,
              height: 56,
              child: OutlinedButton(
                onPressed: () {},
                style: OutlinedButton.styleFrom(
                  side: const BorderSide(color: Color(0xFF2563EB)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(28)),
                  backgroundColor: Colors.transparent,
                ),
                child: const Text(
                  "Use Saved Card",
                  style: TextStyle(fontSize: 16, fontWeight: FontWeight.bold, color: Color(0xFF2563EB)),
                ),
              ),
            ),
            const SizedBox(height: 24),

            Center(
              child: Text(
                "By paying you agree to the Terms & Refund Policy.",
                style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
              ),
            ),
            const SizedBox(height: 8),
            Row(
              mainAxisAlignment: MainAxisAlignment.center,
              children: [
                Icon(Icons.lock_outline, size: 14, color: Colors.grey.shade500),
                const SizedBox(width: 4),
                Text(
                  "256-bit encrypted",
                  style: TextStyle(fontSize: 12, color: Colors.grey.shade500),
                ),
              ],
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  // Helper Widgets
  Widget _buildTab(String title, {required bool isActive}) {
    return Column(
      children: [
        Text(
          title,
          style: TextStyle(
            fontSize: 14,
            fontWeight: FontWeight.w600,
            color: isActive ? const Color(0xFF60A5FA) : Colors.grey.shade500,
          ),
        ),
        const SizedBox(height: 8),
        Container(
          height: 2,
          width: 40,
          color: isActive ? const Color(0xFF60A5FA) : Colors.transparent,
        ),
      ],
    );
  }

  Widget _buildLabel(String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 8.0),
      child: Text(
        text,
        style: TextStyle(fontSize: 13, fontWeight: FontWeight.w700, color: Colors.grey.shade300),
      ),
    );
  }

  Widget _buildTextField({
    required String hint,
    required TextEditingController controller,
    IconData? suffixIcon,
  }) {
    return TextField(
      controller: controller,
      style: const TextStyle(color: Colors.white),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: TextStyle(color: Colors.grey.shade500, fontSize: 14),
        filled: true,
        fillColor: Colors.grey.shade800,
        contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade700),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: BorderSide(color: Colors.grey.shade700),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(12),
          borderSide: const BorderSide(color: Color(0xFF2563EB), width: 1.5),
        ),
        suffixIcon: suffixIcon != null ? Icon(suffixIcon, color: Colors.grey.shade400) : null,
      ),
    );
  }
}
