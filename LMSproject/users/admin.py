
# Register your models here.
from django.contrib import admin
from .models import Role,Permission

class RolesPermissionAdmin(admin.ModelAdmin):
    list_display = (
        'id','role', 'meetings_read', 'meetings_write', 'meetings_full',
        'courses_read', 'courses_write', 'courses_full', 
        'users_read', 'users_write', 'users_full'
    )
    list_filter = (
        'meetings_read', 'meetings_write', 'meetings_full', 
        'courses_read', 'courses_write', 'courses_full', 
        'users_read', 'users_write', 'users_full'
    )
    search_fields = ('id',)
    
    # Optionally, you can add fieldsets to group permissions logically if needed
    fieldsets = (
        ('rolepermissions',{'fields': ('role',)}),
        ('Meeting Permissions', {'fields': ('meetings_read', 'meetings_write', 'meetings_full')}),
        ('Course Permissions', {'fields': ('courses_read', 'courses_write', 'courses_full')}),
        ('User Permissions', {'fields': ('users_read', 'users_write', 'users_full')}),
    )

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

class CustomUserAdmin(UserAdmin):
    model = User

    # Define the fields to be displayed in the list view
    list_display = ('firstname', 'lastname', 'email', 'phone', 'dob', 'is_active', 'role', 'created_on')

    # Define the fields to be used in the search functionality
    search_fields = ('email', 'firstname', 'lastname', 'phone')

    # Define the fields to be displayed when editing a user
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('firstname', 'lastname', 'dob', 'address', 'phone', 'role','is_active')}),
    )

    # Define which fields should be used in the "Add User" form
    add_fieldsets = (
        (None, {
            'fields': ('email', 'password1', 'password2', 'firstname', 'lastname', 'dob', 'address', 'phone', 'role', 'is_active'),
        }),
    )

    # Optionally, exclude the 'created_on' field explicitly (in case it appears in any other places)
    exclude = ('created_on','last_updated_on')

    # Optionally, allow sorting based on any of the fields in the list display
    ordering = ('created_on',)

    # Remove 'is_staff' if it was previously added to `list_filter` or `ordering`
    list_filter = ('is_active', 'role')  # Use fields that actually exist in your model

# Register the customized UserAdmin
admin.site.register(User, CustomUserAdmin)

admin.site.register(Role)
admin.site.register(Permission, RolesPermissionAdmin)
