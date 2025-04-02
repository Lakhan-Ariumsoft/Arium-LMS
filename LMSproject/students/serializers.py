from rest_framework import serializers
from .models import Students, Enrollment
from courses.models import Courses

class CoursesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = [ 'courses', 'instructorName' ,'studentCount','videosCount']

class EnrollmentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Enrollment
        fields = ['student', 'courses', 'enrollmentDate', 'expiryDate' , 'status']
        extra_kwargs = {
            'enrollmentDate': {'required': False, 'allow_null': True},
            'expiryDate': {'required': False, 'allow_null': True},
        }
class StudentsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Students
        fields = ['id', 'firstname', 'lastname', 'email', 'phone', 'dob','countryCode','address', 'courses','batch', 'created_on', 'updated_on']
