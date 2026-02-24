class TokenOut {
  final String accessToken;
  TokenOut({required this.accessToken});

  factory TokenOut.fromJson(Map<String, dynamic> j) =>
      TokenOut(accessToken: j['access_token'] as String);
}
