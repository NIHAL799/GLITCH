from django.urls import path
from . import views
app_name = 'user'


urlpatterns = [

#======================================= User management =================================== #
    path("", views.home_page, name="home"),
    path('login/',views.user_login,name='user_login'),
    path('signup/',views.user_signup,name='user_signup'),
    path('signout/',views.signout,name='signout'),
    path('verify_otp/',views.verify_otp,name='verify_otp'),
    path('resend_otp/',views.resend_otp,name='resend_otp'),
    path('forgot_password/',views.forgot_password,name='forgot_password'),
    path('forgot_password_otp/',views.forgot_password_otp,name='forgot_password_otp'),
    path('forgot_password_resend_otp/',views.forgot_password_resend_otp,name='forgot_password_resend_otp'),
    path('reset_password/',views.reset_password,name='reset_password'),
    path('login_verify_otp/',views.login_verify_otp,name='login_verify_otp'),
    path('my_account/',views.my_account,name='my_account'),
    path('edit_profile/',views.edit_profile,name='edit_profile'),
    path('add_address/',views.add_address,name='add_address'),
    path('edit_address/<int:address_id>/',views.edit_address,name='edit_address'),
    path('edit_password/',views.edit_password,name='edit_password'),


]
