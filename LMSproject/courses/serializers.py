# serializers.py
from rest_framework import serializers
from .models import Courses

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ['id', 'courseName', 'instructorName', 'created_at', 'updated_at', 'studentsCount', 'videosCount']
