from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from api.season.models import Season

User = get_user_model()


### ✅ Serializer for LoginView
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    colors = serializers.ListField(
        child=serializers.DictField(), read_only=True
    )  # List of colors

    def validate(self, data):
        username = data.get("username")
        password = data.get("password")

        if not username or not password:
            raise serializers.ValidationError("Username and password are required")

        user = User.objects.filter(username=username).first()
        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid username or password")

        refresh = RefreshToken.for_user(user)

        # Get the user's season colors
        season = user.season
        colors = (
            list(season.season_colors.values("color__id", "color__name", "color__code"))
            if season
            else []
        )

        return {
            "user": {"id": user.id, "username": user.username},
            "access": str(refresh.access_token),
            "refresh": str(refresh),
            "colors": colors,
        }


### ✅ Serializer for RegisterView
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ("username", "password", "password2")

    def validate(self, data):
        if data["password"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        validated_data.pop("password2")
        user = User.objects.create(username=validated_data["username"], season=None)
        user.set_password(validated_data["password"])
        user.save()
        return user


### ✅ Serializer for LogoutView
class LogoutSerializer(serializers.Serializer):
    pass  # Logout doesn't need data, it just clears cookies


### ✅ Serializer for ClassificationViewSet
class ClassificationSerializer(serializers.Serializer):
    image = serializers.ImageField()

    def create(self, validated_data):
        # TODO: Implement actual classification logic
        return {"message": "Image received successfully. Classification pending."}
