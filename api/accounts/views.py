from django.contrib.auth import get_user_model, authenticate
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.viewsets import ViewSet
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response

from api.authentication import CookieJWTAuthentication
from api.accounts.serializers import (
    LoginSerializer,
    RegisterSerializer,
    LogoutSerializer,
    ClassificationSerializer,
)

User = get_user_model()


class AuthCheckView(APIView):
    """
    Validates JWT from HttpOnly cookie and returns authentication status.
    """

    authentication_classes = [CookieJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(
            {
                "authenticated": True,
                "username": request.user.username,
                "email": request.user.email,
            },
            status=status.HTTP_200_OK,
        )


class ClassificationViewSet(ViewSet):
    """
    Viewset for classifying a user’s season based on an uploaded image.
    Requires authentication via cookie-based JWT.
    """

    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]  # Allows image file uploads
    serializer_class = ClassificationSerializer

    queryset = User.objects.none()

    @action(detail=False, methods=["post"], url_path="classify")
    def classify(self, request):
        """
        Handles image upload for classification.
        """
        user = request.user  # Get the authenticated user

        # Check if an image was provided
        if "image" not in request.FILES:
            return Response(
                {"error": "No image provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        image = request.FILES["image"]

        # Placeholder for future classification logic
        # TODO: Process `image` to determine user's season

        return Response(
            {"message": "Image received successfully. Classification pending."},
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
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    def post(self, request):
        username = request.data.get("username")
        email = request.data.get("email")
        password = request.data.get("password")

        print(
            f"DEBUG: Received username={username}, email={email}, password={password}"
        )

        if not email:
            user = authenticate(username=username, password=password)
        else:
            user = authenticate(email=email, password=password)

        if user is None:
            print("DEBUG: Authentication failed, user not found")
            return Response(
                {"detail": "User not found", "code": "user_not_found"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        print(f"DEBUG: Authenticated user: {user}")

        refresh = RefreshToken.for_user(user)
        season = user.season
        colors = (
            list(
                season.season_colors.values_list(
                    "color__id", "color__name", "color__code"
                )
            )
            if season
            else []
        )

        response = Response(
            {"message": "Login successful", "colors": colors},
            status=status.HTTP_200_OK,
        )
        response.set_cookie(
            key="access_token",
            value=str(refresh.access_token),
            httponly=True,
            secure=False,
            samesite="Lax",
        )
        return response


class LogoutView(APIView):
    """
    Handles user logout by clearing the JWT cookie.
    """

    serializer_class = LogoutSerializer

    def post(self, request):
        response = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        response.delete_cookie("access_token")
        return response
