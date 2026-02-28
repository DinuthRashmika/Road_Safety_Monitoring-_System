import 'package:flutter/material.dart';
import '../models/notification_model.dart';
import '../services/notification_service.dart';

class AlertsScreen extends StatefulWidget {
  const AlertsScreen({super.key});

  @override
  State<AlertsScreen> createState() => _AlertsScreenState();
}

class _AlertsScreenState extends State<AlertsScreen> {
  bool _loading = true;

  List<NotificationModel> _protective = [];
  List<NotificationModel> _violations = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _loading = true);
    try {
      final protective = await NotificationService.getProtectiveAlerts();
      final violations = await NotificationService.getMyNotifications();

      setState(() {
        _protective = protective;
        _violations = violations;
      });
    } catch (e) {
      debugPrint("Alert load error: $e");
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      backgroundColor: Colors.black,
      appBar: AppBar(
        backgroundColor: Colors.black,
        foregroundColor: Colors.white,
        title: const Text('Alerts'),
      ),
      body: _loading
          ? const Center(
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation(Color(0xFF2563EB)),
              ),
            )
          : RefreshIndicator(
              onRefresh: _load,
              color: const Color(0xFF2563EB),
              child: ListView(
                padding: const EdgeInsets.all(16),
                children: [

                  /// ================= PROTECTIVE =================
                  _SectionTitle(
                    title: 'Protective Alerts',
                    subtitle: '${_protective.length} alerts',
                    icon: Icons.shield,
                  ),
                  const SizedBox(height: 10),

                  if (_protective.isEmpty)
                    const _EmptyCard(text: 'No protective alerts yet.')
                  else
                    ..._protective.map(
                      (n) => _NotifCard(
                        n: n,
                        isProtective: true,
                        onTap: () async {
                          await NotificationService.markProtectiveAsRead(n.id);
                          await _load();
                        },
                      ),
                    ),

                  const SizedBox(height: 24),

                  /// ================= VIOLATIONS =================
                  _SectionTitle(
                    title: 'Violation Alerts',
                    subtitle: '${_violations.length} alerts',
                    icon: Icons.report,
                  ),
                  const SizedBox(height: 10),

                  if (_violations.isEmpty)
                    const _EmptyCard(text: 'No violation alerts yet.')
                  else
                    ..._violations.map(
                      (n) => _NotifCard(
                        n: n,
                        isProtective: false,
                        onTap: () async {
                          await NotificationService.markAsRead(n.id);
                          await _load();
                        },
                      ),
                    ),
                ],
              ),
            ),
    );
  }
}








/// ================= UI COMPONENTS =================

class _SectionTitle extends StatelessWidget {
  final String title;
  final String subtitle;
  final IconData icon;

  const _SectionTitle({
    required this.title,
    required this.subtitle,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFF60A5FA)),
        const SizedBox(width: 10),
        Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(title,
                style: const TextStyle(
                    color: Colors.white,
                    fontSize: 18,
                    fontWeight: FontWeight.w700)),
            Text(subtitle,
                style: TextStyle(
                    color: Colors.grey.shade400, fontSize: 13)),
          ],
        ),
      ],
    );
  }
}

class _EmptyCard extends StatelessWidget {
  final String text;

  const _EmptyCard({required this.text});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(18),
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.grey.shade900,
        borderRadius: BorderRadius.circular(14),
      ),
      child: Text(
        text,
        style: TextStyle(color: Colors.grey.shade400),
      ),
    );
  }
}

class _NotifCard extends StatelessWidget {
  final NotificationModel n;
  final bool isProtective;
  final VoidCallback onTap;

  const _NotifCard({
    required this.n,
    required this.isProtective,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      decoration: BoxDecoration(
        color: Colors.grey.shade900,
        borderRadius: BorderRadius.circular(14),
      ),
      child: ListTile(
        onTap: onTap,
        leading: Icon(
          isProtective
              ? Icons.shield
              : Icons.warning_amber_rounded,
          color: isProtective
              ? const Color(0xFF60A5FA)
              : const Color(0xFFF87171),
        ),
        title: Text(
          n.vehiclePlate.isNotEmpty
              ? n.vehiclePlate
              : "Notification",
          style: TextStyle(
            color: Colors.white,
            fontWeight:
                n.isRead ? FontWeight.w500 : FontWeight.w700,
          ),
        ),
        subtitle: Text(
          "${n.message}\n${n.location}",
          style: TextStyle(
            color: Colors.grey.shade400,
            height: 1.3,
          ),
        ),
        isThreeLine: true,
        trailing: n.isRead
            ? const Icon(Icons.done, color: Colors.green)
            : const Icon(Icons.circle,
                size: 10, color: Color(0xFF2563EB)),
      ),
    );
  }
}