from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('sales/', views.sales_report_view, name='sales_report'),
    path('sales/pdf/', views.download_pdf_report_view, name='sales_pdf'),
    path('sales/excel/', views.download_excel_report_view, name='sales_excel'),
]