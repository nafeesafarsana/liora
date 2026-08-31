from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Auth
    path('login/', views.admin_login_view, name='login'),
    path('logout/', views.admin_logout_view, name='logout'),

    # Dashboard
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # User Management
    path('users/', views.user_management_view, name='user_management'),
    path('users/<int:user_id>/toggle-block/', views.toggle_block_user_view, name='toggle_block_user'),

    # Category Management
    path('categories/', views.category_list_view, name='category_list'),
    path('categories/add/', views.category_add_view, name='category_add'),
    path('categories/<int:pk>/edit/', views.category_edit_view, name='category_edit'),
    path('categories/<int:pk>/delete/', views.category_delete_view, name='category_delete'),
    path('categories/<int:pk>/toggle-list/', views.category_toggle_list_view, name='category_toggle_list'),

    # Product Management
    path('products/', views.product_list_view, name='product_list'),
    path('products/add/', views.product_add_view, name='product_add'),
    path('products/<int:pk>/edit/', views.product_edit_view, name='product_edit'),
    path('products/<int:pk>/delete/', views.product_delete_view, name='product_delete'),
    path('products/<int:pk>/toggle-list/', views.product_toggle_list_view, name='product_toggle_list'),
    path('products/images/<int:pk>/delete/', views.product_image_delete_view, name='product_image_delete'),

    # Order Management (Admin)
    path('orders/', views.admin_order_list_view, name='admin_order_list'),
    path('orders/<str:order_id>/', views.admin_order_detail_view, name='admin_order_detail'),

    # Inventory / Stock Management
    path('inventory/', views.inventory_view, name='inventory'),
    path('inventory/<int:pk>/update-stock/', views.update_stock_view, name='update_stock'),
     # Coupons
    path('coupons/', views.coupon_list_view, name='coupon_list'),
    path('coupons/add/', views.coupon_add_view, name='coupon_add'),
    path('coupons/<int:pk>/delete/', views.coupon_delete_view, name='coupon_delete'),
    path('coupons/<int:pk>/toggle/', views.coupon_toggle_view, name='coupon_toggle'),

    # Offers
    path('offers/', views.offer_list_view, name='offer_list'),
    path('offers/add/', views.offer_add_view, name='offer_add'),
    path('offers/<int:pk>/delete/', views.offer_delete_view, name='offer_delete'),
    path('offers/<int:pk>/toggle/', views.offer_toggle_view, name='offer_toggle'),

    # Returns
    path('returns/', views.return_requests_view, name='return_requests'),
    path('returns/<str:order_id>/confirm-refund/', views.confirm_refund_view, name='confirm_refund'),
    # Reports
    path('reports/sales/', views.sales_report_redirect, name='sales_report'),
]