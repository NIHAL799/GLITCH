from . import views
from django.urls import path
 
app_name = 'wallet'

urlpatterns = [
    path('wallet_recharge/', views.wallet_recharge, name='wallet_recharge'),
    path('payment_success/', views.payment_success, name='payment_success'),
]
