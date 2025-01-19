from django.urls import path
from .views import LoginAPIView , LogoutView ,CSRFView # Import the LoginAPIView from your views.py

urlpatterns = [
    path('login/', LoginAPIView.as_view(), name='login'),  # Add the URL pattern for login
    path('logout/', LogoutView.as_view(), name='logout'),
    path('csrf/', CSRFView.as_view(), name='csrf'),




]
