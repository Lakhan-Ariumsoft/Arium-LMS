from django.db import models
from courses.models import Courses  # Ensure that the Courses model is correctly imported

class ZoomMeeting(models.Model):
    course = models.ForeignKey(Courses, null=True, blank=True, on_delete=models.SET_NULL)  # Allows blank course
    title = models.CharField(max_length=200)
    meeting_id = models.CharField(max_length=50)  # Meeting ID should be unique
    duration = models.IntegerField()  # Duration is fine, but you might want to specify time units (seconds)
    recording_url = models.URLField()  # URL for the recording
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Zoom Meeting: {self.title} - {self.meeting_id}"

