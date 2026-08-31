from django.urls import path
from . import views

app_name = 'home'

urlpatterns = [
    path('', views.home_view, name='home'),
    path('about/', views.about_view, name='about'),  # ← add this
]