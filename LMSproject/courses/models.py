from django.db import models
from django.conf import settings
from django.utils.timezone import now

class Courses(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructor_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=15 , verbose_name="Instructor phone")
    dob = models.DateField(verbose_name="Instructor DOB")
    start_date = models.DateField()
    end_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title
