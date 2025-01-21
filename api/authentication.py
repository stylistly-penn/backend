from rest_framework_simplejwt.authentication import JWTAuthentication
from django.conf import settings


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
