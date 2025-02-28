from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.response import Response
from rest_framework import status
from .models import Courses
from .serializers import CourseSerializer
from rest_framework.views import APIView
from .models import Courses 
from users.models import User
from .serializers import CourseSerializer
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.db.models import Q
from students.models import Enrollment
from rest_framework.permissions import IsAuthenticated
from users.permissions import IsModeratorOrInstructor 


class CourseView(APIView):

    permission_classes = [IsAuthenticated, IsModeratorOrInstructor] 

    def get(self, request, pk=None):
        try:
            # Fetch single course
            if pk:
                try:
                    course = Courses.objects.get(pk=pk)
                    serializer = CourseSerializer(course)
                    response_data = {
                        'status': True,
                        'message': f'Course {course.courseName} fetched.',
                        'data': serializer.data,
                        'total': 1,
                        'limit': 1,
                        'page': 1,
                        'pages': 1
                    }
                    return Response(response_data, status=status.HTTP_200_OK)
                except Courses.DoesNotExist:
                    return Response({
                        'status': False,
                        'message': 'Course not found.',
                        'data': [],
                        'total': 0,
                        'limit': 1,
                        'page': 1,
                        'pages': 1
                    }, status=status.HTTP_404_NOT_FOUND)

            # Fetch all courses
            courses = Courses.objects.all()

            # Search by text (course name or instructor name)
            search_text = request.query_params.get('searchText', None)
            if search_text:
                courses = courses.filter(
                    Q(courseName__icontains=search_text) |
                    Q(instructor__firstname__icontains=search_text) |
                    Q(instructor__lastname__icontains=search_text)
                )

            # Search by Instructor ID
            instructor_id = request.query_params.get('instructorId', None)
            if instructor_id:
                courses = courses.filter(instructor_id=instructor_id)

            # Filter by date range
            date_range = request.query_params.get('dateRange', None)
            if date_range:
                try:
                    start_date_str, end_date_str = date_range.split(',')
                    start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d')
                    end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d')
                    end_date = end_date.replace(hour=23, minute=59, second=59)

                    courses = courses.filter(created_at__range=(start_date, end_date))
                except ValueError:
                    return Response(
                        {"status": False, "message": "Invalid date range format. Use 'YYYY-MM-DD,YYYY-MM-DD'."},
                        status=status.HTTP_400_BAD_REQUEST
                    )

            # Pagination
            limit = int(request.query_params.get('limit', 10))
            page_number = int(request.query_params.get('page', 1))

            paginator = Paginator(courses.order_by('-created_at'), limit)
            page_obj = paginator.get_page(page_number)

            serializer = CourseSerializer(page_obj, many=True)

            response_data = {
                'status': paginator.count > 0,
                'message': 'Courses fetched successfully.' if paginator.count > 0 else 'No search data found.',
                'data': serializer.data,
                'total': paginator.count,
                'limit': limit,
                'page': page_number,
                'pages': paginator.num_pages
            }

            return Response(response_data, status=status.HTTP_200_OK if paginator.count > 0 else status.HTTP_404_NOT_FOUND)

        except Exception as e:
            print(f"Error: {str(e)}")
            return Response({
                'status': False,
                'message': f'An unexpected error occurred: {str(e)}',
                'data': [],
                'total': 0,
                'limit': 1,
                'page': 1,
                'pages': 1
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # def get(self, request, pk=None):
    #     try:
    #         # Check for a single course retrieval
    #         if pk: 
    #             try:
    #                 course = Courses.objects.get(pk=pk)
    #                 serializer = CourseSerializer(course , many=True)
    #                 response_data = {
    #                     'status': True,
    #                     'message': f'Course {course.courseName} fetched.',
    #                     'data': serializer.data,
    #                     'total': 1,
    #                     'limit': 1,
    #                     'page': 1,
    #                     'pages': 1
    #                 }
    #                 return Response(response_data, status=status.HTTP_200_OK)
    #             except Courses.DoesNotExist:
    #                 return Response({
    #                     'status': False,
    #                     'message': 'Course not found.',
    #                     'data': [],
    #                     'total': 0,
    #                     'limit': 1,
    #                     'page': 1,
    #                     'pages': 1
    #                 }, status=status.HTTP_404_NOT_FOUND)

    #         # Listing and filtering courses
    #         courses = Courses.objects.all()

    #         search_text = request.query_params.get('searchText', None)
    #         if search_text:
    #             courses = courses.filter(
    #                 Q(courseName__icontains=search_text) |
    #                 Q(instructorName__icontains=search_text) |
    #                 Q(created_at__date__icontains=search_text) |  # Search by date part of created_at
    #                 Q(updated_at__date__icontains=search_text)   # Search by date part of updated_at
    #             )

    #         search_instructor = request.query_params.get('searchInstructor', None)
    #         if search_instructor:
    #             courses = courses.filter(instructorName__icontains=search_instructor)

    #         date_range = request.query_params.get('dateRange', None)
    #         if date_range:
    #             try:
    #                 start_date_str, end_date_str = date_range.split(',')
    #                 start_date = datetime.strptime(start_date_str.strip(), '%Y-%m-%d')
    #                 end_date = datetime.strptime(end_date_str.strip(), '%Y-%m-%d')
    #                 end_date = end_date.replace(hour=23, minute=59, second=59)

    #                 courses = courses.filter(created_at__range=(start_date, end_date))
    #             except ValueError:
    #                 return Response(
    #                     {"status": False, "message": "Invalid date range format. Use 'YYYY-MM-DD,YYYY-MM-DD'."},
    #                     status=status.HTTP_400_BAD_REQUEST
    #                 )

    #         # Pagination
    #         limit = int(request.query_params.get('limit', 10))
    #         page_number = int(request.query_params.get('page', 1))
            
    #         paginator = Paginator(courses.order_by('id'), limit)  # Use filtered courses queryset
    #         page_obj = paginator.get_page(page_number)

    #         serializer = CourseSerializer(page_obj, many=True)

    #         response_data = {
    #             'status': True if paginator.count > 0 else False,
    #             'message': 'Courses fetched successfully.' if paginator.count > 0 else 'No Search data found.',
    #             'data': serializer.data,
    #             'total': paginator.count,
    #             'limit': limit,
    #             'page': page_number,
    #             'pages': paginator.num_pages
    #         }

    #         return Response(response_data, status=status.HTTP_200_OK if paginator.count > 0 else status.HTTP_404_NOT_FOUND)

    #     except Exception as e:
    #         print(f"Error: {str(e)}")
    #         return Response({
    #             'status': False,
    #             'message': f'An unexpected error occurred: {str(e)}',
    #             'data': [],
    #             'total': 0,
    #             'limit': 1,
    #             'page': 1,
    #             'pages': 1
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    
    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': True,
                'message': 'Course created successfully.',
                'data': serializer.data
            }, status=status.HTTP_201_CREATED)
        return Response({
            'status': False,
            'message': 'Course creation failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request, pk=None):
        try:
            course = Courses.objects.get(pk=pk)
        except Courses.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Course not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        serializer = CourseSerializer(course, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'status': True,
                'message': 'Course updated successfully.',
                'data': serializer.data
            }, status=status.HTTP_200_OK)
        return Response({
            'status': False,
            'message': 'Course update failed.',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)


    def delete(self, request, pk=None):
        try:
            course = Courses.objects.get(pk=pk)
            
            # Check if any students are enrolled in this course
            if Enrollment.objects.filter(courses=course).exists():
                return Response({
                    "status": False,
                    "message": "Students are enrolled in this course. Cannot delete the course."
                }, status=status.HTTP_400_BAD_REQUEST)

            course.delete()
            return Response({
                "status": True,
                "message": "Course deleted successfully."
            }, status=status.HTTP_200_OK)  # Ensure 200 OK is returned

        except Courses.DoesNotExist:
            return Response({
                "status": False,
                "message": "Course not found."
            }, status=status.HTTP_404_NOT_FOUND)

        except Exception as e:
            return Response({
                "status": False,
                "message": f"An unexpected error occurred: {str(e)}"
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)





from django.http import JsonResponse
from users.models import Instructor
# from students.models import Students

class CourseDropdownListView(APIView):

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # user = request.user  # Get the authenticated user

        # if user.role.name.lower() == "student":  # Normalize role check (case-insensitive)
        #     try:
        #         student = Students.objects.get(email=user.email)  # Fetch the student instance
        #         enrolled_courses = Courses.objects.filter(enrollment__student=student).distinct()
        #     except Students.DoesNotExist:
        #         return JsonResponse({"error": "Student record not found"}, status=404)
        # else:
        enrolled_courses = Courses.objects.all()  # For other roles, return all courses

        data = [{"id": course.id, "title": course.courseName} for course in enrolled_courses]
        return JsonResponse(data, safe=False)
        
    
class InstructorListView(APIView):

    permission_classes = [IsAuthenticated, IsModeratorOrInstructor] 
    
    def get(self, request):
        # Fetch all instructors
        instructors = Instructor.objects.all()
        data = [{"id": instructor.id, "name": f"{instructor.firstname} {instructor.lastname}"} for instructor in instructors]
        return JsonResponse(list(data), safe=False)
