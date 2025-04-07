from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from django.db.models import Q
from django.db import transaction
from courses.models import Courses
from .models import Students, Enrollment
from .serializers import StudentsSerializer, EnrollmentSerializer 
from users.serializers import UserSerializer
from django.contrib.auth import get_user_model
from datetime import datetime
from rest_framework.response import Response
from rest_framework import status

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from .models import Students, Enrollment
from zoomApp.models import Recordings
from courses.models import Courses
from users.permissions import IsModerator
from users.models import User
# from django.http import JsonResponse
from django.db import DatabaseError
from rest_framework.exceptions import ValidationError
from django.utils.timezone import now 



def get_paginated_students(request, students_queryset, search_course):
    """
    Handles pagination for the students data and returns the paginated response.
    """
    try:
        limit = int(request.query_params.get('limit', 10))
        page = int(request.query_params.get('page', 1))

        student_data = []
        all_enrollments = []

        # Filtering enrollments based on searchCourse if provided
        for student in students_queryset:
            enrollments = Enrollment.objects.filter(student=student)
            
            # If search_course is given, filter enrollments by course ID
            if search_course:
                enrollments = enrollments.filter(courses__id=search_course)

            for enrollment in enrollments:
                all_enrollments.append({
                    "studentId": student.id,
                    "name": f"{student.firstname} {student.lastname}",
                    "countryCode": student.countryCode if student.countryCode else "",
                    "phone": student.phone,
                    "email": student.email,
                    "dob": student.dob.strftime("%Y-%m-%d") if student.dob else "",
                    "enrollmentId": enrollment.id,
                    "course": enrollment.courses.courseName,
                    "start_date": enrollment.enrollmentDate.isoformat() if enrollment.enrollmentDate else "",
                    "end_date": enrollment.expiryDate.isoformat() if enrollment.expiryDate else "",
                    "status": enrollment.status
                })

        # Apply pagination to enrollments instead of students
        paginator = Paginator(all_enrollments, limit)

        try:
            paginated_data = paginator.page(page)
        except PageNotAnInteger:
            paginated_data = paginator.page(1)
        except EmptyPage:
            paginated_data = []

        response = {
            "status": True,
            "message": "Fetched successfully.",
            "data": list(paginated_data),
            "total": paginator.count,
            "limit": limit,
            "page": page,
            "pages": paginator.num_pages,
        }

        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"status": False, "message": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


def checkStudentsEnrollment(student):
    """
    Check if the student is enrolled in any course other than the ones being deleted.
    """
    try:
        return Enrollment.objects.filter(student=student).exists()
    except Exception as e:
        # Log the error (if logging is set up) and return a structured error message
        print(f"Error checking enrollment for student {student.id}: {str(e)}")
        return {
            "error": True,
            "message": f"An unexpected error occurred while checking enrollments: {str(e)}"
        }

class StudentsListCreateAPIView(APIView):
    """
    View to handle fetching all students, creating a student, and search/filter students with proper exception handling.
    """

    permission_classes = [IsAuthenticated, IsModerator] 

    def get(self, request):
        try:
            search_text = request.query_params.get('searchText', None)
            search_course = request.query_params.get('searchCourse', None)
            search_status = request.query_params.get('searchStatus', None)
            country_code = request.query_params.get("countryCode", "").strip()

            query = Q()

            if search_text:
                query |= Q(firstname__icontains=search_text) | Q(lastname__icontains=search_text)
                query |= Q(email__icontains=search_text) | Q(phone__icontains=search_text)

            if country_code:
                query &= Q(countryCode=country_code)

            if search_course:
                try:
                    search_course = int(search_course)
                    query &= Q(enrollment__courses__id=search_course)
                except ValueError:
                    print(f"Searching by name: {search_course}")

            if search_status:
                query &= Q(enrollment__status__icontains=search_status)

            students_queryset = Students.objects.filter(query).distinct().order_by('-created_on')

            # No records in the database
            if not Students.objects.exists():
                return Response(
                    {"status": True, "message": "No records found in the database.", "data": [], "total": 0, "page": 1, "pages": 1},
                    status=status.HTTP_404_NOT_FOUND
                )

            # No search results found
            if search_text or search_course or search_status:
                if not students_queryset.exists():
                    return Response(
                        {"status": True, "message": "No search data found", "data": [], "total": 0, "page": 1, "pages": 1},
                        status=status.HTTP_404_NOT_FOUND
                    )

            return get_paginated_students(request, students_queryset, search_course)

        except Exception as e:
            print(f"Error occurred while fetching students: {str(e)}")
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Create a new student and enroll them in selected courses.
        """
        try:
            with transaction.atomic():
                student_data = request.data.get("student")
                enrollment_data = request.data.get("enrollment")

                # Validate enrollment data
                if not enrollment_data or not isinstance(enrollment_data, list):
                    return Response(
                        {"status": "error", "message": "Enrollment data must be a non-empty list."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                # Ensure each enrollment contains a valid course ID
                for enrollment in enrollment_data:
                    if not enrollment.get("course"):
                        return Response(
                            {"status": "error", "message": "Each enrollment must include a valid course ID."},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                # Create the student
                student_serializer = StudentsSerializer(data=student_data)
                if student_serializer.is_valid():
                    student = student_serializer.save()

                    # Enroll the student in selected courses
                    for enrollment in enrollment_data:
                        course_id = enrollment.get("course")
                        try:
                            course = get_object_or_404(Courses, id=course_id)

                            # Ensure the student is not already enrolled
                            if Enrollment.objects.filter(student=student, courses=course).exists():
                                return Response(
                                    {"status": "error", "message": f"Student is already enrolled in {course.courseName}."},
                                    status=status.HTTP_400_BAD_REQUEST,
                                )

                            # Convert date strings to datetime.date objects
                            enrollment_date = enrollment.get("enrollmentDate" , None)
                            expiry_date = enrollment.get("expiryDate",None)
                            enrollStatus = enrollment.get("enrollmentStatus","Active")

                            if enrollment_date:
                                enrollment_date = datetime.strptime(enrollment_date, "%Y-%m-%d").date()
                            else:
                                enrollment_date = None

                            if expiry_date:
                                expiry_date = datetime.strptime(expiry_date, "%Y-%m-%d").date()
                            else:
                                expiry_date = None  

                            # Create enrollment
                            Enrollment.objects.create(
                                student=student,
                                courses=course,
                                enrollmentDate=enrollment_date,
                                expiryDate=expiry_date,
                                status = enrollStatus
                            )

                            # Update the course's student count
                            course.studentsCount += 1
                            course.save(update_fields=["studentsCount"])

                        except Courses.DoesNotExist:
                            return Response(
                                {"status": "error", "message": f"Course with ID {course_id} does not exist."},
                                status=status.HTTP_400_BAD_REQUEST,
                            )

                    return Response(
                        {"status": "success", "data": student_serializer.data},
                        status=status.HTTP_201_CREATED,
                    )

                return Response(
                    {"status": "error", "message": student_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except Exception as e:
            print(f"Error: {e}")  # Debugging log
            return Response(
                {"status": "error", "message": f"An error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StudentsDetailAPIView(APIView):
    """
    View to handle fetching, updating, and deleting a specific student.
    """

    permission_classes = [IsAuthenticated, IsModerator] 

    def get(self, request, pk=None):
        try:
            student = get_object_or_404(Students, pk=pk)
            enrollments = Enrollment.objects.filter(student=student)
            student_data = StudentsSerializer(student).data
            enrollment_data = EnrollmentSerializer(enrollments, many=True).data
            return Response({"student": student_data, "enrollments": enrollment_data}, status=status.HTTP_200_OK)
        except Students.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)
    

    def patch(self, request, pk=None):
        try:
            # Start a transaction to ensure data consistency
            with transaction.atomic():
                # Fetch the student object
                student = get_object_or_404(Students, pk=pk)

                # Partial update for student fields
                student_serializer = StudentsSerializer(student, data=request.data, partial=True)
                if student_serializer.is_valid():
                    updated_student = student_serializer.save()
                    updated_student.refresh_from_db()  # Refresh instance to fetch updated values

                    # Handle enrollment updates if provided
                    if 'enrollments' in request.data:
                        updated_enrollments = []
                        for enrollment_data in request.data['enrollments']:
                            course_id = enrollment_data.get("courses")

                            # Check if enrollment exists for this student-course pair
                            enrollment = Enrollment.objects.filter(
                                student=updated_student, courses=course_id
                            ).first()

                            if enrollment:
                                # Update existing enrollment
                                enrollment_data['student'] = updated_student.id  # Ensure correct student ID
                                enrollment_serializer = EnrollmentSerializer(enrollment, data=enrollment_data, partial=True)

                                if enrollment_serializer.is_valid():
                                    # Update the enrollment fields explicitly from the validated data
                                    enrollment.enrollmentDate = enrollment_serializer.validated_data.get('enrollmentDate', enrollment.enrollmentDate)
                                    enrollment.expiryDate = enrollment_serializer.validated_data.get('expiryDate', enrollment.expiryDate)

                                    # Set the status based on expiryDate
                                    if enrollment.expiryDate:
                                        if enrollment.expiryDate < now().date():
                                            enrollment.status = 'expired'  # Set to 'expired' if the expiryDate is in the past
                                        else:
                                            enrollment.status = 'active'  # Set to 'active' if expiryDate is in the future
                                    else:
                                        enrollment.status = 'active'  # If expiryDate is None, keep status as 'active'

                                    # Apply any updates to status (if status is provided in the request, override the current one)
                                    enrollment.status = enrollment_serializer.validated_data.get('status', enrollment.status)

                                    # Save the enrollment after making updates
                                    enrollment.save()

                                    updated_enrollments.append(EnrollmentSerializer(enrollment).data)
                                else:
                                    return Response({
                                        "error": "Enrollment update failed.",
                                        "details": enrollment_serializer.errors
                                    }, status=status.HTTP_400_BAD_REQUEST)

                            else:
                                # Create new enrollment only if no existing enrollment for this student-course
                                enrollment_data['student'] = updated_student.id
                                new_enrollment_serializer = EnrollmentSerializer(data=enrollment_data)

                                if new_enrollment_serializer.is_valid():
                                    # Check status for new enrollment based on expiryDate
                                    expiry_date = new_enrollment_serializer.validated_data.get('expiryDate', None)
                                    if expiry_date:
                                        if expiry_date < now().date():
                                            enrollment_data['status'] = 'expired'  # If expiryDate is in the past, set status to 'expired'
                                        else:
                                            enrollment_data['status'] = 'active'  # If expiryDate is in the future, set status to 'active'
                                    else:
                                        enrollment_data['status'] = 'active'  # If expiryDate is None, keep status as 'active'

                                    new_enrollment = new_enrollment_serializer.save()

                                    updated_enrollments.append(EnrollmentSerializer(new_enrollment).data)

                                else:
                                    return Response({
                                        "error": "Enrollment creation failed.",
                                        "details": new_enrollment_serializer.errors
                                    }, status=status.HTTP_400_BAD_REQUEST)

                        # Return the response with the updated student and enrollments
                        return Response({
                            "message": "Student and enrollment(s) updated successfully",
                            "status": "success",
                            "data": {
                                "student": StudentsSerializer(updated_student).data,
                                "enrollments": updated_enrollments
                            }
                        }, status=status.HTTP_200_OK)

                    else:
                        # If no enrollments were provided, just return the updated student data
                        return Response({
                            "message": "Student updated successfully",
                            "status": "success",
                            "data": StudentsSerializer(updated_student).data
                        }, status=status.HTTP_200_OK)

                else:
                    return Response({
                        "error": "Student update failed.",
                        "details": student_serializer.errors
                    }, status=status.HTTP_400_BAD_REQUEST)

        except Students.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        except ValidationError as e:
            return Response({"error": "Validation error", "details": e.detail}, status=status.HTTP_400_BAD_REQUEST)
        
        except DatabaseError:
            return Response({"error": "Database error occurred"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk=None):
        try:
            with transaction.atomic():
                # Fetch the enrollment instance
                try:
                    enrollment = Enrollment.objects.get(pk=pk)
                    student = enrollment.student  # Get student from enrollment
                except Enrollment.DoesNotExist:
                    return Response(
                        {"success": False, "message": "Enrollment not found."},
                        status=status.HTTP_404_NOT_FOUND
                    )

                # Get associated course and update students count
                course = enrollment.courses
                if course.studentsCount > 0:  # Prevent negative count
                    course.studentsCount = max(0, course.studentsCount - 1)
                    course.save(update_fields=["studentsCount"])

                # Delete the specific enrollment
                enrollment.delete()

                # Check if student has any remaining enrollments
                remaining_enrollments = Enrollment.objects.filter(student=student).exists()

                if not remaining_enrollments:
                    # If no enrollments remain, deactivate user and delete student
                    if hasattr(student, "phone") and student.phone:
                        user = User.objects.filter(phone=student.phone).first()
                        if user:
                            user.delete() 

                    student.delete()

                    return Response(
                        {"success": True, "message": "Student deleted as no enrollments were found."},
                        status=status.HTTP_200_OK
                    )

                return Response(
                    {"success": True, "message": "Enrollment deleted successfully."},
                    status=status.HTTP_200_OK
                )

        except Exception as e:
            return Response(
                {"success": False, "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    


from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.exceptions import ObjectDoesNotExist

class DashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    
    def get(self, request):
        try:
            user = request.user
            
            if not user.is_authenticated:
                return Response({"status": False, "message": "Unauthorized access."}, status=status.HTTP_401_UNAUTHORIZED)


            # Check if a phone number is provided in query parameters   
            # phone_number = request.query_params.get("phone", "").strip()
            # country_code = request.query_params.get("countryCode", "").strip()

            if user.role.name.lower() == "moderator":

                    # Check if a phone number is provided in query parameters
                phone_number = request.query_params.get("phone", "")
                country_code = request.query_params.get("countryCode", "")

                if phone_number and country_code:
                # Ensure phone_number and country_code are not None before stripping
                    phone_number = phone_number.strip() 
                    country_code = country_code.strip()
                # Ensure both phone number and country code are provided
                else:
                    return Response({"status": False, "message": "phoneNumber and countryCode is required."}, status=status.HTTP_400_BAD_REQUEST)

                # Fetch student based on phone number and country code
                student = Students.objects.filter(phone=phone_number, countryCode=country_code).first()
                
                if not student:
                    return Response({"status": False, "message": "Student with given phone number and country code not found."}, status=status.HTTP_404_NOT_FOUND)

            else:
                # Default case: Fetch student for the logged-in user
                student = get_object_or_404(Students, email=user.email)

            # Get enrollments (ensuring they exist)
            enrollments = Enrollment.objects.filter(student=student)
            if not enrollments.exists():
                return Response({"status": False, "message": "No enrollments found."}, status=status.HTTP_404_NOT_FOUND)

            # Extract query params
            search_text = request.query_params.get("searchText", "")
            search_course_id = request.query_params.get("searchCourse", "")
            date_range = request.query_params.get("dateRange", "")

            
            enrolled_courses_data = []
            unique_meetings = set()

            for enrollment in enrollments:
                course = enrollment.courses
                expiry_date = enrollment.expiryDate  # Fetch expiry date if available
                enrollment_date = enrollment.enrollmentDate
            # for enrollment in enrollments:
            #     course = enrollment.courses
            #     expiry_date = enrollment.expiryDate  # Fetch expiry date if available

                # Fetch Zoom recordings for this course before expiry date
                # Only apply expiry date filter if expiry_date is not None
                # if expiry_date:
                #     zoom_meetings = Recordings.objects.filter(course=course, created_at__date__lte=expiry_date)
                # else:
                zoom_meetings = Recordings.objects.filter(course=course)  # Avoid passing None

                # if expiry_date:
                #     zoom_meetings = Recordings.objects.filter(
                #         course=course,
                #         created_on__range=(enrollment_date, expiry_date)
                #     )
                # else:
                #     zoom_meetings = Recordings.objects.filter(
                #         course=course,
                #         created_on__gte=enrollment_date
                #     )

                # zoom_meetings = Recordings.objects.filter(course=course, created_at__date__lte=expiry_date)

                # Apply search text filter
                if search_text:
                    zoom_meetings = zoom_meetings.filter(title__icontains=search_text)

                # Apply course filter (handle invalid IDs)
                if search_course_id:
                    try:
                        course_id = int(search_course_id)
                        zoom_meetings = zoom_meetings.filter(course__id=course_id)
                    except ValueError:
                        return Response({
                            "status": False,
                            "message": "Invalid course ID format. Must be an integer.",
                            "data": [], "total": 0, "limit": 10, "page": 1, "pages": 1
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Apply date range filter (handle incorrect format)
                if date_range:
                    try:
                        start_date, end_date = date_range.split(",")
                        start_date = datetime.strptime(start_date.strip(), "%Y-%m-%d").date()
                        end_date = datetime.strptime(end_date.strip(), "%Y-%m-%d").date()
                        zoom_meetings = zoom_meetings.filter(updated_at__date__range=(start_date, end_date))
                    except ValueError:
                        return Response({
                            "status": False,
                            "message": "Invalid date range format. Expected: YYYY-MM-DD,YYYY-MM-DD",
                            "data": [], "total": 0, "limit": 10, "page": 1, "pages": 1
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Collect unique meeting data
                for meeting in zoom_meetings:
                    unique_key = (
                        meeting.title.strip().lower(),
                        meeting.duration,
                        meeting.updated_at.strftime("%Y-%m-%d %H:%M:%S"),
                    )

                    if unique_key not in unique_meetings:
                        unique_meetings.add(unique_key)
                        enrolled_courses_data.append({
                            "id":meeting.id,
                            "courseId": course.id,
                            "courseName": course.courseName,
                            "title": meeting.title,
                            "recordingUrl": meeting.recording_url,
                            "duration": meeting.duration,
                            "updatedAt": unique_key[2]
                        })

            # Return final response
            return Response({
                "status": True,
                "message": "Fetched successfully.",
                "data": enrolled_courses_data,
                "total": len(enrolled_courses_data),
                "limit": 10,
                "page": 1,
                "pages": 1
            }, status=status.HTTP_200_OK)

        except ObjectDoesNotExist:
            return Response({"status": False, "message": "Requested data not found."}, status=status.HTTP_404_NOT_FOUND)

        except ValueError as ve:
            return Response({"status": False, "message": f"Invalid input: {str(ve)}"}, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # def get(self, request):
    #     # Get the logged-in user
    #     user = request.user

    #     # Fetch the student instance
    #     student = get_object_or_404(Students, email=user.email)  # Assuming email is the identifier

    #     # Fetch courses where the student is enrolled
    #     enrolled_courses = Courses.objects.filter(enrollment__student=student).distinct()

    #     # Get search parameters
    #     search_text = request.query_params.get('searchText', None)
    #     search_course_id = request.query_params.get('searchCourse', None)
    #     date_range = request.query_params.get('dateRange', None)

    #     enrolled_courses_data = []
    #     unique_meetings = set()
        
    #     for course in enrolled_courses:
    #         # Fetch Zoom recordings for the course
    #         zoom_meetings = Recordings.objects.filter(course=course)

    #         # Apply filters
    #         if search_text:
    #             zoom_meetings = zoom_meetings.filter(title__icontains=search_text)

    #         if search_course_id:
    #             try:
    #                 course_id = int(search_course_id)
    #                 zoom_meetings = zoom_meetings.filter(course__id=course_id)
    #             except ValueError:
    #                 return Response({
    #                     "status": False,
    #                     "message": "Invalid course ID. It should be a valid integer.",
    #                     "data": [],
    #                     "total": 0,
    #                     "limit": 10,
    #                     "page": 1,
    #                     "pages": 1
    #                 }, status=status.HTTP_400_BAD_REQUEST)

    #         if date_range:
    #             try:
    #                 start_date, end_date = date_range.split(',')
    #                 start_date = datetime.strptime(start_date.strip(), "%Y-%m-%d")
    #                 end_date = datetime.strptime(end_date.strip(), "%Y-%m-%d")
    #                 zoom_meetings = zoom_meetings.filter(updated_at__date__range=(start_date, end_date))
    #             except ValueError:
    #                 return Response({
    #                     "status": False,
    #                     "message": "Invalid date range format. Expected format: YYYY-MM-DD,YYYY-MM-DD",
    #                     "data": [],
    #                     "total": 0,
    #                     "limit": 10,
    #                     "page": 1,
    #                     "pages": 1
    #                 }, status=status.HTTP_400_BAD_REQUEST)

    #         # Collect course and meeting data
    #         # for meeting in zoom_meetings:
    #         #     enrolled_courses_data.append({
    #         #         "courseId": course.id,
    #         #         "courseName": course.courseName,
    #         #         "title": meeting.title,
    #         #         "recordingUrl": meeting.recording_url,
    #         #         "duration": meeting.duration,
    #         #         "updatedAt": meeting.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    #         #     })

    #         # enrolled_courses_data = []

    #         for meeting in zoom_meetings:
    #             unique_key = (meeting.title.strip().lower(), meeting.duration, meeting.updated_at.strftime("%Y-%m-%d %H:%M:%S"))

    #             if unique_key not in unique_meetings:
    #                 unique_meetings.add(unique_key)  # Store the unique key to prevent duplicates
    #                 enrolled_courses_data.append({
    #                     "courseId": course.id,
    #                     "courseName": course.courseName,
    #                     "title": meeting.title,
    #                     "recordingUrl": meeting.recording_url,
    #                     "duration": meeting.duration,
    #                     "updatedAt": unique_key[2]
    #                 })

    #     # Response data
    #     response_data = {
    #         "status": True,
    #         "message": "Fetched successfully.",
    #         "data": enrolled_courses_data,
    #         "total": len(enrolled_courses_data),
    #         "limit": 10,
    #         "page": 1,
    #         "pages": 1
    #     }

    #     return Response(response_data, status=status.HTTP_200_OK)

    # def get(self, request):
    #     # Get the logged-in user
    #     user = request.user

    #     # Get the student instance
    #     student = get_object_or_404(Students, email=user.email)  # Assuming email is the identifier

    #     # Get all enrolled courses for the student
    #     enrollments = Enrollment.objects.filter(student=student, status="active")  # Ensure only active enrollments

    #     # Get search parameters
    #     search_text = request.query_params.get('searchText', None)
    #     search_course_id = request.query_params.get('searchCourse', None)  # Now filtering by course ID
    #     date_range = request.query_params.get('dateRange', None)  # Expected format: "YYYY-MM-DD,YYYY-MM-DD"

    #     # Fetch course details and Zoom meeting details for enrolled courses
    #     enrolled_courses_data = []
    #     for enrollment in enrollments:
    #         course = enrollment.courses

    #         # Fetch Zoom meetings associated with this course
    #         zoom_meetings = Recordings.objects.filter(course=course)

    #         # Apply filters
    #         if search_text:
    #             zoom_meetings = zoom_meetings.filter(title__icontains=search_text)

    #         if search_course_id:
    #             try:
    #                 course_id = int(search_course_id)
    #                 zoom_meetings = zoom_meetings.filter(course__id=course_id)
    #             except ValueError:
    #                 return Response({
    #                     "status": False,
    #                     "message": "Invalid course ID. It should be a valid integer.",
    #                     "data": [],
    #                     "total": 0,
    #                     "limit": 10,
    #                     "page": 1,
    #                     "pages": 1
    #                 }, status=status.HTTP_400_BAD_REQUEST)

    #         if date_range:
    #             try:
    #                 start_date, end_date = date_range.split(',')
    #                 start_date = datetime.strptime(start_date.strip(), "%Y-%m-%d")
    #                 end_date = datetime.strptime(end_date.strip(), "%Y-%m-%d")
    #                 zoom_meetings = zoom_meetings.filter(updated_at__date__range=(start_date, end_date))
    #             except ValueError:
    #                 return Response({
    #                     "status": False,
    #                     "message": "Invalid date range format. Expected format: YYYY-MM-DD,YYYY-MM-DD",
    #                     "data": [],
    #                     "total": 0,
    #                     "limit": 10,
    #                     "page": 1,
    #                     "pages": 1
    #                 }, status=status.HTTP_400_BAD_REQUEST)

    #         for meeting in zoom_meetings:
    #             course_data = {
    #                 "courseId": course.id,
    #                 "courseName": course.courseName,
    #                 "title": meeting.title,
    #                 "recordingUrl": meeting.recording_url,
    #                 "duration": meeting.duration,
    #                 "updatedAt": meeting.updated_at.strftime("%Y-%m-%d %H:%M:%S")  # Format date/time
    #             }
    #             enrolled_courses_data.append(course_data)

    #     # Response data (Always consistent format)
    #     response_data = {
    #         "status": True,
    #         "message": "Fetched successfully.",
    #         "data": enrolled_courses_data,
    #         "total": len(enrolled_courses_data),
    #         "limit": 10,
    #         "page": 1,
    #         "pages": 1
    #     }

    #     return Response(response_data, status=status.HTTP_200_OK)

    # def get(self, request):
    #     # Get the logged-in user
    #     user = request.user

    #     # Check if the user is a student
    #     # if user.role == "student":
    #     #     return Response({
    #     #         "status": False,
    #     #         "message": "Access denied. Only students can view this dashboard.",
    #     #         "data": [],
    #     #         "total": 0,
    #     #         "limit": 10,
    #     #         "page": 1,
    #     #         "pages": 1
    #     #     }, status=status.HTTP_403_FORBIDDEN)

    #     # Get the student instance
    #     student = get_object_or_404(Students, email=user.email)  # Assuming email is the identifier

    #     # Get all enrolled courses for the student
    #     enrollments = Enrollment.objects.filter(student=student, status="active")  # Ensure only active enrollments
    #     if not enrollments.exists():
    #         return Response({
    #             "status": True,
    #             "message": "No enrolled courses found.",
    #             "data": [],
    #             "total": 0,
    #             "limit": 10,
    #             "page": 1,
    #             "pages": 1
    #         }, status=status.HTTP_200_OK)

    #     # Fetch course details and Zoom meeting details for enrolled courses
    #     enrolled_courses_data = []
    #     for enrollment in enrollments:
    #         course = enrollment.courses

    #         # Fetch Zoom meetings associated with this course
    #         zoom_meetings = Recordings.objects.filter(course=course)

    #         for meeting in zoom_meetings:
    #             course_data = {
    #                 "courseName": course.courseName,
    #                 "title": meeting.title,
    #                 "recordingUrl": meeting.recording_url,
    #                 "duration": meeting.duration,
    #                 "updatedAt": meeting.updated_at.strftime("%Y-%m-%d %H:%M:%S")  # Format date/time
    #             }
    #             enrolled_courses_data.append(course_data)

    #     # If no Zoom meetings found for the enrolled courses
    #     if not enrolled_courses_data:
    #         return Response({
    #             "status": True,
    #             "message": "No Recordings found for the enrolled courses.",
    #             "data": [],
    #             "total": 0,
    #             "limit": 10,
    #             "page": 1,
    #             "pages": 1
    #         }, status=status.HTTP_200_OK)

    #     # Response data
    #     response_data = {
    #         "status": True,
    #         "message": "Fetched successfully.",
    #         "data": enrolled_courses_data,
    #         "total": len(enrolled_courses_data),
    #         "limit": 10,
    #         "page": 1,
    #         "pages": 1
    #     }

    #     return Response(response_data, status=status.HTTP_200_OK)
