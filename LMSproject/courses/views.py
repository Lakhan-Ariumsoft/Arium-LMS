from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from rest_framework.response import Response
from rest_framework import status
from .models import Courses
from .serializers import CourseSerializer
from rest_framework.views import APIView
from .models import Courses
from .serializers import CourseSerializer
from rest_framework.response import Response
from rest_framework import status
from datetime import datetime
from django.db.models import Q


def getPaginatedCourses(request, courses_queryset):
    """
    Handles pagination for the courses data and returns the paginated response.
    Adds filtering based on searchText, searchInstructor, and dateRange query params.

    Args:
        request: The HTTP request object containing query parameters.
        courses_queryset: Queryset of course objects to be paginated.

    Returns:
        Response: A formatted response with paginated course data.
    """
    try:
        # Default limit and page if not provided in the query params
        limit = int(request.query_params.get('limit', 10))
        page = int(request.query_params.get('page', 1))

        # Filter by searchText (search in courseName, instructorName, created_at, and updated_at)
        search_text = request.query_params.get('searchText', None)
        if search_text:
            courses_queryset = courses_queryset.filter(
                Q(courseName__icontains=search_text) | 
                Q(instructorName__icontains=search_text) |
                Q(created_at__icontains=search_text) |  # This might be better as an exact match or range
                Q(updated_at__icontains=search_text)
            )

        # Filter by searchInstructor (search in instructorName)
        search_instructor = request.query_params.get('searchInstructor', None)
        if search_instructor:
            courses_queryset = courses_queryset.filter(instructorName__icontains=search_instructor)

        # Filter by dateRange (search within a date range)
        date_range = request.query_params.get('dateRange', None)
        if date_range:
            try:
                # Split the date range into start and end dates
                start_date_str, end_date_str = date_range.split(',')
                
                # Parse the dates as datetime objects (you can remove time if you only want to compare dates)
                start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
                end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

                # Set the time for the end date to 23:59:59 to include the entire day
                end_date = end_date.replace(hour=23, minute=59, second=59)

                # Apply the date range filter on created_at
                courses_queryset = courses_queryset.filter(created_at__range=[start_date, end_date])

            except ValueError:
                return Response(
                    {"status": False, "message": "Invalid date range format. Use 'YYYY-MM-DD,YYYY-MM-DD'."},
                    status=status.HTTP_400_BAD_REQUEST
                )

        # Pagination
        paginator = Paginator(courses_queryset, limit)

        try:
            # Get the requested page
            paginated_courses = paginator.get_page(page)
        except PageNotAnInteger:
            # If the page is not an integer, return the first page
            paginated_courses = paginator.page(1)
        except EmptyPage:
            # If the page is out of range, return an empty result
            paginated_courses = []

        # Prepare course data
        course_data = []
        for course in paginated_courses:
            course_data.append({
                "id": course.id,
                "courseName": course.courseName,
                "instructorName": course.instructorName,
                "studentsCount": course.studentsCount,
                "videosCount": course.videosCount,
                "created_at": course.created_at.isoformat(),
                "updated_at": course.updated_at.isoformat(),
            })

        # If no courses found, return a specific message
        if not course_data:
            return Response({
                "status": True,
                "message": "No courses found.",
                "data": [],
                "total": 0,
                "limit": limit,
                "page": page,
                "pages": 0,
            }, status=status.HTTP_200_OK)

        # Return paginated response
        response = {
            "status": True,
            "message": "Courses fetched successfully.",
            "data": course_data,
            "total": paginator.count,
            "limit": limit,
            "page": paginated_courses.number,
            "pages": paginator.num_pages,
        }

        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {"status": False, "message": f"An unexpected error occurred: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

class CourseView(APIView):

    def get(self, request, pk=None):
        if pk:  # If pk is provided, it's for a single course
            try:
                course = Courses.objects.get(pk=pk)
                serializer = CourseSerializer(course)
                return Response({
                    'status': True,
                    'message': f'Course {course.courseName} fetched.',
                    'data': serializer.data
                }, status=status.HTTP_200_OK)
            except Courses.DoesNotExist:
                return Response({
                    'status': False,
                    'message': 'Course not found.',
                }, status=status.HTTP_404_NOT_FOUND)
        
        # For listing courses with pagination
        courses = Courses.objects.all()
        return getPaginatedCourses(request, courses)
    
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
        except Courses.DoesNotExist:
            return Response({
                'status': False,
                'message': 'Course not found.',
            }, status=status.HTTP_404_NOT_FOUND)

        course.delete()
        return Response({
            'status': True,
            'message': 'Course deleted successfully.'
        }, status=status.HTTP_204_NO_CONTENT)
