from django.contrib.auth.models import AbstractUser,UserManager
from django.db import models
from django.contrib.auth.hashers import make_password


class CustomUserManager(UserManager):
    def _create_user(self, email, password, **extra_fields):
        email = self.normalize_email(email)
        user = Profile(email=email, **extra_fields)
        user.password = make_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        # extra_fields.setdefault("role_id", "1")
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        assert extra_fields["is_staff"]
        assert extra_fields["is_superuser"]
        return self._create_user(email, password, **extra_fields)


# Role Model
class Role(models.Model):
    role_title = models.CharField(max_length=20, default='student')

    def __str__(self):
        return self.role_title
 
# Custom Permission Model (Separate from Django's Permission system)
class Permission(models.Model):
    role = models.ForeignKey(Role, on_delete=models.CASCADE)
    meetings_read = models.BooleanField(default=False)
    meetings_write = models.BooleanField(default=False)
    meetings_full = models.BooleanField(default=False)
    courses_read = models.BooleanField(default=False)
    courses_write = models.BooleanField(default=False)
    courses_full = models.BooleanField(default=False)
    users_read = models.BooleanField(default=False)
    users_write = models.BooleanField(default=False)
    users_full = models.BooleanField(default=False)

# Custom User Model
class Profile(AbstractUser):  # No use of Group or Django's Permission
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15)
    dob = models.DateField(verbose_name="Date of Birth", null=True, blank=True)
    address = models.TextField(null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_on = models.DateTimeField(auto_now_add=True)
    last_updated_on = models.DateTimeField(auto_now=True)
    role = models.ForeignKey(Permission, on_delete=models.CASCADE,null=True, blank=True)
    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = CustomUserManager()

    def __str__(self):
        return f"{self.firstname} {self.lastname}"
