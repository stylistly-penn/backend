from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings
from drf_spectacular.extensions import OpenApiAuthenticationExtension
from drf_spectacular.utils import OpenApiTypes


class CookieJWTAuthentication(JWTAuthentication):
    def authenticate(self, request):
        # First, try getting the token from the Authorization header
        header_auth = super().authenticate(request)
        if header_auth is not None:
            return header_auth

        # If no Authorization header, check for access_token in cookies
        access_token = request.COOKIES.get(settings.SIMPLE_JWT["AUTH_COOKIE"])
        if access_token:
            validated_token = self.get_validated_token(access_token)
            return self.get_user(validated_token), validated_token

        return None


class CookieJWTAuthenticationScheme(OpenApiAuthenticationExtension):
    target_class = "api.authentication.CookieJWTAuthentication"  # Your auth class
    name = "JWT via Cookie"

    def get_security_definition(self, *args, **kwargs):  # Accepts extra arguments
        return {
            "type": "apiKey",
            "in": "cookie",
            "name": "access_token",  # Ensure this matches the cookie name
            "description": "JWT stored in an HTTP-only cookie",
        }
