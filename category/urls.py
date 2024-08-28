from django.urls import path
from . import views

app_name = 'category'

urlpatterns = [
    #======================================= Admin Category =================================== #
    path('', views.category_list, name='category_list'), 
    path('add_category/', views.add_category, name='add_category'),  
    path('category_edit/<int:id>/', views.category_edit, name='category_edit'),  
    path('category_soft_delete/<int:id>/', views.category_soft_delete, name='category_soft_delete'),
    #======================================= User Category =================================== #  
    path('shop_by_category/<str:category_name>/', views.shop_by_category, name='shop_by_category'),  

    # path('category_delete/<int:id>/', views.category_delete, name='category_delete'),  
]