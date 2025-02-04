from rest_framework import serializers
from .models import Recordings
from courses.models import Courses

class RecordingsSerializer(serializers.ModelSerializer):
    course_ids = serializers.ListField(child=serializers.IntegerField(), write_only=True, required=False)
    course_names = serializers.SerializerMethodField()

    class Meta:
        model = Recordings
        fields = ['id', 'title', 'meeting_id', 'duration', 'recording_url', 'created_at', 'updated_at', 'course_ids', 'course_names' , 'course']

    def get_course_names(self, obj):
        return obj.course.courseName if obj.course else None  # Directly access courseName


    def create(self, validated_data):
        course_ids = validated_data.pop('course_ids', [])
        recording = Recordings.objects.create(**validated_data)

        if course_ids:
            courses = Courses.objects.filter(id__in=course_ids)
            recording.course.set(courses)  # Use `.set()` for ManyToManyField
        else:
            recording.status = "unassigned"  # Set status if no course assigned
        
        recording.save()
        return recording



    def update(self, instance, validated_data):
        course_ids = validated_data.pop('course_ids', [])
        
        old_course = instance.course
        new_course = Courses.objects.filter(id__in=course_ids).first() if course_ids else None

        if old_course and old_course != new_course:
            old_course.videosCount = max(0, old_course.videosCount - 1)
            old_course.save()

        if new_course and new_course != old_course:
            new_course.videosCount += 1
            new_course.save()
            instance.course = new_course
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        return instance
