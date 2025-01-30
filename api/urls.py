from rest_framework.permissions import AllowAny
from rest_framework.routers import DefaultRouter
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView,
)
from .items.views import ItemViewSet
from .brands.views import BrandViewSet
from .color.views import ColorViewSet
from .season.views import SeasonViewSet
from .accounts.views import (
    LoginView,
    LogoutView,
    RegisterView,
    ClassificationViewSet,
    AuthCheckView,  # ✅ Import AuthCheckView
)

# ✅ Register ViewSets for Routers
router = DefaultRouter()
router.register(r"items", ItemViewSet)
router.register(r"brands", BrandViewSet)
router.register(r"colors", ColorViewSet)
router.register(r"seasons", SeasonViewSet)
router.register(r"classification", ClassificationViewSet)

urlpatterns = [
    # ✅ Django Admin
    path("admin/", admin.site.urls),
    # ✅ API Routes (ViewSets)
    path("", include(router.urls)),
    # ✅ Authentication Routes
    path("auth/login/", LoginView.as_view(), name="login"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/register/", RegisterView.as_view(), name="register"),
    path(
        "auth/check/", AuthCheckView.as_view(), name="auth-check"
    ),  # ✅ Add auth-check
    # ✅ OpenAPI Schema (Make it Public)
    path(
        "api/schema/",
        SpectacularAPIView.as_view(permission_classes=[AllowAny]),
        name="schema",
    ),
    # ✅ Swagger-UI (Make it Public)
    path(
        "api/schema/swagger-ui/",
        SpectacularSwaggerView.as_view(
            url_name="schema", permission_classes=[AllowAny]
        ),
        name="swagger-ui",
    ),
    # ✅ Redoc (Make it Public)
    path(
        "api/schema/redoc/",
        SpectacularRedocView.as_view(url_name="schema", permission_classes=[AllowAny]),
        name="redoc",
    ),
]
