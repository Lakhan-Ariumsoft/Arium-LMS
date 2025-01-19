from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Courses
from rest_framework.exceptions import NotFound, ValidationError

class CourseView(APIView):
    def get(self, request):
        try:
            # Get all courses
            courses = Courses.objects.all()
            data = [{
                "id": course.id,
                "title": course.title,
                "description": course.description,
                "instructor_name": course.instructor_name,
                "phone": course.phone,
                "dob": course.dob,
                "start_date": course.start_date,
                "end_date": course.end_date,
                "created_at": course.created_at,
                "updated_at": course.updated_at
            } for course in courses]
            return Response(data, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"error": "Error retrieving courses", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def post(self, request):
        data = request.data
        try:
            # Validate required fields
            required_fields = ['title', 'description', 'instructor_name', 'phone', 'dob', 'start_date', 'end_date']
            for field in required_fields:
                if field not in data:
                    raise ValidationError(f"'{field}' is required")

            # Create a new course
            course = Courses.objects.create(
                title=data['title'],
                description=data['description'],
                instructor_name=data['instructor_name'],
                phone=data['phone'],
                dob=data['dob'],
                start_date=data['start_date'],
                end_date=data['end_date']
            )
            return Response({
                "message": "Course created successfully",
                "course_id": course.id
            }, status=status.HTTP_201_CREATED)
        except ValidationError as ve:
            return Response({"error": str(ve)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": "Error creating course", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def put(self, request, pk):
        data = request.data
        try:
            # Get the course to update
            course = Courses.objects.get(id=pk)
            # Update fields
            course.title = data.get('title', course.title)
            course.description = data.get('description', course.description)
            course.instructor_name = data.get('instructor_name', course.instructor_name)
            course.phone = data.get('phone', course.phone)
            course.dob = data.get('dob', course.dob)
            course.start_date = data.get('start_date', course.start_date)
            course.end_date = data.get('end_date', course.end_date)
            course.save()
            return Response({"message": "Course updated successfully"}, status=status.HTTP_200_OK)
        except Courses.DoesNotExist:
            raise NotFound(detail="Course not found")
        except Exception as e:
            return Response({"error": "Error updating course", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def delete(self, request, pk):
        try:
            # Delete the course
            course = Courses.objects.get(id=pk)
            course.delete()
            return Response({"message": "Course deleted successfully"}, status=status.HTTP_204_NO_CONTENT)
        except Courses.DoesNotExist:
            raise NotFound(detail="Course not found")
        except Exception as e:
            return Response({"error": "Error deleting course", "details": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
