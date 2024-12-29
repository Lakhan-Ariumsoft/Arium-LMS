from django.db import models
from django.conf import settings
from django.utils.timezone import now

class Course(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    dob = models.DateField(verbose_name="Instructor DOB")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

class CourseEnrollment(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='enrollments')
    course = models.ForeignKey(Course, on_delete=models.CASCADE, related_name='enrollments')
    enrollment_date = models.DateTimeField(default=now)
    status = models.CharField(max_length=20, choices=[('active', 'Active'), ('completed', 'Completed')])

    def __str__(self):
        return f"{self.user.email} - {self.course.title}"
