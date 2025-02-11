from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from api.season.serializers import SeasonSerializer  # Import the season serializer

User = get_user_model()


### Serializer for LoginView
class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=False)
    password = serializers.CharField(write_only=True)
    email = serializers.EmailField(required=False)
    colors = serializers.ListField(
        child=serializers.DictField(), read_only=True
    )  # List of colors

    def validate(self, data):
        username = data.get("username")
        email = data.get("email")
        password = data.get("password")

        if (not username and not email) or not password:
            raise serializers.ValidationError(
                "Username/email and password are required"
            )

        if username:
            user = User.objects.filter(username=username).first()
        else:
            user = User.objects.filter(email=email).first()
        if user is None or not user.check_password(password):
            raise serializers.ValidationError("Invalid username or password")

        refresh = RefreshToken.for_user(user)

        return {
            "user": UserSerializer(user).data,  # Use the UserSerializer here
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }


### Serializer for RegisterView
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=8)
    password2 = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = (
            "email",
            "username",
            "first_name",
            "last_name",
            "password",
            "password2",
        )

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


### Serializer for LogoutView
class LogoutSerializer(serializers.Serializer):
    pass  # Logout doesn't need data, it just clears cookies


### New Serializer for User
class UserSerializer(serializers.ModelSerializer):
    season = SeasonSerializer(
        read_only=True
    )  # Use the SeasonSerializer for the season field

    class Meta:
        model = User
        fields = ("username", "email", "season")
