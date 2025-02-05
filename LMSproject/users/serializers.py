from rest_framework import serializers
from .models import User, Role, Permission
from .models import Instructor
from courses.models import Courses

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'can_read_users', 'can_write_users', 'can_read_courses', 'can_write_courses',
                  'can_read_meetings', 'can_write_meetings']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(read_only=True)  # Nested PermissionSerializer

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)  # Nested RoleSerializer

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'firstname', 'lastname', 'countryCode', 'phone', 'dob', 'address',
                  'created_on', 'last_updated_on', 'is_active', 'is_admin', 'role']

    def create(self, validated_data):
        role_data = validated_data.pop('role', None)
        user = User.objects.create(**validated_data)

        if role_data:
            role = Role.objects.create(**role_data)
            user.role = role
            user.save()

        return user

    def update(self, instance, validated_data):
        role_data = validated_data.pop('role', None)
        
        # Update User fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.firstname = validated_data.get('firstname', instance.firstname)
        instance.lastname = validated_data.get('lastname', instance.lastname)
        instance.countryCode = validated_data.get('countryCode', instance.countryCode)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.address = validated_data.get('address', instance.address)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.is_admin = validated_data.get('is_admin', instance.is_admin)
        instance.save()

        if role_data:
            # If a role is passed, update it
            instance.role.name = role_data.get('name', instance.role.name)
            instance.role.save()

        return instance
    

# instructor  serializers.py



from rest_framework import serializers
from .models import Instructor
from courses.models import Courses
from django.db import transaction
import traceback

class InstructorSerializer(serializers.ModelSerializer):
    # Adding assigned courses for the instructor
    # assigned_courses = serializers.SerializerMethodField()
    assigned_courses = serializers.PrimaryKeyRelatedField(
        queryset=Courses.objects.all(), many=True, required=False
    )

    class Meta:
        model = Instructor
        fields = ['id', 'firstname', 'lastname', 'email', 'phone','countryCode' ,'dob', 'address', 'created_at', 'updated_at', 'assigned_courses' ]

    def get_assigned_courses(self, obj):
        # Get the names of the courses assigned to the instructor
        assigned_courses = obj.assigned_courses.all()
        return [{"course_name": course.courseName} for course in assigned_courses] if assigned_courses.exists() else []

    def create(self, validated_data):
        email = validated_data.pop("email")  # Extract email separately
        firstname = validated_data.pop("firstname")
        lastname = validated_data.pop("lastname")
        phone = validated_data.pop("phone")
        countryCode = validated_data.pop("countryCode")

        assigned_courses = validated_data.pop("assigned_courses", [])  # Extract courses

        try:
            with transaction.atomic():  # Rollback if an error occurs
                # Fetch or create role instance
                instructor_role, _ = Role.objects.get_or_create(name__iexact='instructor')

                # Check if user already exists
                user, created = User.objects.get_or_create(email=email, defaults={
                    "username": email,
                    "first_name": firstname,
                    "last_name": lastname,
                    "phone": phone,
                    "countryCode":countryCode,
                    "role": instructor_role,  
                    "is_active": True
                })

                # If user exists but inactive, reactivate
                if not created and not user.is_active:
                    user.is_active = True
                    user.first_name = firstname
                    user.last_name = lastname
                    user.phone = phone
                    user.countryCode = countryCode
                    user.role = instructor_role
                    user.save()

                # Create Instructor entry
                instructor = Instructor.objects.create(
                    email=email, firstname=firstname, lastname=lastname,
                    phone=phone,countryCode=countryCode,**validated_data
                )

                print("Assigned Courses:", assigned_courses)
                if assigned_courses:
                    print(f"Raw assigned_courses: {assigned_courses}")  

                    # Ensure assigned_courses is a list of integers (IDs)
                    assigned_course_ids = [course.id if isinstance(course, Courses) else course for course in assigned_courses]
                    print(f"Processed assigned_course_ids: {assigned_course_ids}")  

                    # Fetch courses using the corrected IDs
                    courses = Courses.objects.filter(id__in=assigned_course_ids)
                    print(f"Filtered courses: {list(courses.values_list('id', flat=True))}")  
                    print("+++++++++++++++ Courses +++++++++++++", courses)

                    if courses.exists():
                        instructor.assigned_courses.set(courses)  #  Correct way to assign many-to-many
                    else:
                        raise ValueError("Invalid Course IDs provided.")


                return instructor

        except Exception as e:
            tb = traceback.format_exc()  # Get full traceback
            print(f"Error creating instructor: {str(e)}")
            print(f"Traceback:\n{tb}")  # Print full traceback
            raise ValueError(f"Failed to create instructor: {str(e)}")