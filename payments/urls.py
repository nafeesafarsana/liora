from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('initiate/<str:order_id>/', views.initiate_payment_view, name='initiate'),
    path('callback/', views.payment_callback_view, name='callback'),
    path('success/', views.payment_success_view, name='success'),
    path('failure/<str:order_id>/', views.payment_failure_view, name='failure'),
]