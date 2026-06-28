from django.urls import path
from . import views

app_name = 'profile_app'

urlpatterns = [
    path('', views.profile_view, name='profile'),
    path('edit/', views.edit_profile_view, name='edit_profile'),
    path('edit/verify-email/', views.verify_email_change_view, name='verify_email_change'),
    path('edit/verify-email/resend/', views.resend_email_change_otp_view, name='resend_email_change_otp'),
    path('change-password/', views.change_password_view, name='change_password'),

    path('addresses/', views.address_list_view, name='address_list'),
    path('addresses/add/', views.add_address_view, name='add_address'),
    path('addresses/edit/<int:pk>/', views.edit_address_view, name='edit_address'),
    path('addresses/delete/<int:pk>/', views.delete_address_view, name='delete_address'),
]