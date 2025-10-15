import 'package:flutter/material.dart';
import '../models/owner.dart';
import '../services/owner_service.dart';

class ProfileScreen extends StatefulWidget {
  const ProfileScreen({super.key});
  @override
  State<ProfileScreen> createState() => _ProfileScreenState();
}

class _ProfileScreenState extends State<ProfileScreen> {
  Owner? _me;

  // editing
  bool _editing = false;
  bool _saving = false;

  // controllers for editable fields
  final _name = TextEditingController();
  final _phone = TextEditingController();
  final _address = TextEditingController();

  // local UI state
  bool _notifyApp = true;
  bool _notifyViolations = true;
  bool _notifyTrips = false;

  Future<void> _load() async {
    final me = await OwnerService.me();
    setState(() {
      _me = me;
      _name.text = me.fullName;
      _phone.text = me.phone;
      _address.text = me.address;
    });
  }

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _save() async {
    setState(() => _saving = true);
    try {
      final updated = await OwnerService.update(
        fullName: _name.text.trim(),
        phone: _phone.text.trim(),
        address: _address.text.trim(),
      );
      setState(() {
        _me = updated;
        _editing = false;
      });
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Profile updated')),
      );
    } finally {
      setState(() => _saving = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_me == null) {
      return const Scaffold(body: Center(child: CircularProgressIndicator()));
    }

    final me = _me!;
    final email = me.email ?? '';
    final nic = me.nic ?? '';
    

    return Scaffold(
      backgroundColor: const Color(0xFFF7F8FA),
      appBar: AppBar(
        title: const Text('Profile'),
        centerTitle: true,
        elevation: 0,
        backgroundColor: Colors.white,
        foregroundColor: Colors.black87,
        actions: [
          if (_editing)
            IconButton(
              icon: _saving
                  ? const SizedBox(
                      width: 20, height: 20, child: CircularProgressIndicator(strokeWidth: 2))
                  : const Icon(Icons.check_rounded),
              onPressed: _saving ? null : _save,
              tooltip: 'Save',
            )
          else
            IconButton(
              icon: const Icon(Icons.edit_rounded),
              onPressed: () => setState(() => _editing = true),
              tooltip: 'Edit',
            ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 24),
        child: Column(
          children: [
            // Header Card
            _Card(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 20),
              child: Column(
                children: [
                  Container(
                    width: 88,
                    height: 88,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: const Color(0xFFF2F4F7),
                      image: (me.imageUrl != null && me.imageUrl!.isNotEmpty)
                          ? DecorationImage(
                              image: NetworkImage(me.imageUrl!),
                              fit: BoxFit.cover,
                            )
                          : null,
                    ),
                    child: (me.imageUrl == null || me.imageUrl!.isEmpty)
                        ? const Icon(Icons.person, size: 44, color: Colors.black38)
                        : null,
                  ),
                  const SizedBox(height: 12),
                  Text(
                    _editing ? _name.text : me.fullName,
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w800,
                      color: Colors.black87,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 6),
                  Text(
                    me.phone.isNotEmpty ? me.phone : '—',
                    style: const TextStyle(color: Colors.black54),
                  ),
                  Text(
                    email.isNotEmpty ? email : '—',
                    style: const TextStyle(color: Colors.black54),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Profile Info
            _Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _SectionTitle('Profile Info'),
                  const Divider(height: 20),
                  _infoRow(
                    label: 'Full Name',
                    value: me.fullName,
                    editor: _editing
                        ? _editField(_name, hint: 'Your name')
                        : null,
                  ),
                  _infoRow(
                    label: 'Phone',
                    value: me.phone,
                    editor: _editing
                        ? _editField(_phone, hint: 'Phone number', keyboardType: TextInputType.phone)
                        : null,
                  ),
                  _infoRow(label: 'Email', value: email),
                  _infoRow(label: 'NIC/ID', value: nic),
                  _infoRow(
                    label: 'Address',
                    value: me.address,
                    editor: _editing ? _editField(_address, hint: 'Address') : null,
                    multiline: true,
                  ),
                  
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Security Card
            _Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _SectionTitle('Security'),
                  const Divider(height: 20),
                  _rowTile(
                    leading: 'Password',
                    trailing: '•••••••',
                    onTap: () => Navigator.pushNamed(context, '/change-password'),
                    trailingIcon: Icons.chevron_right_rounded,
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Notifications
            _Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _SectionTitle('Notifications'),
                  const Divider(height: 20),
                  _switchTile(
                    'App Alerts',
                    _notifyApp,
                    (v) => setState(() => _notifyApp = v),
                  ),
                  _switchTile(
                    'Violations',
                    _notifyViolations,
                    (v) => setState(() => _notifyViolations = v),
                  ),
                  _switchTile(
                    'Trip Summaries',
                    _notifyTrips,
                    (v) => setState(() => _notifyTrips = v),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 12),

            // Documents
            _Card(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _SectionTitle('Documents'),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      _chipButton('License', onTap: () => Navigator.pushNamed(context, '/doc-license')),
                      _chipButton('Insurance', onTap: () => Navigator.pushNamed(context, '/doc-insurance')),
                    ],
                  ),
                ],
              ),
            ),
            const SizedBox(height: 48),
          ],
        ),
      ),
    );
  }

  // ---------- small builders ----------

  Widget _editField(
    TextEditingController c, {
    String? hint,
    TextInputType? keyboardType,
  }) {
    return TextField(
      controller: c,
      keyboardType: keyboardType,
      decoration: InputDecoration(
        hintText: hint,
        isDense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: Color(0xFFE6E9EF)),
        ),
      ),
    );
  }

  Widget _infoRow({
    required String label,
    required String value,
    Widget? editor,
    bool multiline = false,
  }) {
    final labelStyle = TextStyle(color: Colors.black54, fontSize: 13, fontWeight: FontWeight.w600);
    final valueStyle = TextStyle(color: Colors.black87, fontSize: 14, fontWeight: FontWeight.w600);

    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 10),
      child: Row(
        crossAxisAlignment: multiline ? CrossAxisAlignment.start : CrossAxisAlignment.center,
        children: [
          SizedBox(
            width: 130,
            child: Text(label, style: labelStyle),
          ),
          const SizedBox(width: 8),
          Expanded(
            child: editor ??
                Text(
                  value.isEmpty ? '—' : value,
                  style: valueStyle,
                  textAlign: TextAlign.right,
                ),
          ),
        ],
      ),
    );
  }

  Widget _rowTile({
    required String leading,
    String? trailing,
    IconData? trailingIcon,
    VoidCallback? onTap,
  }) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(12),
      child: Padding(
        padding: const EdgeInsets.symmetric(vertical: 10),
        child: Row(
          children: [
            Expanded(
              child: Text(
                leading,
                style: const TextStyle(
                  color: Colors.black87,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ),
            if (trailing != null)
              Text(
                trailing,
                style: const TextStyle(color: Colors.black54, fontWeight: FontWeight.w600),
              ),
            if (trailingIcon != null) ...[
              const SizedBox(width: 8),
              Icon(trailingIcon, color: Colors.black26),
            ],
          ],
        ),
      ),
    );
  }

  Widget _switchTile(String title, bool value, ValueChanged<bool> onChanged) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        children: [
          Expanded(
            child: Text(
              title,
              style: const TextStyle(color: Colors.black87, fontWeight: FontWeight.w600),
            ),
          ),
          Switch(
            value: value,
            onChanged: onChanged,
            activeColor: Colors.white,
            activeTrackColor: const Color(0xFF2563EB),
          ),
        ],
      ),
    );
  }

  Widget _chipButton(String text, {VoidCallback? onTap}) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(999),
      child: Container(
        padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 8),
        decoration: BoxDecoration(
          color: const Color(0xFFEAF2FF),
          borderRadius: BorderRadius.circular(999),
        ),
        child: Text(
          text,
          style: const TextStyle(
            color: Color(0xFF2563EB),
            fontWeight: FontWeight.w700,
          ),
        ),
      ),
    );
  }
}

/* ======= small reusable bits ======= */

class _Card extends StatelessWidget {
  const _Card({required this.child, this.padding});
  final Widget child;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: double.infinity,
      padding: padding ?? const EdgeInsets.all(16),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE6E9EF)),
        boxShadow: [
          BoxShadow(
            color: Colors.black.withOpacity(0.04),
            blurRadius: 12,
            offset: const Offset(0, 4),
          ),
        ],
      ),
      child: child,
    );
  }
}

class _SectionTitle extends StatelessWidget {
  const _SectionTitle(this.text);
  final String text;

  @override
  Widget build(BuildContext context) {
    return Text(
      text,
      style: const TextStyle(
        fontWeight: FontWeight.w800,
        fontSize: 16,
        color: Colors.black87,
      ),
    );
  }
}
