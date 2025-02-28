# serializers.py
from rest_framework import serializers
from .models import Courses

class CourseSerializer(serializers.ModelSerializer):

    instructor = serializers.SerializerMethodField()
    # instructor = serializers.PrimaryKeyRelatedField(
    #     queryset=Instructor.objects.all(), allow_null=True, required=False
    # ) 
    class Meta:
        model = Courses
        fields = ['id', 'courseName', 'instructor', 'created_at', 'updated_at', 'studentsCount', 'videosCount']

    def get_instructor(self, obj):
        """Retrieve instructor ID and name if assigned."""
        if obj.instructor:
            return {
                "id": obj.instructor.id,
                "name": f"{obj.instructor.firstname} {obj.instructor.lastname}"
            }
        return None 