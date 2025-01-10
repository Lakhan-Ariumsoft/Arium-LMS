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
