from rest_framework import serializers
from django.contrib.auth import get_user_model, authenticate
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()


### ✅ Serializer for LoginView
class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data["email"], password=data["password"])
        if not user:
            raise serializers.ValidationError("Invalid email or password")

        refresh = RefreshToken.for_user(user)
        return {
            "user": {
                "id": user.id,
                "email": user.email,
                "first_name": user.first_name,
                "last_name": user.last_name,
            },
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


### ✅ Serializer for RegisterView
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("email", "first_name", "last_name", "password", "password2")

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create_user(**validated_data)
        return user


### ✅ Serializer for LogoutView
class LogoutSerializer(serializers.Serializer):
    refresh_token = serializers.CharField()

    def validate_refresh_token(self, token):
        try:
            RefreshToken(token).blacklist()
        except Exception:
            raise serializers.ValidationError("Invalid token")
        return token


### ✅ Serializer for ClassificationViewSet
class ClassificationSerializer(serializers.Serializer):
    input_text = serializers.CharField()
    result = serializers.CharField(read_only=True)

    def create(self, validated_data):
        # Example: simple text classification
        input_text = validated_data["input_text"]
        result = "Category A" if "keyword" in input_text else "Category B"
        return {"input_text": input_text, "result": result}
