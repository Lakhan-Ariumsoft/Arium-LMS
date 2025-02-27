# serializers.py
from rest_framework import serializers
from .models import Courses

class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Courses
        fields = ['id', 'courseName', 'created_at', 'updated_at', 'studentsCount', 'videosCount']
