from rest_framework import serializers
from .models import ZoomMeeting
from courses.models import Courses

class ZoomMeetingSerializer(serializers.ModelSerializer):
    courseName = serializers.CharField(source='course.name', read_only=True)  # Add course name to the response if course is assigned
    status = serializers.SerializerMethodField()  # Add a 'status' field to indicate whether the meeting is assigned or unassigned

    class Meta:
        model = ZoomMeeting
        fields = ['id', 'title', 'meeting_id', 'duration', 'recording_url', 'course', 'courseName', 'status', 'created_at', 'updated_at']

    def get_status(self, obj):
        # Determine the status (assigned or unassigned)
        return 'assigned' if obj.course else 'unassigned'

    def create(self, validated_data):
        """
        Override the create method to ensure that the course's videoCount is incremented
        when a new ZoomMeeting is created and assigned to a course.
        """
        course = validated_data.get('course')
        zoom_meeting = ZoomMeeting.objects.create(**validated_data)

        if course:
            course.videosCount += 1
            course.save()  # Save the updated videoCount for the course

        return zoom_meeting

    def update(self, instance, validated_data):
        """
        Override the update method to ensure that the course's videoCount is updated
        correctly when a ZoomMeeting is updated.
        """
        course = validated_data.get('course', instance.course)
        # Only update videoCount if the course has changed
        if course != instance.course:
            if instance.course:
                instance.course.videosCount -= 1
                instance.course.save()

            if course:
                course.videosCount += 1
                course.save()

        return super().update(instance, validated_data)
