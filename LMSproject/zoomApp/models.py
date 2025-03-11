from django.db import models
from courses.models import Courses  # Ensure that the Courses model is correctly imported

class Recordings(models.Model):
    course = models.ManyToManyField(Courses, related_name="recordings" , null=True)
    # course = models.ForeignKey(Courses, null=True, blank=True, on_delete=models.SET_NULL)  # Allows blank course
    filePath = models.CharField(max_length=6000)
    title = models.CharField(max_length=200)
    meeting_id = models.CharField(max_length=50)  # Meeting ID should be unique
    duration = models.IntegerField(blank=True)  # Duration is fine, but you might want to specify time units (seconds)
    recording_url = models.URLField(max_length=10000,blank=True)  # URL for the recording
    expiration_time = models.DateTimeField(null=True, blank=True)  # Stores signed URL expiry time
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Recodings: {self.title} - {self.meeting_id}"

