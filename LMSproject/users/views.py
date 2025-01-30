from django.contrib.auth import login
from .models import User
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.permissions import IsAuthenticated
from rest_framework.permissions import AllowAny
from django.middleware.csrf import get_token
import os

from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
import re
from rest_framework.exceptions import ValidationError

class LoginAPIView(APIView):
    """
    API View for user login using phone and password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        countryCode = request.data.get("countryCode")
        # print("phone::::::::",phone)

        # password = request.data.get("password")
        # password = os.getenv("DEFAULT_USER_PASSWORD")
        password = "Pass@1234"

        if not phone:
            return Response({"detail": "Phone and password are required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate phone number
        if not re.fullmatch(r'^\d{10}$', phone):
            return Response({"detail": "Phone number must be exactly 10 digits without spaces."})
        
        try:
            # Get user by phone
            user = User.objects.get(phone=phone , countryCode = countryCode)

            # Check password
            if user.check_password(password):
                # Log the user in (optional)
                login(request, user)

                # Generate JWT tokens
                refresh = RefreshToken.for_user(user)
                access_token = str(refresh.access_token)
                refresh_token = str(refresh)

                csrf_token = get_token(request)

                return Response({
                    "status":True,
                    "message": "Login successful.",
                    "access_token": access_token,
                    "refresh_token": refresh_token,
                    "csrf_token": csrf_token,
                    "user": {
                        "id": user.id,
                        "email": user.email,
                        "phone": user.phone,
                        "role": str(user.role),
                        "name": user.firstname + user.lastname,
                        "countryCode":user.countryCode
                    }
                }, status=status.HTTP_200_OK)
            else:
                return Response({"status":False,"message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            return Response({"status":False,"message": "User with this phone does not exist."}, status=status.HTTP_404_NOT_FOUND)



class LogoutAPIView(APIView):
    """
    API View for user logout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh_token")
        if not refresh_token:
            return Response({"status":"error","Message": "Refresh token is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:

            # Blacklist the refresh token
            token = RefreshToken(refresh_token)
            token.blacklist()
            
            # Create a successful logout response
            response = Response({"status":True,"message": "Logout successful."}, status=status.HTTP_200_OK)
            
            # Clear cookies
            response.delete_cookie("csrftoken")  # Clear the CSRF cookie
            response.delete_cookie("sessionid")  # Clear the session cookie if used
            
            return response  # Return the response object
        except Exception:
            return Response({"Status":"error" ,"Message": "Invalid or expired refresh token."}, status=status.HTTP_400_BAD_REQUEST)




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
        
