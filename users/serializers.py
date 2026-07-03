from rest_framework import serializers

from users.models import Role, User


class RegisterSerializer(serializers.Serializer):
    last_name = serializers.CharField(max_length=150)
    first_name = serializers.CharField(max_length=150)
    patronymic = serializers.CharField(max_length=150, required=False, allow_blank=True)
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    def validate_email(self, value):
        value = value.strip().lower()
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password2"]:
            raise serializers.ValidationError({"password2": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password2")
        password = validated_data.pop("password")
        default_role, _ = Role.objects.get_or_create(
            name="user", defaults={"description": "Обычный пользователь"}
        )
        return User.objects.create_user(password=password, role=default_role, **validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)


class UserSerializer(serializers.ModelSerializer):
    role = serializers.CharField(source="role.name", read_only=True)

    class Meta:
        model = User
        fields = [
            "id", "last_name", "first_name", "patronymic",
            "email", "role", "is_active", "created_at",
        ]
        read_only_fields = ["id", "email", "role", "is_active", "created_at"]


class UserUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["last_name", "first_name", "patronymic"]
