from django.urls import path
from .views import CourseView

urlpatterns = [
    path('', CourseView.as_view(), name='course_list'),
    path('<int:pk>/', CourseView.as_view(), name='course_detail'),
]
