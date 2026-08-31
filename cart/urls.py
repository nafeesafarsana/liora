from django.urls import path
from . import views

app_name = 'cart'

urlpatterns = [
    path('', views.cart_detail_view, name='cart_detail'),
    path('add/<int:product_id>/', views.add_to_cart_view, name='add_to_cart'),
    path('remove/<int:item_id>/', views.remove_from_cart_view, name='remove_from_cart'),
    path('update/<int:item_id>/', views.update_cart_quantity_view, name='update_quantity'),
    path('wishlist/', views.wishlist_view, name='wishlist'),
    path('wishlist/toggle/<int:product_id>/', views.wishlist_toggle_view, name='wishlist_toggle'),
    path('wishlist/remove/<int:product_id>/', views.wishlist_remove_view, name='wishlist_remove'),
]