from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

from api.authentication import CookieJWTAuthentication
from api.accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    LogoutSerializer,
    UserSerializer,
)

User = get_user_model()


class AuthCheckView(APIView):
    """
    Validates JWT from HttpOnly cookie and returns authentication status.
    Uses UserSerializer to return user data.
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "authenticated": True,
                "user": UserSerializer(request.user).data,
            },
            status=status.HTTP_200_OK,
        )


class RegisterView(APIView):
    """
    Handles user registration, assigns a default season, and returns JWT in an HTTP-only cookie.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = RegisterSerializer

    def post(self, request):
        email = request.data.get("email")
        username = request.data.get("username")
        password = request.data.get("password")
        first_name = request.data.get("first_name")
        last_name = request.data.get("last_name")

        if not email or not password:
            return Response(
                {"error": "Email and password are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not first_name or not last_name:
            return Response(
                {"error": "First and last name are required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "Email already taken"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if username:
            if User.objects.filter(username=username).exists():
                return Response(
                    {"error": "Username already taken"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        else:
            username = first_name[:1] + last_name + str(User.objects.count())

        user = User.objects.create(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            season=None,
        )
        user.set_password(password)
        user.save()

        response = Response(
            {"message": "Registration successful"}, status=status.HTTP_201_CREATED
        )
        return response


class LoginView(APIView):
    """
    Authenticates the user using the LoginSerializer.
    Returns user info (using UserSerializer), tokens, and colors.
    Sets the access token as an HttpOnly cookie.
    """

    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        response = Response(
            {
                "message": "Login successful",
                "user": data[
                    "user"
                ],  # Serialized via UserSerializer within LoginSerializer
                "access": data["access"],
                "refresh": data["refresh"],
            },
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="access_token",
            value=data["access"],
            httponly=True,
            secure=False,
            samesite="Lax",
        )
        return response


class LogoutView(APIView):
    """
    Handles user logout by clearing the JWT cookie.
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]
    serializer_class = LogoutSerializer

    def post(self, request):
        response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        return response
