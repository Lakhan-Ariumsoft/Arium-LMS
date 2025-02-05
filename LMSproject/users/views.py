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
from django.contrib.auth.hashers import make_password




import traceback

class LoginAPIView(APIView):
    """
    API View for user login using phone and password.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        phone = request.data.get("phone")
        countryCode = request.data.get("countryCode")
        # print("phone::::::::",phone)

        # password = os.getenv("DEFAULT_USER_PASSWORD")

        if not phone:
            return Response({"detail": "Phone number is required."}, status=status.HTTP_400_BAD_REQUEST)

        # Validate phone number
        if not re.fullmatch(r'^\d{10}$', phone):
            return Response({"detail": "Phone number must be exactly 10 digits without spaces."})
        
        try:
            try:
                user = User.objects.get(phone=phone, countryCode=countryCode)
            except User.DoesNotExist:
                return Response({"status": False, "message": "User not found."}, status=status.HTTP_404_NOT_FOUND)


            # Check password
            # if user.check_password(password):
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
                    "name": user.firstname +" " + user.lastname,
                    "countryCode":user.countryCode
                }
            }, status=status.HTTP_200_OK)
            # else:
                # return Response({"status":False,"message": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)

        except User.DoesNotExist:
            return Response({"status":False,"message": "User with this phone does not exist."}, status=status.HTTP_404_NOT_FOUND)
    
        except Exception as e:
            # Print the full stack trace to the terminal
            print("An error occurred:", str(e))
            traceback.print_exc()  # This will print the full traceback for debugging

            return Response({"status": False, "message": "An unexpected error occurred."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



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






from rest_framework import generics, status
from rest_framework.response import Response
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.db.models import Q
from .serializers import InstructorSerializer
from .models import Instructor
from courses.models import Courses
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction


class InstructorListCreateView(generics.ListCreateAPIView):
    serializer_class = InstructorSerializer
    
    def get_queryset(self):
        try:
            queryset = Instructor.objects.all().order_by("-created_at")
            
            # Handle search filters
            search_by_course = self.request.query_params.get("searchByCourse", None)
            search_text = self.request.query_params.get("searchText", None)

            if search_by_course:
                try:
                    search_by_course = int(search_by_course)  # Ensure it's a valid ID
                    queryset = queryset.filter(assigned_courses__id=search_by_course)
                except ValueError:
                    return Instructor.objects.none()  # Return empty queryset if invalid ID
            
            if search_text:
                queryset = queryset.filter(
                    Q(firstname__icontains=search_text) |
                    Q(lastname__icontains=search_text) |
                    Q(email__icontains=search_text) |
                    Q(phonenumber__icontains=search_text)
                )
            
            return queryset.distinct()
        
        except Exception as e:
            # Return an empty queryset to avoid breaking the API
            print(f"Error in get_queryset: {str(e)}")  # Debugging purpose
            return Instructor.objects.none()  

    def get_paginated_instructors(self, request, instructors_queryset):
        """
        Handles pagination for instructors data and returns the paginated response.
        """
        try:
            limit = int(request.query_params.get('limit', 10))  # Default limit 10
            page = request.query_params.get('page', 1)  # Default page 1

            paginator = Paginator(instructors_queryset, limit)

            try:
                paginated_instructors = paginator.get_page(page)
            except PageNotAnInteger:
                paginated_instructors = paginator.page(1)
            except EmptyPage:
                paginated_instructors = paginator.page(paginator.num_pages)

            instructor_data = []
            for instructor in paginated_instructors:
                assigned_courses = instructor.assigned_courses.all()
                
                course_data = [
                    {
                        "course_name": course.courseName,
                        "start_date": course.created_at.isoformat() if course.created_at else "",
                        # "end_date": course.endDate.isoformat() if course.endDate else "",
                    }
                    for course in assigned_courses
                ]

                print(course_data)
                instructor_data.append({
                    "id": instructor.id,
                    "name": f"{instructor.firstname} {instructor.lastname}",
                    "email": instructor.email,
                    "phone": instructor.phonenumber,
                    "assigned_courses": course_data,
                    "joinedOn": instructor.created_at
                })

            response = {
                "status": True,
                "message": "Fetched successfully.",
                "data": instructor_data,
                "total": paginator.count,
                "limit": limit,
                "page": paginated_instructors.number,
                "pages": paginator.num_pages,
            }

            return Response(response, status=status.HTTP_200_OK)

        except Exception as e:
            return Response(
                {"status": False, "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def list(self, request, *args, **kwargs):
        try:
            queryset = self.get_queryset()

            # If no instructors found, return empty data in the same format
            if not queryset.exists():
                response_data = {
                    "status": True,
                    "message": "No instructors found.",
                    "data": [],
                    "total": 0,
                    "limit": 10,
                    "page": 1,
                    "pages": 1
                }
                return Response(response_data, status=status.HTTP_200_OK)

            # Process paginated response
            return self.get_paginated_instructors(request, queryset)

        except Exception as e:
            response_data = {
                "status": False,
                "message": f"An error occurred: {str(e)}",
                "data": [],
                "total": 0,
                "limit": 10,
                "page": 1,
                "pages": 1
            }
            return Response(response_data, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def create(self, request, *args, **kwargs):
        try:
            print("Request Data:", request.data)
            serializer = self.serializer_class(data=request.data)

            if serializer.is_valid():
                assigned_courses = request.data.get('assigned_courses', [])

                with transaction.atomic():  # Ensures rollback on failure
                    instructor = serializer.save()
                    if assigned_courses:
                        instructor.assigned_courses.set(assigned_courses)

                    response = {"status": True, "message": "Instructor added successfully."}
                    return Response(response, status=status.HTTP_201_CREATED)

            return Response(
                {"status": False, "message": "Invalid data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class InstructorRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            # Check if the instructor exists
            pk = kwargs.get("pk")
            if not Instructor.objects.filter(pk=pk).exists():
                return Response(
                    {
                        "status": True,  # ✅ API executed successfully
                        "message": "No instructor found.",
                        "data": [],
                        "total": 0,
                        "limit": 10,
                        "page": 1,
                        "pages": 1
                    },
                    status=status.HTTP_200_OK  # ✅ No instructor, but request was successful
                )

            instructor = self.get_object()  # Retrieve the instructor
            serializer = self.get_serializer(instructor)
            return Response(
                {
                    "status": True,
                    "message": "Fetched successfully.",
                    "data": serializer.data,
                    "total": 1,
                    "limit": 10,
                    "page": 1,
                    "pages": 1
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            return Response(
                {
                    "status": False,
                    "message": f"An error occurred: {str(e)}",
                    "data": [],
                    "total": 0,
                    "limit": 10,
                    "page": 1,
                    "pages": 1
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


    def update(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            serializer = self.serializer_class(instance, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                response = {
                    "status": True,
                    "message": "Instructor updated successfully."
                }
                return Response(response, status=status.HTTP_200_OK)
            return Response(
                {"status": False, "message": "Invalid data", "errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ObjectDoesNotExist:
            return Response(
                {"status": False, "message": "Instructor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            instance.delete()
            response = {"status": True, "message": "Instructor deleted successfully."}
            return Response(response, status=status.HTTP_204_NO_CONTENT)
        except ObjectDoesNotExist:
            return Response(
                {"status": False, "message": "Instructor not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        except Exception as e:
            return Response(
                {"status": False, "message": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
