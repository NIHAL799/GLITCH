from django.urls import path
from . import views

app_name = 'wishlist'

urlpatterns = [
    path('wishlist_view/', views.wishlist_view, name='wishlist_view'), 
    path('remove_from_wishlist/<int:product_id>/', views.remove_from_wishlist, name='remove_from_wishlist'), 
    path('add_to_wishlist/<int:product_id>/', views.add_to_wishlist, name='add_to_wishlist'), 

]