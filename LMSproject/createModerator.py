import django
from django.contrib.auth.models import Group
from django.utils import timezone
from users.models import User  # Replace with your app name


def create_groups_and_moderator(phone, name, password, email, role='moderator'):
    # Create roles (groups) if not already created
    moderator_group, created = Group.objects.get_or_create(name='moderator')
    instructor_group, created = Group.objects.get_or_create(name='instructor')
    student_group, created = Group.objects.get_or_create(name='student')

    # Create the moderator user
    user = User.objects.create(
        username=name,  # Username can be name or something else as per your requirement
        email=email,
        phone=phone,
        role=role,
        is_staff=True,  # You can set to True for moderator to have admin access
        is_active=True,
    )
    user.set_password(password)  # Set the password
    user.save()

    # Assign the user to the 'moderator' group
    user.groups.add(moderator_group)

    # Print the moderator user details
    print(f'Moderator {user.username} created with phone {user.phone} and role {user.role}')

    return user


# Replace with the actual phone number, name, password, and email you want to provide
phone_number = input("Enter phone number: ")
name = input("Enter name: ")
password = input("Enter password: ")
email = input("Enter email: ")

create_groups_and_moderator(phone_number, name, password, email)
