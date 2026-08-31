from django.urls import path
from . import views

app_name = 'offers'

urlpatterns = [
    path('my-referral/', views.my_referral_view, name='my_referral'),
    path('apply-referral/', views.apply_referral_view, name='apply_referral'),
]