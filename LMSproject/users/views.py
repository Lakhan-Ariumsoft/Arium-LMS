from django.http import JsonResponse
from django.views import View
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from .models import Profile, Role
import json


@method_decorator(login_required, name='dispatch')
class StudentView(View):
    def has_permission(self, Profile, action):
        """
        Check permissions based on the Profile's role.
        - Moderator: Full permissions.
        - Instructor: Add your logic if needed.
        - Student: Read-only permissions.
        """
        role_title = Profile.role.role_title  # Access role title
        if role_title == "moderator":
            return True  # Full access
        if role_title == "instructor" and action in ["read", "update"]:
            return True  # Add custom instructor logic if needed
        if role_title == "student" and action == "read":
            return True  # Read-only for students
        return False

    def get(self, request, student_id=None):
        """
        GET: Retrieve student(s).
        - Students: Can only read.
        - Moderators/Instructors: Can access all data.
        """
        if not self.has_permission(request.Profile, "read"):
            return JsonResponse({"error": "Access Denied"}, status=403)

        if student_id:
            try:
                student = Profile.objects.get(id=student_id, role__role_title="student")
                data = {
                    "id": student.id,
                    "firstname": student.firstname,
                    "lastname": student.lastname,
                    "email": student.email,
                    "phone": student.phone,
                    "dob": student.dob,
                    "address": student.address,
                    "is_active": student.is_active,
                }
                return JsonResponse(data, safe=False)
            except Profile.DoesNotExist:
                return JsonResponse({"error": "Student not found"}, status=404)
        else:
            students = Profile.objects.filter(role__role_title="student")
            data = [
                {
                    "id": student.id,
                    "firstname": student.firstname,
                    "lastname": student.lastname,
                    "email": student.email,
                    "phone": student.phone,
                    "dob": student.dob,
                    "address": student.address,
                    "is_active": student.is_active,
                }
                for student in students
            ]
            return JsonResponse(data, safe=False)

    def post(self, request):
        """
        POST: Create a new student.
        - Only Moderators can create students.
        """
        if not self.has_permission(request.Profile, "create"):
            return JsonResponse({"error": "Access Denied"}, status=403)

        try:
            data = json.loads(request.body)
            role = Role.objects.get(role_title="student")  # Assign 'student' role
            student = Profile.objects.create(
                firstname=data["firstname"],
                lastname=data["lastname"],
                email=data["email"],
                phone=data["phone"],
                dob=data.get("dob"),
                address=data.get("address"),
                role=role,
            )
            return JsonResponse(
                {"message": "Student created successfully", "id": student.id}, status=201
            )
        except KeyError as e:
            return JsonResponse({"error": f"Missing field: {e}"}, status=400)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def put(self, request, student_id):
        """
        PUT: Update student details.
        - Only Moderators can update students.
        """
        if not self.has_permission(request.Profile, "update"):
            return JsonResponse({"error": "Access Denied"}, status=403)

        try:
            data = json.loads(request.body)
            student = Profile.objects.get(id=student_id, role__role_title="student")

            student.firstname = data.get("firstname", student.firstname)
            student.lastname = data.get("lastname", student.lastname)
            student.phone = data.get("phone", student.phone)
            student.dob = data.get("dob", student.dob)
            student.address = data.get("address", student.address)
            student.is_active = data.get("is_active", student.is_active)
            student.save()

            return JsonResponse({"message": "Student updated successfully"})
        except Profile.DoesNotExist:
            return JsonResponse({"error": "Student not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    def delete(self, request, student_id):
        """
        DELETE: Delete a student.
        - Only Moderators can delete students.
        """
        if not self.has_permission(request.Profile, "delete"):
            return JsonResponse({"error": "Access Denied"}, status=403)

        try:
            student = Profile.objects.get(id=student_id, role__role_title="student")
            student.delete()
            return JsonResponse({"message": "Student deleted successfully"})
        except Profile.DoesNotExist:
            return JsonResponse({"error": "Student not found"}, status=404)
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
