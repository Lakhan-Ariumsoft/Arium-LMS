# from django.db import transaction
# from django.db.models.signals import post_save, pre_delete
# from django.dispatch import receiver
# from django.utils.timezone import now
# from django.contrib.auth.hashers import make_password
# import os
# import logging
# from django.db.models import Q
# from .models import Students, Role, Enrollment
# from django.contrib.auth import get_user_model

# logger = logging.getLogger(__name__)

# @receiver(post_save, sender=Students)
# def create_or_update_user_for_student(sender, instance, created, **kwargs):
#     try:
#         with transaction.atomic():
#             student_role_id = Role.objects.get(name__iexact='student').id
#             logger.info(f"Updating or creating user for student {instance.id}")
            
#             # Fetch custom user model
#             User = get_user_model()

#             # Ensure that the current user is correctly accessed for updates
#             if not hasattr(instance, 'user'):
#                 raise ValueError("Student does not have an associated user.")
            
#             # Check if the phone or email already exists (excluding the current user)
#             existing_user = User.objects.filter(
#                 Q(email=instance.email) | Q(phone=instance.phone)
#             ).exclude(id=instance.user.id).first()

#             if existing_user:
#                 raise ValueError(f"A user with this email or phone already exists: {existing_user.email} / {existing_user.phone}")

#             if created:
#                 # If it's a new student, create a new user instance
#                 User.objects.create(
#                     username=f"{instance.firstname.lower()}.{instance.lastname.lower()}",
#                     email=instance.email,
#                     firstname=instance.firstname,
#                     lastname=instance.lastname,
#                     countryCode=instance.countryCode,
#                     phone=instance.phone,
#                     dob=instance.dob,
#                     address=instance.address,
#                     is_active=True,
#                     is_admin=False,
#                     role_id=student_role_id,
#                     password=make_password(os.getenv('DEFAULT_USER_PASSWORD')),
#                     created_on=now(),
#                     last_updated_on=now(),
#                 )
#                 logger.info(f"Created User: {instance.email}")
#             else:
#                 # If it's an update, update the existing user
#                 user = instance.user
#                 user.firstname = instance.firstname
#                 user.lastname = instance.lastname
#                 user.phone = instance.phone
#                 user.dob = instance.dob
#                 user.address = instance.address
#                 user.countryCode = instance.countryCode
#                 user.last_updated_on = now()
#                 user.save(update_fields=['firstname', 'lastname', 'phone', 'dob', 'address', 'countryCode', 'last_updated_on'])
#                 logger.info(f"Updated User: {user.username}")

#     except Role.DoesNotExist:
#         instance.delete()
#         logger.error("Role 'Student' does not exist.")
#         raise ValueError("Role 'Student' does not exist.")
#     except Exception as e:
#         instance.delete()
#         logger.error(f"Error in create_or_update_user_for_student: {str(e)}")
#         raise ValueError(f"An error occurred: {e}")

# @receiver(post_save, sender=Students)
# def handle_student_courses_update(sender, instance, created, **kwargs):
#     try:
#         with transaction.atomic():
#             if created:
#                 for course in instance.courses.all():
#                     course.studentsCount += 1
#                     course.save()
#             else:
#                 previous_instance = Students.objects.get(pk=instance.pk)
#                 for course in previous_instance.courses.all():
#                     if course not in instance.courses.all():
#                         course.studentsCount -= 1
#                         course.save()
#                 for course in instance.courses.all():
#                     if course not in previous_instance.courses.all():
#                         course.studentsCount += 1
#                         course.save()
#     except Exception as e:
#         logger.error(f"Error in handle_student_courses_update: {str(e)}")
#         raise ValueError(f"An error occurred: {e}")

# @receiver(pre_delete, sender=Students)
# def handle_student_deletion(sender, instance, **kwargs):
#     try:
#         enrollments = Enrollment.objects.filter(student=instance)
#         if enrollments.exists():
#             enrollments.delete()
#         else:
#             user = instance.user
#             user.is_active = False
#             user.save()
#             instance.delete()
#     except Exception as e:
#         logger.error(f"Error in handle_student_deletion: {str(e)}")
#         raise ValueError(f"An error occurred: {e}")
