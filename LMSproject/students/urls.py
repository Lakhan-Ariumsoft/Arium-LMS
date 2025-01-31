from django.urls import path
from .views import StudentsListCreateAPIView, StudentsDetailAPIView  , DashboardAPIView

urlpatterns = [
    path('', StudentsListCreateAPIView.as_view(), name='students-list-create'),
    path('<int:pk>/', StudentsDetailAPIView.as_view(), name='get-delete-put'),
     path('dashboard/', DashboardAPIView.as_view(), name='studentdashboard'),
    # path('search/', StudentsFilterAPIView.as_view(), name='students-search')
]

