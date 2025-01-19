
from django.contrib.auth import authenticate, login
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import CustomUser
from django.contrib.auth import logout
from django.views.decorators.csrf import csrf_exempt
from django.middleware.csrf import CsrfViewMiddleware



class CSRFView(APIView):

    def get(self, request):
        # Get CSRF token from cookies
        csrf_token = request.COOKIES.get('csrftoken')
        
        if csrf_token:
            return Response({"csrf_token": csrf_token})
        else:
            return Response({"detail": "CSRF token not found in cookies."}, status=400)

class LoginAPIView(APIView):
    """
    API View to handle user login based on phone number and password, with role check.
    """
    

    @csrf_exempt
    def post(self, request, *args, **kwargs):
        phone_number = request.data.get('phone_number')
        password = request.data.get('password')

        if not phone_number or not password:
            return Response({"detail": "Phone number and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Check if phone_number exists
        try:
            user = CustomUser.objects.get(phone=phone_number)
        except CustomUser.DoesNotExist:
            return Response({"detail": "Invalid phone number."}, status=status.HTTP_401_UNAUTHORIZED)

        # Authenticate the user using the phone number and password
        if user.check_password(password):
            # Check the role of the user
            role = user.role  # Assuming you have 'role' field in your model

            # Validate user role
            if role not in ['moderator', 'instructor', 'student']:
                return Response({"detail": "Unauthorized role."}, status=status.HTTP_403_FORBIDDEN)

            # Log the user in
            login(request, user)

            # Manually ensure the session is saved and session ID is added to the `django_session` table
            request.session.save()

            # Create the response data
            response_data = {
                'email': user.email,
                'role': role,
                'name': user.get_full_name(),  # Using `get_full_name()` method of AbstractUser
                'session_id': request.session.session_key  # Include the session ID
            }

            return Response({
                "message": "User logged in successfully.",
                "user": response_data,
            }, status=status.HTTP_200_OK)
        else:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    @csrf_exempt
    def post(self, request):
        # Retrieve CSRF token from the request headers
        csrf_token = request.headers.get('X-CSRFToken')

        if not csrf_token:
            return Response({"detail": "CSRF token is missing."}, status=400)

        # Validate CSRF token
        csrf_check = CsrfViewMiddleware().process_request(request)
        if csrf_check:
            return Response({"detail": "CSRF token validation failed."}, status=403)

        # Logout the user
        logout(request)
        
        return Response({"message": "User logged out successfully."}, status=200)


# from django.http import JsonResponse
# from django.views import View
# from django.utils.decorators import method_decorator
# from django.contrib.auth.decorators import login_required
# from .models import Profile, Role
# import json


# @method_decorator(login_required, name='dispatch')
# class StudentView(View):
#     def has_permission(self, Profile, action):
#         """
#         Check permissions based on the Profile's role.
#         - Moderator: Full permissions.
#         - Instructor: Add your logic if needed.
#         - Student: Read-only permissions.
#         """
#         role_title = Profile.role.role_title  # Access role title
#         if role_title == "moderator":
#             return True  # Full access
#         if role_title == "instructor" and action in ["read", "update"]:
#             return True  # Add custom instructor logic if needed
#         if role_title == "student" and action == "read":
#             return True  # Read-only for students
#         return False

#     def get(self, request, student_id=None):
#         """
#         GET: Retrieve student(s).
#         - Students: Can only read.
#         - Moderators/Instructors: Can access all data.
#         """
#         if not self.has_permission(request.Profile, "read"):
#             return JsonResponse({"error": "Access Denied"}, status=403)

#         if student_id:
#             try:
#                 student = Profile.objects.get(id=student_id, role__role_title="student")
#                 data = {
#                     "id": student.id,
#                     "firstname": student.firstname,
#                     "lastname": student.lastname,
#                     "email": student.email,
#                     "phone": student.phone,
#                     "dob": student.dob,
#                     "address": student.address,
#                     "is_active": student.is_active,
#                 }
#                 return JsonResponse(data, safe=False)
#             except Profile.DoesNotExist:
#                 return JsonResponse({"error": "Student not found"}, status=404)
#         else:
#             students = Profile.objects.filter(role__role_title="student")
#             data = [
#                 {
#                     "id": student.id,
#                     "firstname": student.firstname,
#                     "lastname": student.lastname,
#                     "email": student.email,
#                     "phone": student.phone,
#                     "dob": student.dob,
#                     "address": student.address,
#                     "is_active": student.is_active,
#                 }
#                 for student in students
#             ]
#             return JsonResponse(data, safe=False)

#     def post(self, request):
#         """
#         POST: Create a new student.
#         - Only Moderators can create students.
#         """
#         if not self.has_permission(request.Profile, "create"):
#             return JsonResponse({"error": "Access Denied"}, status=403)

#         try:
#             data = json.loads(request.body)
#             role = Role.objects.get(role_title="student")  # Assign 'student' role
#             student = Profile.objects.create(
#                 firstname=data["firstname"],
#                 lastname=data["lastname"],
#                 email=data["email"],
#                 phone=data["phone"],
#                 dob=data.get("dob"),
#                 address=data.get("address"),
#                 role=role,
#             )
#             return JsonResponse(
#                 {"message": "Student created successfully", "id": student.id}, status=201
#             )
#         except KeyError as e:
#             return JsonResponse({"error": f"Missing field: {e}"}, status=400)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)

#     def put(self, request, student_id):
#         """
#         PUT: Update student details.
#         - Only Moderators can update students.
#         """
#         if not self.has_permission(request.Profile, "update"):
#             return JsonResponse({"error": "Access Denied"}, status=403)

#         try:
#             data = json.loads(request.body)
#             student = Profile.objects.get(id=student_id, role__role_title="student")

#             student.firstname = data.get("firstname", student.firstname)
#             student.lastname = data.get("lastname", student.lastname)
#             student.phone = data.get("phone", student.phone)
#             student.dob = data.get("dob", student.dob)
#             student.address = data.get("address", student.address)
#             student.is_active = data.get("is_active", student.is_active)
#             student.save()

#             return JsonResponse({"message": "Student updated successfully"})
#         except Profile.DoesNotExist:
#             return JsonResponse({"error": "Student not found"}, status=404)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)

#     def delete(self, request, student_id):
#         """
#         DELETE: Delete a student.
#         - Only Moderators can delete students.
#         """
#         if not self.has_permission(request.Profile, "delete"):
#             return JsonResponse({"error": "Access Denied"}, status=403)

#         try:
#             student = Profile.objects.get(id=student_id, role__role_title="student")
#             student.delete()
#             return JsonResponse({"message": "Student deleted successfully"})
#         except Profile.DoesNotExist:
#             return JsonResponse({"error": "Student not found"}, status=404)
#         except Exception as e:
#             return JsonResponse({"error": str(e)}, status=400)
        
