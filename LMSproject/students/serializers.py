from rest_framework import serializers
from .models import Students, Enrollment
from courses.models import Courses

class CoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = [ 'courses', 'instructorName' ,'studentCount','videosCount']

class EnrollmentSerializer(serializers.ModelSerializer):
    # Course = CoursesSerializer()

    class Meta:
        model = Enrollment
        fields = ['student', 'courses', 'enrollmentDate', 'expiryDate' , 'status']

class StudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = ['id', 'firstname', 'lastname', 'email', 'phone', 'dob','countryCode','address', 'courses','batch', 'created_on', 'updated_on']
