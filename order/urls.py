from django.urls import path
from . import views
app_name = 'order'


urlpatterns = [   
#======================================= Admin Order =================================== #

    path('update_order_status/', views.update_order_status, name='update_order_status'),
    path('order_list_admin/', views.order_list_admin, name='order_list_admin'),
    path('order_detail_admin/<int:order_id>/', views.order_detail_admin, name='order_detail_admin'),
    path('accept_return/<int:item_id>/', views.accept_return, name='accept_return'),
    path('reject_return/<int:item_id>/', views.reject_return, name='reject_return'),
#======================================= User Order =================================== #
    path('order_detail/<int:order_id>', views.order_detail, name='order_detail'),
    path('checkout/', views.checkout, name='checkout'),
    path('cancel_order/<int:item_id>/', views.cancel_order, name='cancel_order'),
    path('order_confirmation/<int:order_id>', views.order_confirmation, name='order_confirmation'),
    path('add_address_checkout',views.add_address_checkout,name='add_address_checkout'),
    path('apply_coupon/', views.apply_coupon, name='apply_coupon'),
    path('return_request/<int:item_id>/', views.return_request, name='return_request'),
    path('payment_success/', views.payment_success, name='payment_success'),
    path('retry_payment/<int:order_id>', views.retry_payment, name='retry_payment'),
    path('retry_payment_success/', views.retry_payment_success, name='retry_payment_success'),
    path('download_invoice/<int:order_id>', views.download_invoice, name='download_invoice'),

    



]