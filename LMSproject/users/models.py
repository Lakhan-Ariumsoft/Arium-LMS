from django.contrib.auth.models import AbstractUser
from django.db import models
from courses.models import Courses

class Permission(models.Model):
    name = models.CharField(max_length=100, unique=True)
    can_read_users = models.BooleanField(default=False)
    can_write_users = models.BooleanField(default=False)
    can_read_courses = models.BooleanField(default=False)
    can_write_courses = models.BooleanField(default=False)
    can_read_meetings = models.BooleanField(default=False)
    can_write_meetings = models.BooleanField(default=False)
    can_read_meetings = models.BooleanField(default=False)
    can_create_meetings = models.BooleanField(default=False)
    can_update_meetings = models.BooleanField(default=False)
    can_delete_meetings = models.BooleanField(default=False)
    can_read_students = models.BooleanField(default=False)
    can_create_students = models.BooleanField(default=False)
    can_update_students = models.BooleanField(default=False)
    can_delete_students = models.BooleanField(default=False)

    def __str__(self):
        return self.name

class Role(models.Model):
    name = models.CharField(max_length=50, unique=True)
    permissions = models.ForeignKey(Permission, on_delete=models.CASCADE)

    def __str__(self):
        return self.name

class User(AbstractUser):
    email = models.EmailField(unique=True)
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    countryCode = models.CharField(max_length=10, blank=True, null=True)
    phone = models.CharField(max_length=15, blank=True, null=True , unique=True)
    dob = models.DateField(verbose_name="Date of Birth", null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    created_on = models.DateTimeField(auto_now_add=True ,blank=True)
    last_updated_on = models.DateTimeField(auto_now=True ,blank=True)
    is_active = models.BooleanField(default=True)
    is_admin = models.BooleanField(default=False)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)


    def __str__(self):
        return f"{self.username})"
    

class Instructor(models.Model):
    firstname = models.CharField(max_length=255)
    lastname = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phonenumber = models.CharField(max_length=15, unique=True)
    dob = models.DateField()
    address = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    assigned_courses = models.ManyToManyField(Courses, related_name="instructors")

    def __str__(self):
        return f"{self.firstname} {self.lastname}"








# from django.contrib.auth.models import AbstractUser,UserManager
# from django.db import models
# from django.contrib.auth.hashers import make_password


# class UserManager(UserManager):
#     def _create_user(self, email, password, **extra_fields):
#         email = self.normalize_email(email)
#         user = Profile(email=email, **extra_fields)
#         user.password = make_password(password)
#         user.save(using=self._db)
#         return user

#     def create_user(self, email, password=None, **extra_fields):
#         extra_fields.setdefault("is_staff", False)
#         extra_fields.setdefault("is_superuser", False)
#         # extra_fields.setdefault("role_id", "1")
#         return self._create_user(email, password, **extra_fields)

#     def create_superuser(self, email, password=None, **extra_fields):
#         extra_fields.setdefault("is_staff", True)
#         extra_fields.setdefault("is_superuser", True)

#         assert extra_fields["is_staff"]
#         assert extra_fields["is_superuser"]
#         return self._create_user(email, password, **extra_fields)


# # Role Model
# class Role(models.Model):
#     role_title = models.CharField(max_length=20, default='student')

#     def __str__(self):
#         return self.role_title
 
# # Custom Permission Model (Separate from Django's Permission system)
# class Permission(models.Model):
#     role = models.ForeignKey(Role, on_delete=models.CASCADE)
#     meetings_read = models.BooleanField(default=False)
#     meetings_write = models.BooleanField(default=False)
#     meetings_full = models.BooleanField(default=False)
#     courses_read = models.BooleanField(default=False)
#     courses_write = models.BooleanField(default=False)
#     courses_full = models.BooleanField(default=False)
#     users_read = models.BooleanField(default=False)
#     users_write = models.BooleanField(default=False)
#     users_full = models.BooleanField(default=False)

# # Custom User Model
# class Profile(AbstractUser):  # No use of Group or Django's Permission
#     firstname = models.CharField(max_length=50)
#     lastname = models.CharField(max_length=50)
#     email = models.EmailField(unique=True)
#     phone = models.CharField(max_length=15)
#     dob = models.DateField(verbose_name="Date of Birth", null=True, blank=True)
#     address = models.TextField(null=True, blank=True)
#     is_active = models.BooleanField(default=True)
#     created_on = models.DateTimeField(auto_now_add=True)
#     last_updated_on = models.DateTimeField(auto_now=True)
#     role = models.ForeignKey(Permission, on_delete=models.CASCADE,null=True, blank=True)
#     USERNAME_FIELD = "email"
#     REQUIRED_FIELDS = []
#     objects = UserManager()

#     def __str__(self):
#         return f"{self.firstname} {self.lastname}"

# from django.db import models
# from courses.models import Course

# # Student Model
# class Profile(models.Model):
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

#      # Define many-to-many relationship using Enrollment as intermediate model

#     def __str__(self):
#         return f"{self.firstname} {self.lastname}"

# # Enrollment Model
# class Enrollment(models.Model):
#     student = models.ForeignKey(Profile, on_delete=models.CASCADE)
#     course = models.ForeignKey(Course, on_delete=models.CASCADE)
#     enrollmentDate = models.DateField()
#     expiryDate = models.DateField()
#     courses = models.ManyToManyField(Course, through='Enrollment', related_name='students')


#     def __str__(self):
#         return f"{self.student} - {self.course}"