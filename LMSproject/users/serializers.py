from rest_framework import serializers
from .models import User, Role, Permission

class PermissionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = ['id', 'name', 'can_read_users', 'can_write_users', 'can_read_courses', 'can_write_courses',
                  'can_read_meetings', 'can_write_meetings']

class RoleSerializer(serializers.ModelSerializer):
    permissions = PermissionSerializer(read_only=True)  # Nested PermissionSerializer

    class Meta:
        model = Role
        fields = ['id', 'name', 'permissions']

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)  # Nested RoleSerializer

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'firstname', 'lastname', 'countryCode', 'phone', 'dob', 'address',
                  'created_on', 'last_updated_on', 'is_active', 'is_admin', 'role']

    def create(self, validated_data):
        role_data = validated_data.pop('role', None)
        user = User.objects.create(**validated_data)

        if role_data:
            role = Role.objects.create(**role_data)
            user.role = role
            user.save()

        return user

    def update(self, instance, validated_data):
        role_data = validated_data.pop('role', None)
        
        # Update User fields
        instance.username = validated_data.get('username', instance.username)
        instance.email = validated_data.get('email', instance.email)
        instance.firstname = validated_data.get('firstname', instance.firstname)
        instance.lastname = validated_data.get('lastname', instance.lastname)
        instance.countryCode = validated_data.get('countryCode', instance.countryCode)
        instance.phone = validated_data.get('phone', instance.phone)
        instance.dob = validated_data.get('dob', instance.dob)
        instance.address = validated_data.get('address', instance.address)
        instance.is_active = validated_data.get('is_active', instance.is_active)
        instance.is_admin = validated_data.get('is_admin', instance.is_admin)
        instance.save()

        if role_data:
            # If a role is passed, update it
            instance.role.name = role_data.get('name', instance.role.name)
            instance.role.save()

        return instance
