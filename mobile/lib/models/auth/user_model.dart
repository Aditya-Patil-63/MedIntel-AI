import 'package:equatable/equatable.dart';

/// Application User Profile representation.
class UserModel extends Equatable {
  final int id;
  final String name;
  final String email;
  final String token;
  final String languagePreference;

  const UserModel({
    required this.id,
    required this.name,
    required this.email,
    required this.token,
    this.languagePreference = 'english',
  });

  factory UserModel.fromJson(Map<String, dynamic> json, {String? token}) {
    // Check if json contains a nested 'user' key
    final userMap = json.containsKey('user') && json['user'] is Map<String, dynamic>
        ? json['user'] as Map<String, dynamic>
        : json;

    final resolvedToken = token ??
        (json['access_token'] as String?) ??
        (userMap['token'] as String?) ??
        '';

    return UserModel(
      id: (userMap['id'] as num?)?.toInt() ?? 0,
      name: (userMap['name'] as String?) ?? '',
      email: (userMap['email'] as String?) ?? '',
      token: resolvedToken,
      languagePreference: (userMap['language_preference'] as String?) ?? 'english',
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'name': name,
        'email': email,
        'token': token,
        'language_preference': languagePreference,
      };

  @override
  List<Object?> get props => [id, name, email, token, languagePreference];
}
