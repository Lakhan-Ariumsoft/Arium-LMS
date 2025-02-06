from rest_framework.permissions import BasePermission
from rest_framework.exceptions import PermissionDenied

class IsModerator(BasePermission):
    """Custom permission to allow only moderators to access the API"""

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role.name in ["moderator" , "Moderator"]:
            return True
        raise PermissionDenied("You do not have permission to access this resource.")


class IsModeratorOrInstructor(BasePermission):
    """Custom permission to allow moderators and instructors to access the API"""

    def has_permission(self, request, view):
        if request.user.is_authenticated and request.user.role.name in ["moderator", "instructor","Instructor","Moderator"]:
            return True
        raise PermissionDenied("You do not have permission to access this resource.")
