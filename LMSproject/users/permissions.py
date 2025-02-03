from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsModerator(BasePermission):
    """Custom permission to allow only moderators to access the API"""

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role.name == "moderator":
            return True
        raise PermissionDenied("You do not have permission to access this resource.")
