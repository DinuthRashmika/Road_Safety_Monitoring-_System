import 'package:flutter/material.dart';

class AppButton extends StatelessWidget {
  const AppButton({super.key, required this.text, required this.onPressed, this.enabled = true});
  final String text;
  final VoidCallback onPressed;
  final bool enabled;

  @override
  Widget build(BuildContext context) {
    return SizedBox(
      width: double.infinity,
      height: 48,
      child: FilledButton(
        onPressed: enabled ? onPressed : null,
        child: Text(text),
      ),
    );
  }
}
