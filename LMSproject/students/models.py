from django.db import models
from users.models import User
from courses.models import Courses
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.contrib.auth.hashers import make_password
from django.utils.timezone import now
from .models import User
from users.models import Role  # Import Role model (adjust import path if necessary)
from django.db.models.signals import post_save, pre_delete
from django.http import JsonResponse
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver

class Students(models.Model):
    # user = models.OneToOneField(User, on_delete=models.CASCADE)
    firstname = models.CharField(max_length=50)
    lastname = models.CharField(max_length=50)
    email = models.EmailField(unique=True)
    countryCode = models.CharField(max_length=10, blank=True)
    phone = models.CharField(max_length=15, blank=True)
    dob = models.DateField(verbose_name="Date of Birth", blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    batch = models.CharField(max_length=50, default="", blank=True)
    courses = models.ManyToManyField(Courses, through='Enrollment', related_name='students')
    # status = models.CharField(max_length=20,default=True )
    created_on = models.DateTimeField(auto_now_add=True)
    updated_on = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.firstname} - {self.batch}"

class Enrollment(models.Model):
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('expired', 'Expired'),
        ('cancelled', 'Cancelled')
    ]
    student = models.ForeignKey(Students, on_delete=models.CASCADE)
    courses = models.ForeignKey(Courses, on_delete=models.CASCADE)  # ForeignKey to Courses
    enrollmentDate = models.DateField(null=True, blank=True)
    expiryDate = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')


    def __str__(self):
        return f"{self.student} - {self.courses.courseName}"



# Signal to check and update enrollment status
@receiver(pre_save, sender=Enrollment)
def update_enrollment_status(sender, instance, **kwargs):
    """Automatically update status based on expiryDate."""
    if instance.expiryDate and instance.expiryDate < now().date():
        instance.status = 'expired'

@receiver(post_save, sender=Enrollment)
def deactivate_student_if_no_active_enrollments(sender, instance, **kwargs):
    """Deactivate student if all enrollments are expired or cancelled."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    student = instance.student

    # Check if the student has any active enrollments
    active_enrollments = Enrollment.objects.filter(student=student, status='active').exists()

    try:
        user = User.objects.get(email=student.email)
        if not active_enrollments:
            user.is_active = False
            user.save()
    except User.DoesNotExist:
        pass  # If no user is found, skip deactivation



from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.timezone import now
from django.contrib.auth.hashers import make_password
import os
import logging
logger = logging.getLogger(__name__)



@receiver(post_save, sender=Students)
def create_or_update_user_for_student(sender, instance, created, **kwargs):
    print("In create_or_update_user_for_student ")

    try:
        print("IN CREATE USER ::::+++")
        # Start a database transaction
        with transaction.atomic():
            # Fetch the numeric ID for the "Student" role
            student_role_id = Role.objects.get(name__iexact='student').id
            logger.info(f"Updating or creating user for student {instance.id}")
            # Check if the student has an associated user
            user = User.objects.filter(email=instance.email).first()
            print("aaaa",instance.countryCode , instance)
            if user:
                # If user exists, update the user data
                user.firstname = instance.firstname
                user.lastname = instance.lastname
                user.phone = instance.phone
                user.dob = instance.dob
                user.address = instance.address
                user.countryCode = instance.countryCode
                user.last_updated_on = now()  # Update the last updated timestamp
                user.save(update_fields=['firstname', 'lastname', 'phone', 'dob', 'address', 'countryCode', 'last_updated_on'])
                print(f"Updated User: {user.username}")
            else:
                # If no user exists, create a new user instance
                User.objects.create(
                    username=f"{instance.firstname.lower()}.{instance.lastname.lower()}",  # Generate username
                    email=instance.email,
                    firstname=instance.firstname,
                    lastname=instance.lastname,
                    countryCode = instance.countryCode,
                    phone=instance.phone,
                    dob=instance.dob,
                    address=instance.address,
                    is_active=True,
                    is_admin=False,
                    role_id=student_role_id,  # Assign the "Student" role ID
                    password="Pass@1234",
                    # make_password(os.getenv('DEFAULT_USER_PASSWORD')),  # Set default hashed password
                    created_on=now(),
                    last_updated_on=now(),
                )
                print(f"Created User: {instance.email}")

            print("KKKKKKKKKKK",User.objects.all())

    except Role.DoesNotExist:
        # Clean up the student record if the role is missing
        instance.delete()
        logger.error(f"Error in create_or_update_user_for_student: {str(e)}")
        raise ValueError("Role 'Student' does not exist. The student record has been deleted.")

    except Exception as e:
        # Clean up the student record for any other errors
        instance.delete()
        logger.error(f"Error in create_or_update_user_for_student: {str(e)}")
        raise ValueError(f"An error occurred while creating or updating the User: {e}")


@receiver(post_save, sender=Students)
def handle_student_courses_update(sender, instance, created, **kwargs):
    """
    Signal to update the `studentsCount` field in the courses model
    when a student is created or their courses are updated.
    """
    try:
        print("In handle_student_courses_update ")
        with transaction.atomic():
            if created:
                # If a new student is created and assigned to courses
                for course in instance.courses.all():
                    course.studentsCount += 1
                    course.save()

            else:
                # If the student is updated, check if the courses have changed
                previous_instance = Students.objects.get(pk=instance.pk)

                # Decrease student count for removed courses
                for course in previous_instance.courses.all():
                    if course not in instance.courses.all():
                        course.studentsCount -= 1
                        course.save()

                # Increase student count for newly added courses
                for course in instance.courses.all():
                    if course not in previous_instance.courses.all():
                        course.studentsCount += 1
                        course.save()

    except Students.DoesNotExist:
        pass
    except Exception as e:
        raise ValueError(f"An error occurred while updating the courses data: {e}")
    

# when student has last course enrolled and he is deleted so he should not be enrolled 
@receiver(pre_delete, sender=Students)
def handle_student_deletion(sender, instance, **kwargs):
    """
    Signal to handle the deletion of a student and check if the user is associated with other courses.
    If the student is not enrolled in any other course, deactivate the user and delete the student record.
    """
    try:
        # Get all enrollments for this student
        enrollments = Enrollment.objects.filter(student=instance)
        
        if enrollments.exists():
            # If student is enrolled in other courses, leave them active
            enrollments.delete()
        else:
            # If the student is not enrolled in any other course, deactivate the user
            user = instance.user  # Assuming Student has a relation with User model
            user.is_active = False
            user.save()
            # Then delete the student record
            instance.delete()

    except Exception as e:
        # Catching any exception and returning a meaningful response
        return JsonResponse({"error": f"An error occurred: {str(e)}"}, status=400)