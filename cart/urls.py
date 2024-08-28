from django.urls import path
from . import views
app_name = 'cart'

urlpatterns = [
    path('add_to_cart/<int:product_id>/', views.add_to_cart, name='add_to_cart'),
    path('cart_detail/', views.cart_detail, name='cart_detail'),
    path('remove_from_cart/<int:cart_item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('update_cart_item/<int:id>/', views.update_cart_item, name='update_cart_item'),
    path('clear_cart/', views.clear_cart, name='clear_cart'),


]