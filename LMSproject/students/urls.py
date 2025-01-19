
from django.urls import path
from . import views

urlpatterns = [
    # Create a new student
    path('create/', views.create_student, name='create_student'),

    # Read (List) all students (accessible by moderator)
    path('list/', views.list_students, name='list_students'),

    # Read (Retrieve) a single student by ID (accessible by moderator)
    path('<int:student_id>/', views.get_student, name='get_student'),

    # Update an existing student (accessible by moderator)
    path('<int:student_id>/update/', views.update_student, name='update_student'),

    # Delete a student (accessible by moderator)
    path('<int:student_id>/delete/', views.delete_student, name='delete_student'),
]
