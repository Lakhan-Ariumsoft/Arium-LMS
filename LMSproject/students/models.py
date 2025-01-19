from django.db import models
from users.models import CustomUser
from courses.models import Courses

class Students(models.Model):
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='student_profile')
    dob = models.DateField(verbose_name="Date of Birth", blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    batch = models.CharField(max_length=50, default="", blank=True)
    courses = models.ManyToManyField(Courses, through='Enrollment', related_name='students')
    status = models.CharField(max_length=20,default=True )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.batch}"



class Enrollment(models.Model):
    student = models.ForeignKey(Students, on_delete=models.CASCADE)  # String reference to Student model
    course = models.ForeignKey(Courses, on_delete=models.CASCADE)
    date_of_joining = models.DateField()
    expiry_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student}- {self.course.title}"








# from django.db import models
# from courses.models import Course

# # Student Model
# class Student(models.Model):
#     ROLE_CHOICES = [
#         ('student', 'Student'),
#     ]

#     firstname = models.CharField(max_length=50)
#     lastname = models.CharField(max_length=50)
#     email = models.EmailField(unique=True)
#     phone = models.CharField(max_length=15, unique=True)
#     dob = models.DateField(verbose_name="Date of Birth")
#     address = models.TextField()
#     is_active = models.BooleanField(default=True)
#     created_on = models.DateTimeField(auto_now_add=True)
#     last_updated_on = models.DateTimeField(auto_now=True)
#     role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='student')  # Default role as 'student'
#     # status = models.CharField(max_length=20,default=True )
#     batch = models.CharField(max_length=50, default="")  # Fixed the typo
#      # Define many-to-many relationship using Enrollment as intermediate model
#     courses = models.ManyToManyField(Course, through='Enrollment', related_name='students')

#     def __str__(self):
#         return f"{self.firstname} {self.lastname}"

# # Enrollment Model
# class Enrollment(models.Model):
#     student = models.ForeignKey(Student, on_delete=models.CASCADE)
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     date_of_joining = models.DateField()
#     expiry_date = models.DateField()

#     def __str__(self):
#         return f"{self.student} - {self.course}"