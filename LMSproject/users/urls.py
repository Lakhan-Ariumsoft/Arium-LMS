from django.urls import path
from .views import LoginAPIView , LogoutAPIView  ,InstructorListCreateView, InstructorRetrieveUpdateDestroyView ,InstructorDashboardView # Import the LoginAPIView from your views.py
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),  # Add the URL pattern for login
    path('logout/', LogoutAPIView.as_view(), name='logout'),
    # path('csrf/', CSRFView.as_view(), name='csrf'),
    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path("instructors/", InstructorListCreateView.as_view(), name="instructor-list-create"),
    path("instructors/<int:pk>/", InstructorRetrieveUpdateDestroyView.as_view(), name="instructor-detail"),
    path("instructors/dashboard/", InstructorDashboardView.as_view(), name="dashboard"),



]
