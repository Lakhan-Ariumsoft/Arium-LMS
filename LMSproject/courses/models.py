from django.db import models

class Courses(models.Model):
    courseName = models.CharField(max_length=255 , unique=True)
    instructor = models.ForeignKey(
        "users.Instructor",  # Use app_name.ModelName as a string
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="courses"
    )
    # instructorName = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    studentsCount = models.IntegerField(default=0)
    videosCount = models.IntegerField(default=0)

    def __str__(self):
        return self.courseName