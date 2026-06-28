from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('signup/', views.signup_view, name='signup'),
    path('signup/otp/', views.signup_otp_view, name='signup_otp'),
    path('signup/otp/resend/', views.resend_signup_otp_view, name='resend_signup_otp'),

    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('forgot-password/otp/', views.forgot_otp_view, name='forgot_otp'),
    path('forgot-password/otp/resend/', views.resend_forgot_otp_view, name='resend_forgot_otp'),
    path('reset-password/', views.reset_password_view, name='reset_password'),
]
