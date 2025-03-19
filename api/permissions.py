from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsAdminOrReadOnly(BasePermission):
    """
    Custom permission to allow read-only access for any request,
    but only allow write actions (POST, PUT, PATCH, DELETE) for admin users.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_staff)


class IsAuthenticatedReadOrAdminWrite(BasePermission):
    """
    Custom permission:
    - For safe methods (GET, HEAD, OPTIONS), the user must be authenticated.
    - For write methods (POST, PUT, PATCH, DELETE), the user must be an admin.
    """

    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            # For read operations, user must be authenticated.
            return bool(request.user and request.user.is_authenticated)
        # For write operations, user must be an admin.
        return bool(request.user and request.user.is_staff)


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission:
    - For all methods, the user must be authenticated.
    - For all methods, the user must be the owner of the object.
    """

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return obj.owner == request.user
