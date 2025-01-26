from rest_framework.permissions import BasePermission

class IsModerator(BasePermission):
    """
    Custom permission to check if the user is a moderator.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'Moderator'
