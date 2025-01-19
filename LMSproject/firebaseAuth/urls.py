from django.urls import path
from .views import GetOTP, VerifyOTP, SignUp, Login

urlpatterns = [
    path('getOtp/', GetOTP.as_view(), name='send-otp'),
    path('verify-otp/', VerifyOTP.as_view(), name='verify-otp'),
    path('signup/', SignUp.as_view(), name='signup'),
    path('login/', Login.as_view(), name='login'),
]
