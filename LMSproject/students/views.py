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

from rest_framework.response import Response
from rest_framework import status
from django.db.models import Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage


from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.db.models import Q
from .models import Students, Enrollment
from zoomApp.models import ZoomMeeting
from courses.models import Courses

def get_paginated_students(request, students_queryset):
    """
    Handles pagination for the students data and returns the paginated response.
    """
    try:
        # Default limit and page if not provided in the query params
        limit = int(request.query_params.get('limit', 10))
        page = request.query_params.get('page', 1)

        paginator = Paginator(students_queryset, limit)

        try:
            # Get the requested page
            paginated_students = paginator.get_page(page)
        except PageNotAnInteger:
            # If the page is not an integer, return the first page
            paginated_students = paginator.page(1)
        except EmptyPage:
            # If the page is out of range, return an empty result
            paginated_students = []

        # Prepare student data
        student_data = []
        for student in paginated_students:
            enrollments = Enrollment.objects.filter(student=student)
            student_serializer = StudentsSerializer(student)

            enrolled_courses = []

            for enrollment in enrollments:
                enrolled_courses.append({
                    "course": enrollment.courses.courseName,
                    "start_date": enrollment.enrollmentDate.isoformat() if enrollment.enrollmentDate else "",
                    "end_date": enrollment.expiryDate.isoformat() if enrollment.expiryDate else ""
                })


            student_data.append({
                "_id": student.id,
                "name": f"{student.firstname} {student.lastname}",
                "countryCode": student.countryCode,
                "phone": student.phone,
                "email": student.email,
                "status": student.status,
                "enrolled_courses": enrolled_courses,
            })

        # Return paginated response
        response = {
            "status": True,
            "message": "Fetched successfully.",
            "data": student_data,
            "total": paginator.count,
            "limit": limit,
            "page": int(paginated_students.number) if paginated_students else int(page),
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

    from django.db.models import Q
    from rest_framework.response import Response
    from rest_framework import status

    def get(self, request):
        try:
            # Get query parameters for filtering
            search_text = request.query_params.get('searchText', None)
            search_course = request.query_params.get('searchCourse', None)
            search_status = request.query_params.get('searchStatus', None)

            # Build the Q object to filter the queryset
            query = Q()

            if search_text:
                query |= Q(firstname__icontains=search_text) | Q(lastname__icontains=search_text)
                query |= Q(email__icontains=search_text) | Q(phone__icontains=search_text)
                query |= Q(status__icontains=search_text)

            if search_course:
                query &= Q(enrollment__courses__courseName__icontains=search_course)

            if search_status:
                query &= Q(status__icontains=search_status)

            # Filter students based on the query
            students_queryset = Students.objects.filter(query).distinct().order_by('id')

            # Case 1: No students in the database
            if not Students.objects.exists():
                return Response({"message": "No records found in the database."}, status=status.HTTP_404_NOT_FOUND)

            # Case 2: Query parameter provided but no matching records found
            if search_text or search_course or search_status:
                if not students_queryset.exists():
                    query_params = []
                    if search_text:
                        query_params.append(f"'{search_text}'")
                    if search_course:
                        query_params.append(f"'{search_course}'")
                    if search_status:
                        query_params.append(f"'{search_status}'")

                    query_msg = ", ".join(query_params)
                    return Response({"message": f"No data found for {query_msg}."}, status=status.HTTP_404_NOT_FOUND)

            # Case 3: Return paginated students
            return get_paginated_students(request, students_queryset)

        except Exception as e:
            # Log the error if needed
            print(f"Error occurred while fetching students: {str(e)}")
            return Response(
                {"message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """
        Create a new student and enroll them in selected courses.
        """
        try:
            # Wrap the entire operation in an atomic transaction
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
                            # Ensure the course exists
                            course = get_object_or_404(Courses, id=course_id)

                            # Check if the student is already enrolled in the course
                            if Enrollment.objects.filter(student=student, courses=course).exists():
                                raise ValueError(f"Student is already enrolled in the course: {course.courseName}")

                            # Create enrollment
                            Enrollment.objects.create(
                                student=student,
                                courses=course,
                                enrollmentDate=enrollment.get("enrollmentDate"),
                                expiryDate=enrollment.get("expiryDate"),
                            )

                            # Update the course's student count
                            course.studentsCount += 1
                            course.save(update_fields=["studentsCount"])

                        except Courses.DoesNotExist:
                            raise ValueError(f"Course with ID {course_id} does not exist.")
                        except Exception as e:
                            raise ValueError(f"An error occurred while enrolling in course ID {course_id}: {str(e)}")

                    return Response(
                        {"status": "success", "data": student_serializer.data},
                        status=status.HTTP_201_CREATED,
                    )

                return Response(
                    {"status": "error", "message": student_serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST,
                )

        except ValueError as e:
            # Handle specific validation or business logic errors
            return Response(
                {"status": "error", "message": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Handle unexpected exceptions
            return Response(
                {"status": "error", "message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class StudentsDetailAPIView(APIView):
    """
    View to handle fetching, updating, and deleting a specific student.
    """

    def get(self, request, pk=None):
        try:
            student = get_object_or_404(Students, pk=pk)
            enrollments = Enrollment.objects.filter(student=student)
            student_data = StudentsSerializer(student).data
            enrollment_data = EnrollmentSerializer(enrollments, many=True).data
            return Response({"student": student_data, "enrollments": enrollment_data}, status=status.HTTP_200_OK)
        except Students.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

    def put(self, request, pk=None):
        try:
            # Fetch the student object
            student = get_object_or_404(Students, pk=pk)

            # Update the student fields in the Students model using the StudentSerializer
            student_serializer = StudentsSerializer(student, data=request.data, partial=True)
            if student_serializer.is_valid():
                updated_student = student_serializer.save()  # Save the updated student

                # Ensure the student is saved before handling the signals
                updated_student.refresh_from_db()  # Refresh the student instance to fetch updated values

                # Check if the student has an associated user, then update the User model
                if hasattr(updated_student, 'user'):
                    user = updated_student.user
                    user_serializer = UserSerializer(user, data=request.data, partial=True)
                    if user_serializer.is_valid():
                        user_serializer.save()  # Save the updated user
                    else:
                        return Response({
                            "error": "User update failed.",
                            "details": user_serializer.errors
                        }, status=status.HTTP_400_BAD_REQUEST)

                # Handle enrollment updates if any
                if 'enrollments' in request.data:
                    for enrollment_data in request.data['enrollments']:
                        enrollment = Enrollment.objects.filter(student=updated_student, id=enrollment_data.get('id')).first()
                        if enrollment:
                            enrollment_serializer = EnrollmentSerializer(enrollment, data=enrollment_data, partial=True)
                            if enrollment_serializer.is_valid():
                                enrollment_serializer.save()
                            else:
                                return Response({
                                    "error": "Enrollment update failed.",
                                    "details": enrollment_serializer.errors
                                }, status=status.HTTP_400_BAD_REQUEST)
                        else:
                            enrollment_data['student'] = updated_student.id
                            new_enrollment_serializer = EnrollmentSerializer(data=enrollment_data)
                            if new_enrollment_serializer.is_valid():
                                new_enrollment_serializer.save()
                            else:
                                return Response({
                                    "error": "Enrollment creation failed.",
                                    "details": new_enrollment_serializer.errors
                                }, status=status.HTTP_400_BAD_REQUEST)

                return Response({
                    "message": "Student successfully updated.",
                    "data": student_serializer.data
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Student update failed.",
                    "details": student_serializer.errors
                }, status=status.HTTP_400_BAD_REQUEST)

        except Students.DoesNotExist:
            return Response({"error": "Student not found."}, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({"error": f"An unexpected error occurred: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



        
    def delete(self, request, pk=None):
        try:
            with transaction.atomic():
                # Fetch the student instance
                student = get_object_or_404(Students, pk=pk)

                # Check enrollments for the student
                enrollments = Enrollment.objects.filter(student=student)

                if not enrollments.exists():
                    return Response(
                        {"message": "No enrollments found for the student."},
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Iterate through enrollments and update course student count
                for enrollment in enrollments:
                    course = enrollment.courses
                    course.studentsCount -= 1
                    course.save(update_fields=["studentsCount"])

                # Delete enrollments for this student
                enrollments.delete()

                # Check if the student is enrolled in any other course
                if not checkStudentsEnrollment(student):
                    # If a `user` field exists
                    if hasattr(student, "user"):
                        user = student.user
                        user.is_active = False
                        user.save(update_fields=["is_active"])

                    # Delete the student record
                    student.delete()

                return Response(
                    {"message": "Student deleted successfully."},
                    status=status.HTTP_204_NO_CONTENT,
                )
        except Students.DoesNotExist:
            return Response(
                {"message": "Student not found."}, status=status.HTTP_404_NOT_FOUND
            )
        except Exception as e:
            # Catch all other exceptions and provide a structured error message
            return Response(
                {"message": f"An unexpected error occurred: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )



class StudentDashboardAPIView(APIView):
    permission_classes = [IsAuthenticated]  # Ensure only authenticated users can access

    def get(self, request):
        # Get the logged-in user
        user = request.user

        # Check if the user is a student
        if user.role != "student":
            return Response({"message": "Access denied. Only students can view this dashboard."}, status=status.HTTP_403_FORBIDDEN)

        # Get the student instance
        student = get_object_or_404(Students, email=user.email)  # Assuming email is the identifier

        # Get all enrolled courses for the student
        enrollments = Enrollment.objects.filter(student=student)

        if not enrollments.exists():
            return Response({"message": "No enrolled courses found for the student."}, status=status.HTTP_404_NOT_FOUND)

        # Fetch course details along with associated Zoom meeting details
        enrolled_courses_data = []
        for enrollment in enrollments:
            course = enrollment.courses

            # Fetch Zoom meetings for the course
            zoom_meetings = ZoomMeeting.objects.filter(course=course)
            
            course_data = {
                "courseName": course.title,  # Assuming `title` is the course name field
                "meetings": []
            }

            for meeting in zoom_meetings:
                course_data["meetings"].append({
                    "title": meeting.title,
                    "recordingUrl": meeting.recording_url,
                    "duration": meeting.duration,
                    "updatedOn": meeting.updated_at.strftime("%Y-%m-%d %H:%M:%S")  # Format date/time
                })

            enrolled_courses_data.append(course_data)

        return Response({"enrolledCourses": enrolled_courses_data}, status=status.HTTP_200_OK)