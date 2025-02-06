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
from users.permissions import IsModerator



# def getPaginatedCourses(request, courses_queryset):
#     """
#     Handles pagination for the courses data and returns the paginated response.
#     Adds filtering based on searchText, searchInstructor, and dateRange query params.

#     Args:
#         request: The HTTP request object containing query parameters.
#         courses_queryset: Queryset of course objects to be paginated.

#     Returns:
#         Response: A formatted response with paginated course data.
#     """
#     try:
#         # Default limit and page if not provided in the query params
#         limit = int(request.query_params.get('limit', 10))
#         page = int(request.query_params.get('page', 1))

#         # Filter by searchText (search in courseName, instructorName, created_at, and updated_at)
#         search_text = request.query_params.get('searchText', None)
#         if search_text:
#             courses_queryset = courses_queryset.filter(
#                 Q(courseName__icontains=search_text) | 
#                 Q(instructorName__icontains=search_text) |
#                 Q(created_at__icontains=search_text) |  # This might be better as an exact match or range
#                 Q(updated_at__icontains=search_text)
#             )

#         # Filter by searchInstructor (search in instructorName)
#         search_instructor = request.query_params.get('searchInstructor', None)
#         if search_instructor:
#             courses_queryset = courses_queryset.filter(instructorName__icontains=search_instructor)

#         # Filter by dateRange (search within a date range)
#         date_range = request.query_params.get('dateRange', None)
#         if date_range:
#             try:
#                 # Split the date range into start and end dates
#                 start_date_str, end_date_str = date_range.split(',')
                
#                 # Parse the dates as datetime objects (you can remove time if you only want to compare dates)
#                 start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
#                 end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

#                 # Set the time for the end date to 23:59:59 to include the entire day
#                 end_date = end_date.replace(hour=23, minute=59, second=59)

#                 # Apply the date range filter on created_at
#                 courses_queryset = courses_queryset.filter(created_at__range=[start_date, end_date])

#             except ValueError:
#                 return Response(
#                     {"status": False, "message": "Invalid date range format. Use 'YYYY-MM-DD,YYYY-MM-DD'."},
#                     status=status.HTTP_400_BAD_REQUEST
#                 )

#         # Pagination
#         paginator = Paginator(courses_queryset, limit)

#         try:
#             # Get the requested page
#             paginated_courses = paginator.get_page(page)
#         except PageNotAnInteger:
#             # If the page is not an integer, return the first page
#             paginated_courses = paginator.page(1)
#         except EmptyPage:
#             # If the page is out of range, return an empty result
#             paginated_courses = []

#         # Prepare course data
#         course_data = []
#         for course in paginated_courses:
#             course_data.append({
#                 "id": course.id,
#                 "courseName": course.courseName,
#                 "instructorName": course.instructorName,
#                 "studentsCount": course.studentsCount,
#                 "videosCount": course.videosCount,
#                 "created_at": course.created_at.isoformat(),
#                 "updated_at": course.updated_at.isoformat(),
#             })

#         # If no courses found, return a specific message
#         if not course_data:
#             return Response({
#                 "status": True,
#                 "message": "No courses found.",
#                 "data": [],
#                 "total": 0,
#                 "limit": limit,
#                 "page": page,
#                 "pages": 0,
#             }, status=status.HTTP_200_OK)

#         # Return paginated response
#         response = {
#             "status": True,
#             "message": "Courses fetched successfully.",
#             "data": course_data,
#             "total": paginator.count,
#             "limit": limit,
#             "page": paginated_courses.number,
#             "pages": paginator.num_pages,
#         }

#         return Response(response, status=status.HTTP_200_OK)

#     except Exception as e:
#         return Response(
#             {"status": False, "message": f"An unexpected error occurred: {str(e)}"},
#             status=status.HTTP_500_INTERNAL_SERVER_ERROR
#         )

class CourseView(APIView):

    permission_classes = [IsAuthenticated, IsModerator] 

    def get(self, request, pk=None):
        try:
            # Check for a single course retrieval
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

            # Listing and filtering courses
            courses = Courses.objects.all()

            search_text = request.query_params.get('searchText', None)
            if search_text:
                courses = courses.filter(
                    Q(courseName__icontains=search_text) |
                    Q(instructorName__icontains=search_text) |
                    Q(created_at__date__icontains=search_text) |  # Search by date part of created_at
                    Q(updated_at__date__icontains=search_text)   # Search by date part of updated_at
                )

            search_instructor = request.query_params.get('searchInstructor', None)
            if search_instructor:
                courses = courses.filter(instructorName__icontains=search_instructor)

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
            
            paginator = Paginator(courses.order_by('id'), limit)  # Use filtered courses queryset
            page_obj = paginator.get_page(page_number)

            serializer = CourseSerializer(page_obj, many=True)

            response_data = {
                'status': True if paginator.count > 0 else False,
                'message': 'Courses fetched successfully.' if paginator.count > 0 else 'No Search data found.',
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
    #         # print("sssss",request.user.role , type(request.user.role))
    #         # if not request.user.role or request.user.role.name != "moderator":
    #         #     return JsonResponse({"error": "Permission denied"}, status=403)
    #         # if request.user.role != "moderator":
    #         #     return JsonResponse({"error": "Permission denied"}, status=403)


    #         if pk:  # If pk is provided, fetch a single course
    #             try:
    #                 course = Courses.objects.get(pk=pk)
    #                 serializer = CourseSerializer(course)
    #                 response_data = {
    #                     'status': True,
    #                     'message': f'Course {course.courseName} fetched.',
    #                     'data': serializer.data,
    #                     'total': 1,  # Since it's a single course
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

    #         # For listing courses with pagination and filtering
    #         courses = Courses.objects.all()

    #         # Apply filtering logic based on query parameters
    #         search_text = request.query_params.get('searchText', None)
    #         if search_text:
    #             courses = courses.filter(
    #                 Q(courseName__icontains=search_text) |
    #                 Q(instructorName__icontains=search_text) |
    #                 Q(created_at__icontains=search_text) |
    #                 Q(updated_at__icontains=search_text)
    #             )

    #         search_instructor = request.query_params.get('searchInstructor', None)
    #         if search_instructor:
    #             courses = courses.filter(instructorName__icontains=search_instructor)

    #         date_range = request.query_params.get('dateRange', None)
    #         if date_range:
    #             try:
    #                 # Split the date range into start and end dates
    #                 start_date_str, end_date_str = date_range.split(',')
                    
    #                 # Parse the dates as datetime objects
    #                 start_date = datetime.strptime(start_date_str, '%Y-%m-%d')
    #                 end_date = datetime.strptime(end_date_str, '%Y-%m-%d')

    #                 # Set the time for the end date to 23:59:59
    #                 end_date = end_date.replace(hour=23, minute=59, second=59)

    #                 # Apply the date range filter on created_at
    #                 courses = courses.filter(created_at__range=[start_date, end_date])

    #             except ValueError:
    #                 return Response(
    #                     {"status": False, "message": "Invalid date range format. Use 'YYYY-MM-DD,YYYY-MM-DD'."},
    #                     status=status.HTTP_400_BAD_REQUEST
    #                 )

    #         # Pagination logic
    #         limit = int(request.query_params.get('limit', 10))
    #         page_number = request.query_params.get('page', 1)
    #         courses = Courses.objects.all().order_by('id') 
    #         paginator = Paginator(courses, limit)
    #         page_obj = paginator.get_page(page_number)

    #         # Serialize the paginated courses
    #         serializer = CourseSerializer(page_obj, many=True)

    #         response_data = {
    #             'status': True if page_obj.paginator.count > 0 else False,
    #             'message': 'Courses fetched successfully.' if page_obj.paginator.count > 0 else 'No Search data found.',
    #             'data': serializer.data,  # Use serialized data here
    #             'total': page_obj.paginator.count,
    #             'limit': limit,  # You can also pass this dynamically
    #             'page': page_number,
    #             'pages': page_obj.paginator.num_pages
    #         }

    #         return Response(response_data, status=status.HTTP_200_OK if page_obj.paginator.count > 0 else status.HTTP_404_NOT_FOUND)

    #     except Exception as e:
    #         print(f"Error: {str(e)}")  # Optionally log the error for debugging purposes
    #         return Response({
    #             'status': False,
    #             'message': f'An unexpected error occurred: {str(e)}',
    #             'data': [],
    #             'total': 0,
    #             'limit': 1,
    #             'page': 1,
    #             'pages': 1
    #         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


    # def get(self, request, pk=None):
    #     if pk:  # If pk is provided, it's for a single course
    #         try:
    #             course = Courses.objects.get(pk=pk)
    #             serializer = CourseSerializer(course)
    #             return Response({
    #                 'status': True,
    #                 'message': f'Course {course.courseName} fetched.',
    #                 'data': serializer.data
    #             }, status=status.HTTP_200_OK)
    #         except Courses.DoesNotExist:
    #             return Response({
    #                 'status': False,
    #                 'message': 'Course not found.',
    #             }, status=status.HTTP_404_NOT_FOUND)
        
    #     # For listing courses with pagination
    #     courses = Courses.objects.all()
    #     return getPaginatedCourses(request, courses)
    
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

class CourseDropdownListView(APIView):

    permission_classes = [IsAuthenticated, IsModerator] 

    def get(self, request):
        # Fetch all courses and their ids
        courses = Courses.objects.all()
        data = [{"id": course.id, "title": course.courseName} for course in courses]
        return JsonResponse(data, safe=False)
        
    
class InstructorListView(APIView):

    permission_classes = [IsAuthenticated, IsModerator] 

    def get(self, request):
        # Fetch instructors from Courses model
        instructors = Courses.objects.all()
        data = [{"instructor": course.instructorName} for course in instructors]
        return JsonResponse(data, safe=False)
