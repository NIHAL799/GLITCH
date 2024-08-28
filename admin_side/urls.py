from django.urls import path
from . import views

app_name = 'superuser'

urlpatterns = [
    path('',views.admin_login,name='admin_login'),
    path('dashboard/',views.dashboard,name ='dashboard'),
    path('admin_logout/',views.admin_logout,name='admin_logout'),
    path('customer_view/',views.customer_view,name='customer_view'),
    path('unblock_user/<int:user_id>/',views.unblock_user,name='unblock_user'),
    path('block_user/<int:user_id>/',views.block_user,name='block_user'),
    path('sales_report/',views.sales_report,name='sales_report'),
    path('download_pdf_report/', views.download_pdf_report, name='download_pdf_report'),
    path('download_excel_report/', views.download_excel_report, name='download_excel_report'),
    path('best_selling/', views.best_selling, name='best_selling'),

]
