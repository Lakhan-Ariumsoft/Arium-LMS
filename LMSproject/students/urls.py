from django.urls import path
from . import views

urlpatterns = [
    # CRUD Operations for Student
    path('', views.list_students, name='list_students'),  # Get all students
    path('<int:student_id>/', views.get_student, name='get_student'),  # Get a single student
    path('create/', views.create_student, name='create_student'),  # Create a new student
    path('<int:student_id>/update/', views.update_student, name='update_student'),  # Update a student
    path('<int:student_id>/delete/', views.delete_student, name='delete_student'),  # Delete a student
]
