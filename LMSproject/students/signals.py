from django.db.models.signals import post_save
from django.dispatch import receiver
from users.models import CustomUser
from .models import Students

@receiver(post_save, sender=CustomUser)
def create_student_profile(sender, instance, created, **kwargs):
    # Check if a new CustomUser is created and the role is 'student'
    if created and instance.role == 'student':
        Students.objects.create(user=instance)
