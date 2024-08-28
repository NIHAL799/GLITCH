from django.urls import path
from . import views
app_name = 'product'

urlpatterns = [
#======================================= Admin Products =================================== #

    path('admin_product_list',views.admin_product_list,name='admin_product_list'),
    path('admin_add_products',views.admin_add_products,name='admin_add_products'),
    path('admin_edit_product/<int:id>',views.admin_edit_product,name='admin_edit_product'),
    path('admin_delete_product/<int:id>',views.admin_delete_product,name='admin_delete_product'),
    path("admin_product_list", views.admin_product_list, name="admin_product_list"),
    path('add_size/<int:id>/', views.add_size, name='add_size'),
    path('delete_size/<int:size_id>/', views.delete_size, name='delete_size'),
    path('manage_sizes/<int:id>',views.manage_sizes,name='manage_sizes'),
    #======================================= User Products =================================== #
    path('all_products/',views.all_products,name='all_products'),
    path('product_details/<int:id> ',views.product_details,name='product_details'),
    path('clear_filters/',views.clear_filters,name='clear_filters'),
    path('search_view/',views.search_view,name='search_view'),
    path('post_review/<int:product_id>',views.post_review,name='post_review'),
    path('admin_edit_best/<int:id>',views.admin_edit_best,name='admin_edit_best'),


]
