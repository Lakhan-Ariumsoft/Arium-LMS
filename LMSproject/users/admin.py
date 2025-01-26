from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import Group, Permission
from .models import User,Role,Permission



class PermissionAdmin(admin.ModelAdmin):
    list_display = ('name', 'can_read_users', 'can_write_users', 'can_read_courses', 'can_write_courses', 'can_read_meetings', 'can_write_meetings')
    search_fields = ('name',)
    list_filter = ('can_read_users', 'can_write_users', 'can_read_courses', 'can_write_courses', 'can_read_meetings', 'can_write_meetings')

class RoleAdmin(admin.ModelAdmin):
    list_display = ('name', 'permissions')
    search_fields = ('name',)
    # filter_horizontal = ('permissions',) 

class UserAdmin(BaseUserAdmin):
    # Fields to display in the list view
    list_display = ('username', 'email', 'firstname', 'lastname','is_active', 'is_admin')
    list_filter = ('is_active', 'is_admin')

    # Fieldsets without groups and permissions
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {'fields': ('firstname', 'lastname', 'email', 'phone', 'countryCode', 'dob', 'address','role')}),
        ('Status', {'fields': ('is_active', 'is_admin', 'is_superuser')}),
    )

    # Add user form without groups and permissions
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'firstname', 'lastname'),
        }),
    )

    search_fields = ('username', 'email', 'firstname', 'lastname', 'phone' ,'countryCode')
    ordering = ('username',)



admin.site.register(Permission, PermissionAdmin)
admin.site.register(Role, RoleAdmin)
admin.site.register(User, UserAdmin)

admin.site.unregister(Group)