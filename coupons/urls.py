from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    path('apply/', views.apply_coupon_view, name='apply'),
    path('remove/', views.remove_coupon_view, name='remove'),
]