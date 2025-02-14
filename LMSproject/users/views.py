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
from users.permissions import IsModeratorOrInstructor , IsModerator
from django.db.models import Q, Count

class InstructorListCreateView(generics.ListCreateAPIView):
    serializer_class = InstructorSerializer

    permission_classes = [IsAuthenticated, IsModerator] 

    
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
                    Q(phone__icontains=search_text) | 
                    Q(countryCode__icontains= search_text) 
                    # Q(assigned_courses__icontains=search_text)

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

                for course in assigned_courses:
                    instructor_data.append({
                        "instructorId": instructor.id,
                        "name": f"{instructor.firstname} {instructor.lastname}",
                        "email": instructor.email,
                        "phone": instructor.phone,
                        "countryCode": instructor.countryCode,
                        "courseId" : course.id,
                        "courseName": course.courseName,
                        "startDate": course.created_at.isoformat() if course.created_at else "",
                        "videosCount": course.videosCount if course.videosCount else 0,
                        "joinedOn": instructor.created_at.isoformat() if instructor.created_at else ""
                    })



            # instructor_data = []
            # for instructor in paginated_instructors:
            #     assigned_courses = instructor.assigned_courses.all()
                
            #     course_data = [
            #         {
            #             "course_name": course.courseName,
            #             "start_date": course.created_at.isoformat() if course.created_at else "",
            #             "videosCount" : course.videosCount if course.videosCount else 0
            #             # "end_date": course.endDate.isoformat() if course.endDate else "",
            #         }
            #         for course in assigned_courses
            #     ]

            #     print(course_data)
            #     instructor_data.append({
            #         "id": instructor.id,
            #         "name": f"{instructor.firstname} {instructor.lastname}",
            #         "email": instructor.email,
            #         "phone": instructor.phone,
            #         "countryCode" : instructor.countryCode,
            #         "assigned_courses": course_data,
            #         "joinedOn": instructor.created_at
            #     })

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
            print("IN LIst")
            search_by_course = request.query_params.get("searchByCourse", None)
            search_text = request.query_params.get("searchText", None)

            queryset = self.get_queryset()
            # Check if the request contains search filters
            is_search_query = bool(search_by_course or search_text)

            # If no instructors found
            if not queryset.exists():
                response_message = "No Search Data found." if is_search_query else "No instructors found."
                response_data = {
                    "status": True,
                    "message": response_message,
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

    permission_classes = [IsAuthenticated, IsModerator] 

    queryset = Instructor.objects.all()
    serializer_class = InstructorSerializer

    def retrieve(self, request, *args, **kwargs):
        try:
            # Get query parameters
            instructor_id = kwargs.get("pk")  # Primary key if provided
            search_by_course = request.query_params.get("searchByCourse", "").strip()
            search_text = request.query_params.get("searchText", "").strip()

            print("++++++++in retrivce" ,search_text )

            # If no instructors exist in the DB at all
            if not Instructor.objects.exists():
                return Response(
                    {
                        "status": True,
                        "message": "No records in database.",
                        "data": [],
                        "total": 0,
                        "limit": 10,
                        "page": 1,
                        "pages": 1
                    },
                    status=status.HTTP_200_OK
                )

            # Fetch instructor based on ID if provided
            if instructor_id:
                instructor = Instructor.objects.filter(pk=instructor_id).first()
                if not instructor:
                    return Response(
                        {
                            "status": True,
                            "message": "No instructor found.",
                            "data": [],
                            "total": 0,
                            "limit": 10,
                            "page": 1,
                            "pages": 1
                        },
                        status=status.HTTP_200_OK
                    )
            else:
                # If no ID is provided, apply search filters
                queryset = Instructor.objects.all()

                if search_by_course:
                    try:
                        search_by_course = int(search_by_course)  # Ensure it's a valid integer ID
                        queryset = queryset.filter(assigned_courses__id=search_by_course)
                    except ValueError:
                        return Response(
                            {
                                "status": True,
                                "message": "Invalid course ID provided.",
                                "data": [],
                                "total": 0,
                                "limit": 10,
                                "page": 1,
                                "pages": 1
                            },
                            status=status.HTTP_400_BAD_REQUEST
                        )

                if search_text:
                    queryset = queryset.filter(
                        Q(firstname__icontains=search_text) |
                        Q(lastname__icontains=search_text) |
                        Q(email__icontains=search_text) |
                        Q(phone__icontains=search_text)
                    )

                if not queryset.exists():
                    return Response(
                        {
                            "status": True,
                            "message": "No search data found." if (search_text or search_by_course) else "No instructor found.",
                            "data": [],
                            "total": 0,
                            "limit": 10,
                            "page": 1,
                            "pages": 1
                        },
                        status=status.HTTP_200_OK
                    )

                instructor = queryset.first()  # Return the first matched instructor

            # Serialize and return instructor data
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
            return Response(response, status=status.HTTP_200_OK)  # Changed from 204 to 200
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


# class InstructorDashboardView(APIView):
#     permission_classes = [IsAuthenticated, IsModeratorOrInstructor]

#     def get(self, request):
#         try:
#             # Get logged-in instructor
#             instructor = Instructor.objects.filter(email=request.user.email).first()
#             if not instructor:
#                 return Response(
#                     {"status": False, "message": "Instructor not found."},
#                     status=status.HTTP_404_NOT_FOUND,
#                 )

#             # Get assigned courses
#             courses = instructor.assigned_courses.all()
#             if not courses.exists():
#                 return Response(
#                     {"status": False, "message": "Instructor is not assigned to any course."},
#                     status=status.HTTP_404_NOT_FOUND,
#                 )

#             # Apply search filter
#             search_text = request.query_params.get("searchText", None)
#             if search_text:
#                 courses = courses.filter(
#                     Q(courseName__icontains=search_text) |
#                     Q(created_at__icontains=search_text) |
#                     Q(updated_at__icontains=search_text)
#                 )

#             # If no results after search
#             if not courses.exists():
#                 return Response(
#                     {
#                         "status": False,
#                         "message": "No search data found.",
#                         "data": [],
#                         "total": 0,
#                         "limit": 10,
#                         "page": 1,
#                         "pages": 0,
#                     },
#                     status=status.HTTP_404_NOT_FOUND,
#                 )

#             # Annotate required fields
#             courses = courses.annotate(
#                 total_videos=Count("recordings"),
#                 total_students=Count("students")
#             ).order_by("-updated_at")

#             # Pagination
#             limit = int(request.query_params.get("limit", 10))
#             page_number = int(request.query_params.get("page", 1))
#             paginator = Paginator(courses, limit)
#             page_obj = paginator.get_page(page_number)

#             # Serialize data
#             response_data = [
#                 {
#                     "courseName": course.courseName,
#                     "TotalVideos": course.total_videos,
#                     "TotalStudent": course.total_students,
#                     "LastUpdatedDate": course.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
#                 }
#                 for course in page_obj
#             ]

#             return Response(
#                 {
#                     "status": True if paginator.count > 0 else False,
#                     "message": "Courses fetched successfully.",
#                     "data": response_data,
#                     "total": paginator.count,
#                     "limit": limit,
#                     "page": page_number,
#                     "pages": paginator.num_pages,
#                 },
#                 status=status.HTTP_200_OK,
#             )

#         except Exception as e:
#             return Response(
#                 {"status": False, "message": f"An error occurred: {str(e)}"},
#                 status=status.HTTP_500_INTERNAL_SERVER_ERROR,
#             )



from datetime import datetime
from django.db.models import Q, Count
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
from zoomApp.models import Recordings
from .permissions import IsModeratorOrInstructor

class InstructorDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsModeratorOrInstructor]

    def get(self, request):
        try:
            # Get logged-in instructor
            instructor = Instructor.objects.filter(email=request.user.email).first()
            if not instructor:
                return Response(
                    {"status": False, "message": "Instructor not found."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check for course recordings request
            course_id = request.query_params.get("courseId", None)
            if course_id:
                # Fetch course and ensure instructor is assigned to it
                course = instructor.assigned_courses.filter(id=course_id).first()
                if not course:
                    return Response(
                        {"status": False, "message": "Course not found or not assigned to instructor."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Fetch recordings for the course
                recordings = Recordings.objects.filter(course=course).order_by("-created_at")

                # If no recordings found
                if not recordings.exists():
                    return Response(
                        {"status": False, "message": "No recordings found for this course.", "data": []},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Serialize response
                recordings_data = [
                    {
                        "videoTitle": recording.title,
                        "videoURL": recording.recording_url,
                        "created_at": recording.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    for recording in recordings
                ]

                return Response(
                    {"status": True, "message": "Recordings fetched successfully.", "data": recordings_data},
                    status=status.HTTP_200_OK,
                )

            # Get assigned courses
            courses = instructor.assigned_courses.all()
            if not courses.exists():
                return Response(
                    {"status": False, "message": "Instructor is not assigned to any course."},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Apply search filter
            search_text = request.query_params.get("searchText", None)
            if search_text:
                courses = courses.filter(
                    Q(courseName__icontains=search_text) |
                    Q(created_at__icontains=search_text) |
                    Q(updated_at__icontains=search_text)
                )

            # If no results after search
            if not courses.exists():
                return Response(
                    {
                        "status": False,
                        "message": "No search data found.",
                        "data": [],
                        "total": 0,
                        "limit": 10,
                        "page": 1,
                        "pages": 0,
                    },
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Annotate required fields
            courses = courses.annotate(
                total_videos=Count("recordings"),
                total_students=Count("students")
            ).order_by("-updated_at")

            # Pagination
            limit = int(request.query_params.get("limit", 10))
            page_number = int(request.query_params.get("page", 1))
            paginator = Paginator(courses, limit)
            page_obj = paginator.get_page(page_number)

            # Serialize data
            response_data = [
                {
                    "courseId" :course.id,
                    "courseName": course.courseName,
                    "TotalVideos": course.total_videos,
                    "TotalStudent": course.total_students,
                    "LastUpdatedDate": course.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
                for course in page_obj
            ]

            return Response(
                {
                    "status": True if paginator.count > 0 else False,
                    "message": "Courses fetched successfully.",
                    "data": response_data,
                    "total": paginator.count,
                    "limit": limit,
                    "page": page_number,
                    "pages": paginator.num_pages,
                },
                status=status.HTTP_200_OK,
            )

        except Exception as e:
            return Response(
                {"status": False, "message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
