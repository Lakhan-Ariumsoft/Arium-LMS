from django.urls import path
from .views import SendOTP, VerifyOTP, Signup, Login

urlpatterns = [
    path('getOtp/', SendOTP.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTP.as_view(), name='verify-otp'),
    path('signup/', Signup.as_view(), name='signup'),
    path('login/', Login.as_view(), name='login'),
]
