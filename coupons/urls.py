from django.urls import path
from . import views

app_name = 'coupons'

urlpatterns = [
    path('coupon_list/',views.coupon_list,name='coupon_list'),
    path('create_coupon/',views.create_coupon,name='create_coupon'),
    path('edit_coupon/<int:coupon_id>/',views.edit_coupon,name='edit_coupon'),
    path('delete_coupon/<int:coupon_id>/',views.delete_coupon,name='delete_coupon'),
    path('activate_deactivate/<int:coupon_id>/',views.activate_deactivate,name='activate_deactivate'),
]
