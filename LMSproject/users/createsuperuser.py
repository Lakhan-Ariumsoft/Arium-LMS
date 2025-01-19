from django.contrib.auth.management.commands.createsuperuser import Command as BaseCommand
from django.core.management import CommandError

class Command(BaseCommand):
    def handle(self, *args, **options):
        email = options.get('email')
        password = options.get('password')
        if not email:
            raise CommandError('You must provide an email address')
        self.UserModel._default_manager.create_superuser(email=email, password=password)
        self.stdout.write(f"Superuser created with email: {email}")


# from django.core.management.base import BaseCommand
# from your_app.models import User

# class Command(BaseCommand):
#     help = "Create a new Moderator"

#     def add_arguments(self, parser):
#         parser.add_argument('username', type=str, help='Username for the Moderator')
#         parser.add_argument('email', type=str, help='Email for the Moderator')
#         parser.add_argument('password', type=str, help='Password for the Moderator')

#     def handle(self, *args, **kwargs):
#         username = kwargs['username']
#         email = kwargs['email']
#         password = kwargs['password']

#         if User.objects.filter(username=username).exists():
#             self.stdout.write(self.style.ERROR('A user with this username already exists.'))
#             return

#         user = User.objects.create_user(
#             username=username,
#             email=email,
#             password=password,
#             role='moderator'
#         )
#         user.is_staff = True
#         user.is_superuser = True
#         user.save()

#         self.stdout.write(self.style.SUCCESS(f'Moderator "{username}" created successfully.'))
