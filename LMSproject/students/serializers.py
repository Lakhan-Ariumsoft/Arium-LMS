from rest_framework import serializers
from .models import Students, Enrollment
from courses.models import Courses

class CoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = [ 'courses', 'instructorName' ,'studentCount','videoCount']

class EnrollmentSerializer(serializers.ModelSerializer):
    # Course = CoursesSerializer()

    class Meta:
        model = Enrollment
        fields = ['student', 'courses', 'enrollmentDate', 'expiryDate']

class StudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = ['id', 'firstname', 'lastname', 'email', 'phone', 'dob', 'address', 'courses','batch', 'status', 'created_on', 'updated_on']
