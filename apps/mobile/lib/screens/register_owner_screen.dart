import 'dart:io';
import 'package:flutter/gestures.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:dotted_border/dotted_border.dart';
import '../services/auth_service.dart';

class RegisterOwnerScreen extends StatefulWidget {
  const RegisterOwnerScreen({super.key});
  @override
  State<RegisterOwnerScreen> createState() => _RegisterOwnerScreenState();
}

class _RegisterOwnerScreenState extends State<RegisterOwnerScreen> {
  final _formKey = GlobalKey<FormState>();

  final _name = TextEditingController();
  final _email = TextEditingController();
  final _phone = TextEditingController();
  final _address = TextEditingController();
  final _nic = TextEditingController();
  final _password = TextEditingController();

  bool _loading = false;
  bool _obscure = true;
  bool _agree = false;
  String? _imgPath;

  Future<void> _pickImage() async {
    final x = await ImagePicker().pickImage(
      source: ImageSource.gallery,
      imageQuality: 85,
    );
    if (x != null) setState(() => _imgPath = x.path);
  }

  // Sri Lanka NIC: old 9 digits + [VvXx] OR new 12 digits
  final _nicReg = RegExp(r'^(\d{9}[VvXx]|\d{12})$');

  double get _pwdStrength {
    final p = _password.text;
    if (p.isEmpty) return 0;
    int score = 0;
    if (p.length >= 8) score++;
    if (RegExp(r'[A-Z]').hasMatch(p)) score++;
    if (RegExp(r'[a-z]').hasMatch(p)) score++;
    if (RegExp(r'\d').hasMatch(p)) score++;
    if (RegExp(r'[!@#\$%^&*(),.?":{}|<>_\-]').hasMatch(p)) score++;
    return (score / 5).clamp(0, 1);
  }

  Color _pwdColor(double v) {
    if (v < 0.34) return const Color(0xFFEF5350); // red
    if (v < 0.67) return const Color(0xFFFFB300); // amber
    return const Color(0xFF43A047); // green
  }

  Future<void> _submit() async {
    FocusScope.of(context).unfocus();
    if (!_formKey.currentState!.validate()) return;
    if (!_agree) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please accept the Privacy Policy and Terms.')),
      );
      return;
    }
    setState(() => _loading = true);
    try {
      await AuthService.registerOwner(
        fullName: _name.text.trim(),
        email: _email.text.trim(),
        phone: _phone.text.trim(),
        address: _address.text.trim(),
        nic: _nic.text.trim(),
        password: _password.text,
        imagePath: _imgPath,
      );
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Registered. Please log in.')),
      );
      Navigator.pop(context);
    } catch (e) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Registration failed')),
      );
    } finally {
      setState(() => _loading = false);
    }
  }

  InputDecoration _decoration(String hint, {Widget? suffix, int? maxLines}) {
    return InputDecoration(
      hintText: hint,
      filled: true,
      fillColor: Colors.white,
      isDense: true,
      contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
      suffixIcon: suffix,
      border: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: Colors.grey.shade300),
      ),
      enabledBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: BorderSide(color: Colors.grey.shade300),
      ),
      focusedBorder: OutlineInputBorder(
        borderRadius: BorderRadius.circular(10),
        borderSide: const BorderSide(color: Color(0xFF1A73E8), width: 1.5),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const primaryBlue = Color(0xFF2563EB);

    return Scaffold(
      appBar: AppBar(
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, size: 18),
          onPressed: () => Navigator.pop(context),
        ),
        centerTitle: true,
        title: const Text('Registration'),
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black,
      ),
      backgroundColor: const Color(0xFFF7F8FA),
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 460),
            child: Container(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 20),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                boxShadow: const [
                  BoxShadow(
                    color: Color(0x14000000),
                    blurRadius: 18,
                    offset: Offset(0, 10),
                  ),
                ],
                border: Border.all(color: Colors.grey.shade200),
              ),
              child: Form(
                key: _formKey,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Avatar picker (dotted)
                    Center(
                      child: GestureDetector(
                        onTap: _pickImage,
                        child: _imgPath == null
                            ? DottedBorder(
                                borderType: BorderType.Circle,
                                dashPattern: const [6, 6],
                                color: Colors.grey.shade400,
                                strokeWidth: 1.6,
                                child: Container(
                                  width: 86,
                                  height: 86,
                                  alignment: Alignment.center,
                                  child: Column(
                                    mainAxisAlignment: MainAxisAlignment.center,
                                    children: [
                                      Icon(Icons.photo_camera_outlined,
                                          size: 26, color: Colors.grey.shade700),
                                      const SizedBox(height: 2),
                                      Text('+',
                                          style: TextStyle(
                                              fontSize: 16,
                                              color: Colors.grey.shade700)),
                                    ],
                                  ),
                                ),
                              )
                            : CircleAvatar(
                                radius: 43,
                                backgroundImage: FileImage(File(_imgPath!)),
                              ),
                      ),
                    ),
                    const SizedBox(height: 16),

                    const Text(
                      'Owner Details',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 12),

                    // Full name
                    const Text('Full Name',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _name,
                      decoration: _decoration('Enter your full name'),
                      validator: (v) =>
                          (v == null || v.trim().isEmpty) ? 'Required' : null,
                    ),
                    const SizedBox(height: 12),

                    // Email
                    const Text('Email',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _email,
                      keyboardType: TextInputType.emailAddress,
                      decoration: _decoration('Enter your email address'),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Required';
                        final ok = RegExp(
                                r"^[\w\.\-]+@([\w\-]+\.)+[\w\-]{2,}$")
                            .hasMatch(v);
                        return ok ? null : 'Please enter a valid email';
                      },
                    ),
                    const SizedBox(height: 12),

                    // NIC/ID
                    const Text('NIC/ID',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _nic,
                      decoration: _decoration('Enter your NIC/ID'),
                      validator: (v) {
                        if (v == null || v.isEmpty) return 'Required';
                        return _nicReg.hasMatch(v)
                            ? null
                            : 'Please enter a valid NIC/ID.';
                      },
                    ),
                    const SizedBox(height: 12),

                    // Contact Number
                    const Text('Contact Number',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _phone,
                      keyboardType: TextInputType.phone,
                      decoration: _decoration('Enter your contact number'),
                      validator: (v) =>
                          (v == null || v.trim().length < 7) ? 'Invalid number' : null,
                    ),
                    const SizedBox(height: 12),

                    // Address
                    const Text('Address',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _address,
                      maxLines: 3,
                      decoration: _decoration('Enter your address'),
                      validator: (v) =>
                          (v == null || v.trim().isEmpty) ? 'Required' : null,
                    ),

                    const SizedBox(height: 16),
                    Divider(color: Colors.grey.shade300, height: 32),

                    const Text(
                      'Security',
                      style: TextStyle(fontSize: 18, fontWeight: FontWeight.w800),
                    ),
                    const SizedBox(height: 12),

                    // Password
                    const Text('Password',
                        style: TextStyle(fontWeight: FontWeight.w600)),
                    const SizedBox(height: 6),
                    TextFormField(
                      controller: _password,
                      obscureText: _obscure,
                      onChanged: (_) => setState(() {}),
                      decoration: _decoration(
                        'Create a password',
                        suffix: IconButton(
                          splashRadius: 20,
                          onPressed: () => setState(() => _obscure = !_obscure),
                          icon: Icon(
                            _obscure
                                ? Icons.visibility_off_outlined
                                : Icons.visibility_outlined,
                            color: Colors.grey.shade600,
                          ),
                        ),
                      ),
                      validator: (v) =>
                          (v == null || v.length < 6) ? 'Min 6 characters' : null,
                    ),
                    const SizedBox(height: 10),

                    // Strength bar
                    ClipRRect(
                      borderRadius: BorderRadius.circular(4),
                      child: LinearProgressIndicator(
                        value: _pwdStrength == 0 ? 0.02 : _pwdStrength,
                        minHeight: 6,
                        backgroundColor: const Color(0xFFECEFF1),
                        valueColor:
                            AlwaysStoppedAnimation<Color>(_pwdColor(_pwdStrength)),
                      ),
                    ),

                    const SizedBox(height: 16),

                    // Terms
                    Row(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Checkbox(
                          value: _agree,
                          onChanged: (v) => setState(() => _agree = v ?? false),
                          materialTapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        const SizedBox(width: 6),
                        Expanded(
                          child: RichText(
                            text: TextSpan(
                              style: const TextStyle(
                                color: Colors.black87,
                                fontSize: 13.5,
                              ),
                              children: [
                                const TextSpan(text: 'I agree to the '),
                                TextSpan(
                                  text: 'Privacy Policy',
                                  style: const TextStyle(
                                      color: Color(0xFF2563EB),
                                      fontWeight: FontWeight.w700),
                                  recognizer: TapGestureRecognizer()
                                    ..onTap = () {
                                      Navigator.pushNamed(context, '/privacy');
                                    },
                                ),
                                const TextSpan(text: ' and '),
                                TextSpan(
                                  text: 'Terms of Service',
                                  style: const TextStyle(
                                      color: Color(0xFF2563EB),
                                      fontWeight: FontWeight.w700),
                                  recognizer: TapGestureRecognizer()
                                    ..onTap = () {
                                      Navigator.pushNamed(context, '/terms');
                                    },
                                ),
                                const TextSpan(text: '.'),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),

                    const SizedBox(height: 12),

                    // Register button
                    SizedBox(
                      width: double.infinity,
                      height: 52,
                      child: ElevatedButton(
                        onPressed: _loading ? null : _submit,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: primaryBlue,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(12),
                          ),
                        ),
                        child: _loading
                            ? const SizedBox(
                                height: 22,
                                width: 22,
                                child: CircularProgressIndicator(
                                  strokeWidth: 2,
                                  valueColor:
                                      AlwaysStoppedAnimation<Color>(Colors.white),
                                ),
                              )
                            : const Text(
                                'Register',
                                style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                ),
                              ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
