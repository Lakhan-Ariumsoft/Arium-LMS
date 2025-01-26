# from django.contrib.auth.models import Group

# def is_moderator(user):
#     """Check if the user is a moderator."""
#     if not user.is_authenticated:
#         return False
#     return user.groups.filter(name='moderator').exists()

# def is_instructor(user):
#     """Check if the user is an instructor."""
#     if not user.is_authenticated:
#         return False
#     return user.groups.filter(name='instructor').exists()

# def is_moderator_or_instructor(user):
#     """Check if the user is either a moderator or an instructor."""
#     if not user.is_authenticated:
#         return False
#     return user.groups.filter(name__in=['moderator', 'instructor']).exists()

# 
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied

def role_required(roles):
    def decorator(view_func):
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                return JsonResponse({'error': 'Authentication required'}, status=401)
            if request.user.role not in roles:
                raise PermissionDenied("You do not have permission to perform this action.")
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


# from functools import wraps
# from django.http import JsonResponse

# def role_required(roles=[]):
#     def decorator(func):
#         @wraps(func)
#         def wrapper(request, *args, **kwargs):
#             if not request.user.is_authenticated:
#                 return JsonResponse({'error': 'Authentication required'}, status=401)
#             if request.user.role not in roles:
#                 return JsonResponse({'error': 'Permission denied'}, status=403)
#             return func(request, *args, **kwargs)
#         return wrapper
#     return decorator



