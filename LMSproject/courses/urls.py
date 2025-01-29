# urls.py
from django.urls import path
from .views import CourseView, CourseDropdownListView, InstructorListView

urlpatterns = [
    path('', CourseView.as_view(), name='course_list'),
    path('<int:pk>/', CourseView.as_view(), name='course_detail'),

    path('courses/', CourseDropdownListView.as_view(), name='course-list'),
    path('instructors/', InstructorListView.as_view(), name='instructor-list'),
]
