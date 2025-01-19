from django.db import IntegrityError, transaction
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from users.decorators import role_required
from .models import Students, Enrollment, Courses
from users.models import CustomUser
from rest_framework.decorators import api_view
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@role_required(roles=['moderator'])
@api_view(['POST'])
def create_student(request):
    try:
        # Start the transaction block
        with transaction.atomic():
            user_data = request.data.get('user')
            dob = request.data.get('dob')
            address = request.data.get('address')
            batch = request.data.get('batch')
            course_ids = request.data.get('courses')  # List of course IDs

            if not user_data:
                return JsonResponse({'error': 'User data is required'}, status=400)

            # Check if the user already exists by username or phone
            if CustomUser.objects.filter(username=user_data['username']).exists():
                return JsonResponse({'error': 'Username already exists'}, status=400)
            if CustomUser.objects.filter(phone=user_data['phone']).exists():
                return JsonResponse({'error': 'Phone number already exists'}, status=400)

            # Create the CustomUser object
            user = CustomUser.objects.create_user(
                username=user_data['username'],
                email=user_data['email'],
                password=user_data['password'],
                phone=user_data['phone'],
                role='student'  # Role will be set as 'student'
            )

            # Create the Student profile
            student = Students.objects.create(
                user=user,
                dob=dob,
                address=address,
                batch=batch
            )

            # Ensure all courses exist before enrolling the student
            for course_id in course_ids:
                try:
                    course = get_object_or_404(Courses, id=course_id)
                    Enrollment.objects.create(student=student, course=course, date_of_joining=request.data.get('date_of_joining'), expiry_date=request.data.get('expiry_date'))
                except Exception as e:
                    # Rollback the transaction if any course is not found or another error occurs
                    raise IntegrityError(f"Course with ID {course_id} not found or error occurred: {str(e)}")

            # If everything is fine, commit the transaction
            return JsonResponse({'message': 'Student created successfully', 'student_id': student.id}, status=201)

    except IntegrityError as e:
        # Rollback any changes if an error occurred
        return JsonResponse({'error': f'Error during student creation: {str(e)}'}, status=400)
    except Exception as e:
        # Catch other exceptions and rollback
        return JsonResponse({'error': f'An error occurred: {str(e)}'}, status=500)


@csrf_exempt
@role_required(roles=['moderator'])
@api_view(['GET'])
def get_student(request, student_id):
    try:
        student = get_object_or_404(Students, id=student_id)
        student_data = {
            'user': student.user.username,
            'dob': student.dob,
            'address': student.address,
            'batch': student.batch,
            'courses': [course.title for course in student.courses.all()],
            'status': student.status,
        }
        return JsonResponse(student_data, status=200)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@csrf_exempt
@role_required(roles=['moderator'])
@api_view(['PUT'])
def update_student(request, student_id):
    try:
        student = get_object_or_404(Students, id=student_id)

        # Update student profile
        student.dob = request.data.get('dob', student.dob)
        student.address = request.data.get('address', student.address)
        student.batch = request.data.get('batch', student.batch)
        student.status = request.data.get('status', student.status)
        student.save()

        # Update courses (we will just remove old courses and add new ones)
        course_ids = request.data.get('courses', [])
        student.courses.clear()  # Remove all previous courses
        for course_id in course_ids:
            course = get_object_or_404(Courses, id=course_id)
            Enrollment.objects.create(student=student, course=course, date_of_joining=request.data.get('date_of_joining'), expiry_date=request.data.get('expiry_date'))

        return JsonResponse({'message': 'Student updated successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@role_required(roles=['moderator'])
@api_view(['DELETE'])
def delete_student(request, student_id):
    try:
        student = get_object_or_404(Students, id=student_id)
        
        # Delete related enrollments
        Enrollment.objects.filter(student=student).delete()

        # Delete the student profile
        student.user.delete()  # Deletes both the Student and associated CustomUser
        student.delete()

        return JsonResponse({'message': 'Student deleted successfully'}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

@csrf_exempt
@role_required(roles=['moderator'])
@api_view(['GET'])
def list_students(request):
    try:
        students = Students.objects.all()
        students_data = [
            {
                'user': student.user.username,
                'dob': student.dob,
                'address': student.address,
                'batch': student.batch,
                'status': student.status,
            }
            for student in students
        ]
        return JsonResponse({'students': students_data}, status=200)

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from django.core.exceptions import ObjectDoesNotExist
# from .models import Students , Enrollment
# from courses.models import Courses
# from datetime import datetime

# # Create Student
# @api_view(['POST'])
# def create_student(request):
#     # Extracting data from the request body
#     firstname = request.data.get('firstname')
#     lastname = request.data.get('lastname')
#     email = request.data.get('email')
#     phone = request.data.get('phone')
#     dob = request.data.get('dob')
#     address = request.data.get('address')
#     course_ids = request.data.get('course_ids')  # course_ids is expected to be a list
#     date_of_joining = request.data.get('date_of_joining')

#     # Check if the required fields are present
#     if not all([firstname, lastname, email, phone, dob, address, course_ids, date_of_joining]):
#         return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

#     # Try to fetch courses based on the provided course_ids
#     try:
#         courses = Courses.objects.filter(id__in=course_ids)
#         if not courses:
#             return Response({"error": "No courses found with the given IDs."}, status=status.HTTP_400_BAD_REQUEST)
#     except Courses.DoesNotExist:
#         return Response({"error": "Invalid course IDs."}, status=status.HTTP_400_BAD_REQUEST)

#     # Create the Student instance
#     student = Students.objects.create(
#         firstname=firstname,
#         lastname=lastname,
#         email=email,
#         phone=phone,
#         dob=dob,
#         address=address,
#     )

#     # Assign courses and create enrollment records
#     for course in courses:
#         Enrollment.objects.create(
#             student=student,
#             course=course,
#             date_of_joining=datetime.strptime(date_of_joining, '%Y-%m-%d'),
#             expiry_date=datetime.strptime(request.data.get('expiry_date'), '%Y-%m-%d')
#         )

#     # Return the created student data along with status and message
#     student_data = {
#         "id": student.id,
#         "firstname": student.firstname,
#         "lastname": student.lastname,
#         "email": student.email,
#         "phone": student.phone,
#         "dob": student.dob,
#         "address": student.address,
#         "courses": [course.title for course in courses],
#     }

#     return Response({
#         "status": "success",
#         "message": "Student created successfully",
#         "data": student_data
#     }, status=status.HTTP_201_CREATED)


# # List Students
# @api_view(['GET'])
# def list_students(request):
#     students = Students.objects.all()
#     student_data = [
#         {
#             "id": student.id,
#             "firstname": student.firstname,
#             "lastname": student.lastname,
#             "email": student.email,
#             "phone": student.phone,
#             "dob": student.dob,
#             "address": student.address,
#             "courses": [enrollment.course.title for enrollment in student.enrollment_set.all()],
#         }
#         for student in students
#     ]
#     return Response({
#         "status": "success",
#         "message": "Students fetched successfully",
#         "data": student_data
#     }, status=status.HTTP_200_OK)


# # Get a Single Student
# # @api_view(['GET'])
# # def get_student(request, student_id):
# #     try:
# #         student = Student.objects.get(id=student_id)
# #         student_data = {
# #             "id": student.id,
# #             "firstname": student.firstname,
# #             "lastname": student.lastname,
# #             "email": student.email,
# #             "phone": student.phone,
# #             "dob": student.dob,
# #             "address": student.address,
# #             "courses": [enrollment.course.title for enrollment in student.enrollment_set.all()],
# #         }
# #         return Response({
# #             "status": "success",
# #             "message": "Student fetched successfully",
# #             "data": student_data
# #         }, status=status.HTTP_200_OK)
# #     except Student.DoesNotExist:
# #         return Response({
# #             "status": "error",
# #             "message": "Student not found"
# #         }, status=status.HTTP_404_NOT_FOUND)

# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from django.db.models import Q
# from .models import Students

# @api_view(['GET'])
# def get_or_search_students(request):
#     student_id = request.query_params.get('student_id')
#     if student_id:
#         try:
#             student = Students.objects.get(id=student_id)
#             student_data = {
#                 "id": student.id,
#                 "firstname": student.firstname,
#                 "lastname": student.lastname,
#                 "email": student.email,
#                 "phone": student.phone,
#                 "dob": student.DOB,
#                 "address": student.address,
#                 "courses": [course.title for course in student.courses.all()],
#                 "is_active": student.is_active,
#             }
#             return Response({
#                 "status": "success",
#                 "message": "Student fetched successfully",
#                 "data": student_data
#             }, status=status.HTTP_200_OK)
#         except Students.DoesNotExist:
#             return Response({
#                 "status": "error",
#                 "message": "Student not found"
#             }, status=status.HTTP_404_NOT_FOUND)

#     studentname = request.query_params.get('studentname')
#     course_title = request.query_params.get('course')
#     status_filter = request.query_params.get('status')

#     filters = Q()
#     if studentname:
#         filters &= Q(firstname__icontains=studentname) | Q(lastname__icontains=studentname)
#     if course_title:
#         filters &= Q(courses__title__icontains=course_title)
#     if status_filter:
#         filters &= Q(is_active=(status_filter.lower() == 'active'))

#     students = Students.objects.filter(filters).distinct()

#     student_list = []
#     for student in students:
#         student_list.append({
#             "id": student.id,
#             "firstname": student.firstname,
#             "lastname": student.lastname,
#             "email": student.email,
#             "phone": student.phone,
#             "dob": student.DOB,
#             "address": student.address,
#             "courses": [course.title for course in student.courses.all()],
#             "is_active": student.is_active,
#         })

#     return Response({
#         "status": "success",
#         "message": "Students fetched successfully",
#         "data": student_list
#     }, status=status.HTTP_200_OK)


# # Update Student
# @api_view(['PUT'])
# def update_student(request, student_id):
#     try:
#         student = Students.objects.get(id=student_id)
#     except Students.DoesNotExist:
#         return Response({
#             "status": "error",
#             "message": "Student not found"
#         }, status=status.HTTP_404_NOT_FOUND)

#     # Update student fields
#     student.firstname = request.data.get('firstname', student.firstname)
#     student.lastname = request.data.get('lastname', student.lastname)
#     student.email = request.data.get('email', student.email)
#     student.phone = request.data.get('phone', student.phone)
#     student.dob = request.data.get('dob', student.dob)
#     student.address = request.data.get('address', student.address)
    
#     # Update courses if provided
#     course_ids = request.data.get('course_ids')
#     if course_ids:
#         courses = Courses.objects.filter(id__in=course_ids)
#         if not courses:
#             return Response({
#                 "status": "error",
#                 "message": "Invalid course IDs"
#             }, status=status.HTTP_400_BAD_REQUEST)
#         # Delete existing enrollments and add new ones
#         student.enrollment_set.all().delete()
#         for course in courses:
#             Enrollment.objects.create(
#                 student=student,
#                 course=course,
#                 date_of_joining=datetime.strptime(request.data.get('date_of_joining', ''), '%Y-%m-%d'),
#                 expiry_date=datetime.strptime(request.data.get('expiry_date', ''), '%Y-%m-%d')
#             )
    
#     student.save()
#     return Response({
#         "status": "success",
#         "message": "Student updated successfully"
#     }, status=status.HTTP_200_OK)


# # Delete Student
# @api_view(['DELETE'])
# def delete_student(request, student_id):
#     try:
#         student = Students.objects.get(id=student_id)
#         student.delete()
#         return Response({
#             "status": "success",
#             "message": "Student deleted successfully"
#         }, status=status.HTTP_204_NO_CONTENT)
#     except Students.DoesNotExist:
#         return Response({
#             "status": "error",
#             "message": "Student not found"
#         }, status=status.HTTP_404_NOT_FOUND)

# from django.db.models import Q
# from rest_framework.decorators import api_view
# from rest_framework.response import Response
# from rest_framework import status
# from students.models import Students

# @api_view(['GET'])
# def search(request):
#     # Extract query parameters
#     name = request.query_params.get("name", None)
#     email = request.query_params.get("email", None)
#     phone = request.query_params.get("phone", None)
#     course_title = request.query_params.get("course", None)
#     enrollment_date = request.query_params.get("enrollment_date", None)  # Format: YYYY-MM-DD
#     status_param = request.query_params.get("status", None)

#     try:
#         # Build the query dynamically
#         query = Q()
#         if name:
#             query &= Q(firstname__icontains=name) | Q(lastname__icontains=name)
#         if email:
#             query &= Q(email__icontains=email)
#         if phone:
#             query &= Q(phone__icontains=phone)
#         if course_title:
#             query &= Q(courses__title__icontains=course_title)  # Assuming Many-to-Many relationship
#         if enrollment_date:
#             query &= Q(studentcourse__date_of_joining=enrollment_date)  # Adjust if field differs
#         if status_param:
#             query &= Q(is_active=(status_param.lower() == "active"))

#         # Fetch filtered students
#         students = Students.objects.filter(query).distinct()

#         # Build response data
#         student_data = []
#         for student in students:
#             courses = [
#                 {
#                     "title": course.title,
#                     "description": course.description,
#                     "instructor_name": course.instructor_name,
#                     # "enrollment_date": course,enrollment_date,
#                     "phone": course.phone,
#                     "dob": course.dob,
#                 }
#                 for course in student.courses.all()  # Assuming Many-to-Many relationship
#             ]

#             student_data.append({
#                 "firstname": student.firstname,
#                 "lastname": student.lastname,
#                 "email": student.email,
#                 "phone": student.phone,
#                 "DOB": student.dob,
#                 "address": student.address,
#                 "courses": courses,
#                 "is_active": student.is_active,
#                 "created_on": student.created_on,
#                 "last_updated_on": student.last_updated_on,
#             })

#         # Return success response
#         return Response({
#             "status": "success",
#             "data": student_data
#         }, status=status.HTTP_200_OK)

#     except Exception as e:
#         # Return error response in case of failure
#         return Response({
#             "status": "error",
#             "message": "An error occurred while processing your request",
#             "details": str(e)
#         }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
