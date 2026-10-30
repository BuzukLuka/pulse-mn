from rest_framework.permissions import BasePermission


def roles(*allowed):
    """Үүргээр хамгаалах permission (NFR-004)."""
    class _Permission(BasePermission):
        message = "Танд энэ үйлдлийг хийх эрх алга."

        def has_permission(self, request, view):
            u = request.user
            return bool(u and u.is_authenticated and u.is_active and u.role in allowed)

    _Permission.__name__ = "Roles_" + "_".join(allowed)
    return _Permission
