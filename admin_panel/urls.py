from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    path('login/', views.admin_login_view, name='login'),
    path('logout/', views.admin_logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('users/', views.user_management_view, name='user_management'),
    path('users/<int:user_id>/toggle-block/', views.toggle_block_user_view, name='toggle_block_user'),
]