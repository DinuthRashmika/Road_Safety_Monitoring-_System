// lib/screens/vehicle_add_screen.dart
import 'dart:io';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:intl/intl.dart';
import '../services/vehicle_service.dart';

class VehicleAddScreen extends StatefulWidget {
  const VehicleAddScreen({super.key});
  @override
  State<VehicleAddScreen> createState() => _VehicleAddScreenState();
}

class _VehicleAddScreenState extends State<VehicleAddScreen> {
  final _type = TextEditingController(text: 'Car');
  final _model = TextEditingController();
  final _plate = TextEditingController();
  DateTime? _regDate;

  String? fFront, fBack, fRight, fLeft, fPlate;
  bool _saving = false;
  int _currentStep = 0;

  // --- Image picker instance & guard ---
  final ImagePicker _picker = ImagePicker();
  bool _picking = false;

  // Colors
  final Color _primaryColor = const Color(0xFF2563EB);
  final Color _primaryDark = const Color(0xFF1D4ED8);
  final Color _successColor = const Color(0xFF10B981);
  final Color _warningColor = const Color(0xFFF59E0B);
  final Color _errorColor = const Color(0xFFEF4444);
  final Color _surfaceColor = Colors.white;
  final Color _backgroundColor = const Color(0xFFF8FAFC);
  final Color _borderColor = const Color(0xFFE2E8F0);
  final Color _textPrimary = const Color(0xFF1E293B);
  final Color _textSecondary = const Color(0xFF64748B);
  final Color _textDisabled = const Color(0xFF94A3B8);

  // Text Styles
  TextStyle get _titleStyle => const TextStyle(
        fontSize: 20,
        fontWeight: FontWeight.w700,
        color: Colors.black87,
      );

  TextStyle get _sectionTitleStyle => const TextStyle(
        fontSize: 18,
        fontWeight: FontWeight.w600,
        color: Colors.black87,
      );

  TextStyle get _labelStyle => const TextStyle(
        fontSize: 16,
        fontWeight: FontWeight.w600,
        color: Colors.black87,
      );

  TextStyle get _hintStyle => TextStyle(
        fontSize: 14,
        color: _textSecondary,
      );

  Future<void> _pickDate() async {
    final now = DateTime.now();
    final picked = await showDatePicker(
      context: context,
      firstDate: DateTime(now.year - 50),
      lastDate: now,
      initialDate: now,
      builder: (context, child) {
        return Theme(
          data: Theme.of(context).copyWith(
            colorScheme: ColorScheme.light(
              primary: _primaryColor,
              onPrimary: Colors.white,
              surface: _surfaceColor,
              onSurface: _textPrimary,
            ),
            dialogBackgroundColor: Colors.white,
          ),
          child: child!,
        );
      },
    );
    if (picked != null && mounted) setState(() => _regDate = picked);
  }

  // which: 'front'|'back'|'right'|'left'|'plate'
  Future<void> _pick(String which) async {
    if (_picking) return; // guard against re-entrancy
    _picking = true;
    try {
      final XFile? x = await _picker.pickImage(
        source: ImageSource.gallery,
        imageQuality: 85,
      );

      // if user cancelled or no file, nothing to do
      if (!mounted || x == null) return;

      setState(() {
        switch (which) {
          case 'front':
            fFront = x.path;
            break;
          case 'back':
            fBack = x.path;
            break;
          case 'right':
            fRight = x.path;
            break;
          case 'left':
            fLeft = x.path;
            break;
          case 'plate':
            fPlate = x.path;
            break;
        }
      });
    } on PlatformException catch (err) {
      // Platform-specific error (including already_active)
      debugPrint('ImagePicker PlatformException: ${err.code} - ${err.message}');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Failed to pick image: ${err.message ?? err.code}'),
            backgroundColor: _errorColor,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
        );
      }
    } catch (e) {
      debugPrint('ImagePicker unknown error: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Failed to pick image'),
            backgroundColor: _errorColor,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
        );
      }
    } finally {
      _picking = false;
    }
  }

  Future<void> _submit() async {
    if (_regDate == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Select registration date'),
          backgroundColor: _warningColor,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      );
      return;
    }
    setState(() => _saving = true);
    try {
      await VehicleService.create(
        vehicleType: _type.text.trim(),
        vehicleModel: _model.text.trim(),
        registrationDate: DateFormat('yyyy-MM-dd').format(_regDate!),
        plateNo: _plate.text.trim(),
        imageFront: fFront,
        imageBack: fBack,
        imageRight: fRight,
        imageLeft: fLeft,
        imagePlate: fPlate,
      );
      if (!mounted) return;
      
      // Show success feedback
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Vehicle added successfully!'),
          backgroundColor: _successColor,
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
        ),
      );
      
      Navigator.pop(context);
    } catch (e) {
      debugPrint('Vehicle create failed: $e');
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: const Text('Failed to create vehicle'),
            backgroundColor: _errorColor,
            behavior: SnackBarBehavior.floating,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  Widget _buildImageUpload(String label, String? path, VoidCallback onPick, {bool required = false}) {
    final bool disabled = _picking;
    return Container(
      margin: const EdgeInsets.only(bottom: 20),
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(4),
                decoration: BoxDecoration(
                  color: _primaryColor.withOpacity(0.1),
                  borderRadius: BorderRadius.circular(6),
                ),
                child: Icon(
                  Icons.photo_camera_outlined,
                  size: 16,
                  color: _primaryColor,
                ),
              ),
              const SizedBox(width: 8),
              Text(
                label,
                style: _labelStyle,
              ),
              if (required) ...[
                const SizedBox(width: 4),
                Text(
                  '*',
                  style: TextStyle(
                    color: _errorColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 16),
          Container(
            height: 140,
            width: double.infinity,
            decoration: BoxDecoration(
              color: _backgroundColor,
              borderRadius: BorderRadius.circular(12),
              border: Border.all(color: _borderColor, width: 1.5),
            ),
            child: path != null
                ? Stack(
                    children: [
                      ClipRRect(
                        borderRadius: BorderRadius.circular(12),
                        child: Image.file(
                          File(path),
                          fit: BoxFit.cover,
                          width: double.infinity,
                          height: double.infinity,
                          errorBuilder: (c, e, s) {
                            return Container(
                              color: _backgroundColor,
                              child: Column(
                                mainAxisAlignment: MainAxisAlignment.center,
                                children: [
                                  Icon(Icons.error_outline, color: _textDisabled, size: 32),
                                  const SizedBox(height: 8),
                                  Text(
                                    'Cannot display image',
                                    style: TextStyle(color: _textDisabled),
                                  ),
                                ],
                              ),
                            );
                          },
                        ),
                      ),
                      Positioned(
                        top: 8,
                        right: 8,
                        child: Container(
                          padding: const EdgeInsets.all(4),
                          decoration: BoxDecoration(
                            color: Colors.black.withOpacity(0.6),
                            shape: BoxShape.circle,
                          ),
                          child: Icon(
                            Icons.check_circle,
                            color: _successColor,
                            size: 16,
                          ),
                        ),
                      ),
                    ],
                  )
                : Column(
                    mainAxisAlignment: MainAxisAlignment.center,
                    children: [
                      Container(
                        width: 48,
                        height: 48,
                        decoration: BoxDecoration(
                          color: _primaryColor.withOpacity(0.1),
                          shape: BoxShape.circle,
                        ),
                        child: Icon(
                          Icons.camera_alt_outlined,
                          size: 24,
                          color: _primaryColor,
                        ),
                      ),
                      const SizedBox(height: 12),
                      Text(
                        'Upload $label Photo',
                        style: _hintStyle.copyWith(fontWeight: FontWeight.w500),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        'Tap to select from gallery',
                        style: _hintStyle.copyWith(fontSize: 12),
                      ),
                    ],
                  ),
          ),
          const SizedBox(height: 16),
          SizedBox(
            width: double.infinity,
            child: FilledButton.icon(
              onPressed: disabled ? null : onPick,
              style: FilledButton.styleFrom(
                backgroundColor: path == null ? _primaryColor : Colors.transparent,
                foregroundColor: path == null ? Colors.white : _primaryColor,
                padding: const EdgeInsets.symmetric(vertical: 14, horizontal: 16),
                shape: RoundedRectangleBorder(
                  borderRadius: BorderRadius.circular(10),
                  side: path == null ? BorderSide.none : BorderSide(color: _primaryColor, width: 1.5),
                ),
                elevation: 0,
              ),
              icon: Icon(
                path == null ? Icons.cloud_upload_outlined : Icons.edit_outlined,
                size: 18,
              ),
              label: Text(
                path == null 
                  ? (disabled ? 'Selecting...' : 'Upload Photo')
                  : (disabled ? 'Selecting...' : 'Change Photo'),
                style: TextStyle(
                  fontWeight: FontWeight.w600,
                  fontSize: 14,
                ),
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildDetailsStep() {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        // Vehicle Type
        _buildSection(
          title: 'Vehicle Type',
          subtitle: 'Select the type of your vehicle.',
          required: true,
          child: DropdownButtonFormField<String>(
            value: _type.text,
            decoration: InputDecoration(
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: _borderColor),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: _primaryColor, width: 2),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            ),
            items: ['Car', 'Motorcycle', 'Truck', 'SUV', 'Van']
                .map((type) => DropdownMenuItem(
                      value: type,
                      child: Text(type, style: const TextStyle(fontSize: 16)),
                    ))
                .toList(),
            onChanged: (value) => setState(() => _type.text = value ?? 'Car'),
            style: const TextStyle(color: Colors.black87, fontSize: 16),
            dropdownColor: _surfaceColor,
            borderRadius: BorderRadius.circular(10),
            icon: Icon(Icons.arrow_drop_down, color: _primaryColor),
          ),
        ),
        const SizedBox(height: 20),

        // Vehicle Model
        _buildSection(
          title: 'Vehicle Model',
          subtitle: 'Make, model, and year.',
          required: true,
          child: TextField(
            controller: _model,
            decoration: InputDecoration(
              hintText: 'e.g., Toyota Aqua 2016',
              hintStyle: _hintStyle,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: _borderColor),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: _primaryColor, width: 2),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            ),
            style: const TextStyle(fontSize: 16),
          ),
        ),
        const SizedBox(height: 20),

        // Registration Date
        _buildSection(
          title: 'Registration Date',
          subtitle: 'Date of first registration.',
          required: true,
          child: GestureDetector(
            onTap: _pickDate,
            child: Container(
              width: double.infinity,
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
              decoration: BoxDecoration(
                border: Border.all(color: _borderColor),
                borderRadius: BorderRadius.circular(10),
              ),
              child: Row(
                children: [
                  Icon(Icons.calendar_today_outlined, color: _textSecondary, size: 20),
                  const SizedBox(width: 12),
                  Text(
                    _regDate == null ? 'Select Date' : DateFormat('MMMM dd, yyyy').format(_regDate!),
                    style: TextStyle(
                      color: _regDate == null ? _textDisabled : _textPrimary,
                      fontSize: 16,
                    ),
                  ),
                  const Spacer(),
                  if (_regDate != null)
                    IconButton(
                      onPressed: () => setState(() => _regDate = null),
                      icon: Icon(Icons.close, color: _textSecondary, size: 18),
                      padding: EdgeInsets.zero,
                      constraints: const BoxConstraints(),
                    ),
                ],
              ),
            ),
          ),
        ),
        const SizedBox(height: 20),

        // Number Plate
        _buildSection(
          title: 'Number Plate',
          subtitle: 'Please enter a valid number plate.',
          required: true,
          child: TextField(
            controller: _plate,
            decoration: InputDecoration(
              hintText: 'ABC-1234',
              hintStyle: _hintStyle,
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: _borderColor),
              ),
              focusedBorder: OutlineInputBorder(
                borderRadius: BorderRadius.circular(10),
                borderSide: BorderSide(color: _primaryColor, width: 2),
              ),
              contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
            ),
            style: const TextStyle(fontSize: 16, letterSpacing: 1.2),
          ),
        ),
      ],
    );
  }

  Widget _buildSection({
    required String title,
    required String subtitle,
    required Widget child,
    bool required = false,
  }) {
    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: _surfaceColor,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: _borderColor),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.05),
            blurRadius: 8,
            offset: const Offset(0, 2),
          ),
        ],
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Text(title, style: _labelStyle),
              if (required) ...[
                const SizedBox(width: 4),
                Text(
                  '*',
                  style: TextStyle(
                    color: _errorColor,
                    fontSize: 16,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 6),
          Text(subtitle, style: _hintStyle),
          const SizedBox(height: 16),
          child,
        ],
      ),
    );
  }

  Widget _buildPhotosStep() {
    return Column(
      children: [
        // Tips Box
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: const Color(0xFFF0F9FF),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFBAE6FD)),
            gradient: LinearGradient(
              begin: Alignment.topLeft,
              end: Alignment.bottomRight,
              colors: [
                const Color(0xFFF0F9FF),
                const Color(0xFFE0F2FE),
              ],
            ),
          ),
          child: Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: _primaryColor,
                  shape: BoxShape.circle,
                ),
                child: const Icon(Icons.lightbulb_outline, color: Colors.white, size: 18),
              ),
              const SizedBox(width: 12),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'Photo Guidelines',
                      style: TextStyle(
                        color: _primaryDark,
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                    const SizedBox(height: 4),
                    Text(
                      '• Use good lighting and avoid shadows\n• Ensure the number plate is fully visible and readable\n• Capture the entire vehicle in frame\n• Avoid blurry or dark photos',
                      style: TextStyle(
                        color: _primaryDark.withOpacity(0.8),
                        fontSize: 14,
                        height: 1.4,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Photo Upload Sections
        _buildImageUpload('Front View', fFront, () => _pick('front'), required: true),
        _buildImageUpload('Rear View', fBack, () => _pick('back'), required: true),
        _buildImageUpload('Right Side', fRight, () => _pick('right'), required: true),
        _buildImageUpload('Left Side', fLeft, () => _pick('left'), required: true),
        _buildImageUpload('Number Plate', fPlate, () => _pick('plate'), required: true),
      ],
    );
  }

  Widget _buildConfirmStep() {
    return Column(
      children: [
        // Summary Card
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: _surfaceColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: _borderColor),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: _successColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.check_circle_outline, color: _successColor, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Ready to Submit',
                    style: _sectionTitleStyle,
                  ),
                ],
              ),
              const SizedBox(height: 20),
              _buildDetailRow('Vehicle Type:', _type.text),
              _buildDetailRow('Vehicle Model:', _model.text.isEmpty ? 'Not specified' : _model.text),
              _buildDetailRow('Registration Date:', _regDate == null ? 'Not selected' : DateFormat('MMMM dd, yyyy').format(_regDate!)),
              _buildDetailRow('License Plate:', _plate.text.isEmpty ? 'Not specified' : _plate.text),
            ],
          ),
        ),
        const SizedBox(height: 24),

        // Photos Preview
        Container(
          width: double.infinity,
          padding: const EdgeInsets.all(20),
          decoration: BoxDecoration(
            color: _surfaceColor,
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: _borderColor),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.05),
                blurRadius: 8,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(6),
                    decoration: BoxDecoration(
                      color: _primaryColor.withOpacity(0.1),
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(Icons.photo_library_outlined, color: _primaryColor, size: 20),
                  ),
                  const SizedBox(width: 12),
                  Text(
                    'Uploaded Photos',
                    style: _sectionTitleStyle,
                  ),
                ],
              ),
              const SizedBox(height: 16),
              Wrap(
                spacing: 12,
                runSpacing: 12,
                children: [
                  if (fFront != null) _buildPhotoThumbnail(fFront!, 'Front'),
                  if (fBack != null) _buildPhotoThumbnail(fBack!, 'Rear'),
                  if (fRight != null) _buildPhotoThumbnail(fRight!, 'Right'),
                  if (fLeft != null) _buildPhotoThumbnail(fLeft!, 'Left'),
                  if (fPlate != null) _buildPhotoThumbnail(fPlate!, 'Plate'),
                ],
              ),
              if (fFront == null && fBack == null && fRight == null && fLeft == null && fPlate == null)
                Container(
                  padding: const EdgeInsets.all(20),
                  decoration: BoxDecoration(
                    color: _backgroundColor,
                    borderRadius: BorderRadius.circular(12),
                  ),
                  child: Column(
                    children: [
                      Icon(Icons.photo_outlined, color: _textDisabled, size: 48),
                      const SizedBox(height: 8),
                      Text(
                        'No photos uploaded',
                        style: TextStyle(color: _textDisabled, fontWeight: FontWeight.w500),
                      ),
                    ],
                  ),
                ),
            ],
          ),
        ),
      ],
    );
  }

  Widget _buildDetailRow(String label, String value) {
    return Container(
      padding: const EdgeInsets.symmetric(vertical: 12),
      decoration: BoxDecoration(
        border: Border(
          bottom: BorderSide(color: _borderColor.withOpacity(0.5)),
        ),
      ),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(
            width: 140,
            child: Text(
              label,
              style: TextStyle(
                fontWeight: FontWeight.w600,
                color: _textSecondary,
                fontSize: 14,
              ),
            ),
          ),
          Expanded(
            child: Text(
              value,
              style: TextStyle(
                color: _textPrimary,
                fontSize: 14,
                fontWeight: FontWeight.w500,
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildPhotoThumbnail(String path, String label) {
    return Column(
      children: [
        Container(
          width: 100,
          height: 75,
          decoration: BoxDecoration(
            borderRadius: BorderRadius.circular(12),
            border: Border.all(color: _borderColor),
            boxShadow: [
              BoxShadow(
                color: Colors.black.withOpacity(0.1),
                blurRadius: 4,
                offset: const Offset(0, 2),
              ),
            ],
          ),
          child: ClipRRect(
            borderRadius: BorderRadius.circular(12),
            child: Image.file(
              File(path),
              fit: BoxFit.cover,
              errorBuilder: (c, e, s) {
                return Container(
                  color: _backgroundColor,
                  child: Icon(Icons.error_outline, color: _textDisabled),
                );
              },
            ),
          ),
        ),
        const SizedBox(height: 6),
        Text(
          label,
          style: TextStyle(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: _textSecondary,
          ),
        ),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: _backgroundColor,
      resizeToAvoidBottomInset: true,
      appBar: AppBar(
        title: Text(
          'Add Vehicle',
          style: _titleStyle,
        ),
        backgroundColor: _surfaceColor,
        elevation: 0,
        foregroundColor: Colors.black87,
        centerTitle: false,
        shadowColor: Colors.black.withOpacity(0.1),
        surfaceTintColor: _surfaceColor,
      ),
      body: Column(
        children: [
          // Stepper Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 24),
            decoration: BoxDecoration(
              color: _surfaceColor,
              border: Border(
                bottom: BorderSide(color: _borderColor),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.05),
                  blurRadius: 4,
                  offset: const Offset(0, 2),
                ),
              ],
            ),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceAround,
              children: [
                _buildStep(1, 'Details', _currentStep == 0, _currentStep > 0),
                _buildStep(2, 'Photos', _currentStep == 1, _currentStep > 1),
                _buildStep(3, 'Confirm', _currentStep == 2, _currentStep > 2),
              ],
            ),
          ),

          // Content
          Expanded(
            child: ListView(
              physics: const ClampingScrollPhysics(),
              padding: const EdgeInsets.all(24),
              children: [
                // Step title
                Padding(
                  padding: const EdgeInsets.only(bottom: 20),
                  child: Text(
                    _currentStep == 0
                        ? 'Vehicle Information'
                        : _currentStep == 1
                            ? 'Vehicle Photos'
                            : 'Review & Submit',
                    style: _sectionTitleStyle.copyWith(fontSize: 20),
                  ),
                ),

                // Step content
                if (_currentStep == 0) _buildDetailsStep(),
                if (_currentStep == 1) _buildPhotosStep(),
                if (_currentStep == 2) _buildConfirmStep(),
                
                const SizedBox(height: 20),
              ],
            ),
          ),

          // Bottom Buttons
          Container(
            padding: const EdgeInsets.all(24),
            decoration: BoxDecoration(
              color: _surfaceColor,
              border: Border(
                top: BorderSide(color: _borderColor),
              ),
              boxShadow: [
                BoxShadow(
                  color: Colors.black.withOpacity(0.1),
                  blurRadius: 8,
                  offset: const Offset(0, -2),
                ),
              ],
            ),
            child: Row(
              children: [
                if (_currentStep > 0)
                  Expanded(
                    child: OutlinedButton(
                      onPressed: () => setState(() => _currentStep--),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 16),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                        side: BorderSide(color: _borderColor),
                      ),
                      child: Text(
                        'Back',
                        style: TextStyle(
                          color: _textPrimary,
                          fontWeight: FontWeight.w600,
                          fontSize: 16,
                        ),
                      ),
                    ),
                  ),
                if (_currentStep > 0) const SizedBox(width: 16),
                Expanded(
                  flex: _currentStep == 0 ? 2 : 1,
                  child: FilledButton(
                    onPressed: _saving
                        ? null
                        : () {
                            if (_currentStep < 2) {
                              setState(() => _currentStep++);
                            } else {
                              _submit();
                            }
                          },
                    style: FilledButton.styleFrom(
                      backgroundColor: _primaryColor,
                      foregroundColor: Colors.white,
                      padding: const EdgeInsets.symmetric(vertical: 16),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                      elevation: 0,
                    ),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.center,
                      children: [
                        if (_saving)
                          SizedBox(
                            width: 20,
                            height: 20,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              valueColor: AlwaysStoppedAnimation(Colors.white.withOpacity(0.8)),
                            ),
                          )
                        else if (_currentStep == 2)
                          const Icon(Icons.check_circle_outline, size: 20),
                        if (_saving || _currentStep == 2) const SizedBox(width: 8),
                        Text(
                          _saving
                              ? 'Submitting...'
                              : _currentStep == 2
                                  ? 'Submit Vehicle'
                                  : 'Continue',
                          style: const TextStyle(
                            fontWeight: FontWeight.w600,
                            fontSize: 16,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildStep(int number, String title, bool isActive, bool isCompleted) {
    return Expanded(
      child: Column(
        children: [
          Container(
            width: 36,
            height: 36,
            decoration: BoxDecoration(
              color: isCompleted
                  ? _successColor
                  : isActive
                      ? _primaryColor
                      : _backgroundColor,
              shape: BoxShape.circle,
              border: Border.all(
                color: isCompleted
                    ? _successColor
                    : isActive
                        ? _primaryColor
                        : _borderColor,
                width: 2,
              ),
            ),
            child: Center(
              child: isCompleted
                  ? Icon(Icons.check, color: Colors.white, size: 18)
                  : Text(
                      number.toString(),
                      style: TextStyle(
                        color: isActive ? Colors.white : _textDisabled,
                        fontWeight: FontWeight.w700,
                        fontSize: 14,
                      ),
                    ),
            ),
          ),
          const SizedBox(height: 8),
          Text(
            title,
            style: TextStyle(
              color: isActive || isCompleted ? _textPrimary : _textDisabled,
              fontWeight: (isActive || isCompleted) ? FontWeight.w600 : FontWeight.normal,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}