from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'orders'

urlpatterns = [
    path('', RedirectView.as_view(pattern_name='orders:order_list'), name='orders_root'),  # ← add this
    path('checkout/', views.checkout_view, name='checkout'),
    path('place-order/', views.place_order_view, name='place_order'),
    path('success/<str:order_id>/', views.order_success_view, name='order_success'),
    path('my-orders/', views.order_list_view, name='order_list'),
    path('my-orders/item/<int:item_id>/cancel/', views.cancel_order_item_view, name='cancel_order_item'),
    path('my-orders/<str:order_id>/', views.order_detail_view, name='order_detail'),
    path('my-orders/<str:order_id>/cancel/', views.cancel_order_view, name='cancel_order'),
    path('my-orders/<str:order_id>/return/', views.return_order_view, name='return_order'),
    path('my-orders/<str:order_id>/invoice/', views.download_invoice_view, name='download_invoice'),
]