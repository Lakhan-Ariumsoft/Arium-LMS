from django.contrib import admin
from .models import Students, Enrollment
from courses.models import Courses


class EnrollmentInline(admin.TabularInline):
    model = Enrollment
    extra = 1
    fields = ['courses', 'enrollmentDate', 'expiryDate']
    verbose_name = "Enrollment"
    verbose_name_plural = "Enrollments"


@admin.register(Students)
class StudentsAdmin(admin.ModelAdmin):
    list_display = ('firstname', 'lastname', 'email', 'phone', 'batch','created_on', 'updated_on')
    list_filter = ('batch', 'created_on')
    search_fields = ('firstname', 'lastname', 'email', 'phone', 'batch')
    readonly_fields = ('created_on', 'updated_on')
    fieldsets = (
        ("Personal Information", {
            'fields': ('firstname', 'lastname', 'email', 'countryCode', 'phone', 'dob', 'address'),
        }),
        ("Batch & Status", {
            'fields': ('batch',),
        }),
        ("Timestamps", {
            'fields': ('created_on', 'updated_on'),
        }),
    )
    inlines = [EnrollmentInline]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ('student', 'courses', 'enrollmentDate', 'expiryDate','status' ,'created_at', 'updated_at')
    list_filter = ('enrollmentDate', 'expiryDate', 'created_at')
    search_fields = ('student__firstname', 'student__lastname', 'courses__courseName')


@admin.register(Courses)
class CoursesAdmin(admin.ModelAdmin):
    list_display = ('courseName', 'studentsCount', 'videosCount', 'created_at', 'updated_at')
    list_filter = ('created_at', 'updated_at')
    search_fields = ('courseName',)
