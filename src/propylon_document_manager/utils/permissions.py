from rest_framework import permissions


class FileVersionPermission(permissions.BasePermission):
    """
    Object-level permission for FileVersion:
    - Owner always has full access.
    - Users with read/write permissions in FilePermissions have access accordingly.
    """

    def has_object_permission(self, request, view, obj):
        user = request.user

        if obj.user == user:
            return True

        permission_qs = obj.file_permissions.filter(user=user)
        if not permission_qs.exists():
            return False

        if request.method in permissions.SAFE_METHODS:
            return permission_qs.filter(permissions__in=["read", "read_write"]).exists()
        else:
            return permission_qs.filter(permissions="read_write").exists()
