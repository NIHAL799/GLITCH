from django.shortcuts import redirect, render,get_object_or_404
from django.contrib import messages
from django.contrib.auth import update_session_auth_hash
from products.models import Products
from .models import UserDetails
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.views.decorators.cache import cache_control, never_cache
from .utils import generate_otp, send_otp_email
from .forms import SignUpForm,AddressForm
import time
from .models import *
from category.models import Category
from .models import UserDetails
from django.contrib.auth.hashers import check_password
from cart.models import *
from django.db.models import Count
from order.models import Order 
from django.db.models import Sum,F
from wallet.models import Wallet,Transaction
from .utils import generate_referral_code 
from decimal import Decimal


def home_page(request):
    if request.user.is_authenticated:
        cart, created = Cart.objects.get_or_create(user=request.user)
        cart_items = CartItem.objects.filter(cart=cart)
        total = sum(item.product.price * item.quantity for item in cart_items)
    else:
        cart = None
        cart_items = None
        total = None

    products = Products.objects.filter(soft_deleted=False, is_available=True).annotate(total_stock=Count('sizes__stock')).filter(total_stock__gt=0)
    categories = Category.objects.filter(is_deleted=False)
    offer_products = Products.objects.filter(soft_deleted=False, is_available=True).annotate(total_stock=Count('sizes__stock')).filter(total_stock__gt=0,category__is_offer_available=True)

    for product in products:
        product.discounted_price = product.calculate_discounted_price()
        product.save()

        
    context = {
        'products': products,
        'categories': categories,
        'cart_items': cart_items,
        'total': total,
        'offer_products':offer_products,
    }

    return render(request, 'user_side/index.html', context)



@never_cache
def user_signup(request):
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data.get('email')
            pass1 = form.cleaned_data.get('password1')
            pass2 = form.cleaned_data.get('password2')

            if UserDetails.objects.filter(email=email).exists():
                messages.error(request, 'Email is already registered')
                return redirect('user:user_signup')

            if pass1 != pass2:
                messages.error(request, 'Passwords do not match. Please try again.')
                return redirect('user:user_signup')

            form_data = form.cleaned_data.copy()
            form_data['phone'] = str(form_data['phone'])
            request.session['form_data'] = form_data
            request.session['email'] = email
            referral_coupon = form.cleaned_data.get('referral_coupon')
            request.session['referral_coupon'] = referral_coupon
            otp = generate_otp()
            send_otp_email(email, otp)
            request.session['otp'] = otp
            request.session['otp_creation_time'] = time.time()

            return redirect('user:verify_otp')

        else:
            context = {'form': form}
            messages.error(request, 'Registration failed. Please correct the errors below.')
            return render(request, 'user_side/signup.html', context)
    else:
        form = SignUpForm()
        context = {'form': form}
    return render(request, 'user_side/signup.html', context)


def verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otpEntered')
        stored_otp = request.session.get('otp')
        otp_created_time = request.session.get('otp_creation_time')
        email = request.session.get('email')
        referral_coupon = request.session.get('referral_coupon')

        if entered_otp == stored_otp and (time.time() - otp_created_time) < 300:
            form_data = request.session.get('form_data')

            if form_data:
                form = SignUpForm(form_data)
                if form.is_valid():
                    user = form.save(commit=False)
                    user.set_password(form.cleaned_data['password1'])
                    user.is_verified = True
                    user.referral_code = generate_referral_code()
                    user.save()

                    if referral_coupon:
                        try:
                            referrer = UserDetails.objects.get(referral_code=referral_coupon)

                            wallet, created = Wallet.objects.get_or_create(user=referrer)

                            reward_amount = 1000.00
                            wallet.balance += Decimal(reward_amount)

                            wallet.save()

                            Transaction.objects.create(
                                wallet=wallet,
                                amount=reward_amount,
                                description=f'Referral reward for referring {user.email}'
                            )
                        except UserDetails.DoesNotExist:
                            pass

                    del request.session['otp']
                    del request.session['otp_creation_time']
                    del request.session['form_data']
                    if 'referral_coupon' in request.session:
                        del request.session['referral_coupon']

                    messages.success(request, 'Account created successfully. Please log in.')
                    return redirect('user:user_login')
                else:
                    response_data = {'error': 'An error occurred during registration. Please try again.'}
                    del request.session['otp']
                    del request.session['otp_creation_time']
                    return JsonResponse(response_data, status=400)
            else:
                response_data = {'error': 'OTP has expired. Please request a new one.'}
                return JsonResponse(response_data, status=400)
        else:
            response_data = {'error': 'Invalid or expired OTP. Please try again.'}
            return JsonResponse(response_data, status=400)
    else:
        return render(request, 'user_side/otp_verification.html')


def resend_otp(request):
    if request.method == 'POST':
        email = request.session.get('email')
        if email:
            try:
                user = UserDetails.objects.get(email=email)
                otp = generate_otp()
                send_otp_email(user.email, otp)
                request.session['otp'] = otp
                request.session['otp_creation_time'] = time.time()
                messages.success(request, 'OTP has been re-sent to your email.')
                return redirect('user:verify_otp')
            except UserDetails.DoesNotExist:
                response_data = {'error': 'User not found.'}
                return JsonResponse(response_data, status=400)
        else:
            response_data = {'error': 'User email is not in the session'}
            return JsonResponse(response_data, status=400)
    else:
        response_data = {'error': 'Method not allowed.'}
        return JsonResponse(response_data, status=405)
    
    
@never_cache
def user_login(request): 
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')

        if not email or not password:
            messages.error(request, 'Email and password are required.')
            return redirect('user:user_login')

        try:
            user = UserDetails.objects.get(email=email)
            user = authenticate(request, email=email, password=password)
            if user:
                if not user.referral_code:
                    referral_code = generate_referral_code()
                    user.referral_code = referral_code
                    user.save()
                if user.is_active:
                    if user.is_verified:
                        login(request, user)
                        return redirect('user:home')
                    else:
                        otp = generate_otp()
                        send_otp_email(email, otp)
                        request.session['otp'] = otp
                        request.session['otp_creation_time'] = time.time()
                        request.session['email'] = email
                        request.session['password'] = password  
                        return redirect('user:login_verify_otp')
                else:
                    messages.error(request,'Your account is blocked by our team. Please contact our team.')
            else:
                messages.error(request, 'Invalid credentials.')
                return redirect('user:user_login')
        except UserDetails.DoesNotExist:
            messages.error(request, 'No account found with this email.')
            return redirect('user:user_login')
    
    return render(request, 'user_side/login.html')

def login_verify_otp(request):
    if request.method == 'POST':
        entered_otp = request.POST.get('otpEntered')
        stored_otp = request.session.get('otp')
        otp_created_time = request.session.get('otp_creation_time')
        email = request.session.get('email')
        password = request.session.get('password')

        if entered_otp == stored_otp and (time.time() - otp_created_time) < 300:
            user = authenticate(request, email=email, password=password)
            if user:
                user.is_verified = True  
                user.save()
                login(request, user)
                
                del request.session['otp']
                del request.session['otp_creation_time']
                del request.session['email']
                del request.session['password']
                messages.success(request, 'Account verified successfully.')
                return redirect('user:home')
            else:
                response_data = {'error': 'User is not authenticated.'}
                return JsonResponse(response_data, status=400)
        else:
            response_data = {'error': 'Your entered OTP doesn\'t match or OTP timeout.'}
            return JsonResponse(response_data, status=400)

    return render(request, 'user_side/login_otp_verification.html')

def forgot_password(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        user = get_object_or_404(UserDetails, email=email)
        
        otp = generate_otp()
        send_otp_email(user.email, otp)
        
        request.session['forgot_password_otp'] = otp
        
        request.session['forgot_password_otp_creation_time'] = time.time()
        request.session['forgot_password_user_id'] = user.id

        return redirect('user:forgot_password_otp')
    return render(request, 'user_side/forgot_password.html')

def forgot_password_otp(request):
    if request.method == 'POST':
        otp_entered = request.POST.get('otpEntered')
        stored_otp = request.session.get('forgot_password_otp')
        otp_creation_time = request.session['forgot_password_otp_creation_time']
        current_time = time.time()
        if otp_entered == stored_otp and (current_time - otp_creation_time) <=120:
            user_id = request.session.get('forgot_password_user_id')
            if user_id:
                del request.session['forgot_password_otp']
                del request.session['forgot_password_otp_creation_time']
                response_data = {'message': 'OTP verified successfully.'}
                return JsonResponse(response_data)
            else:
                response_data = {'error': 'User not found.'}
                return JsonResponse(response_data, status=400)
        else:
            response_data = {'error': 'OTP has expired or Invalid OTP. Please request a new one.'}
            return JsonResponse(response_data, status=400)
    else:
        return render(request, 'user_side/forgot_password_otp.html')

def forgot_password_resend_otp(request):
    if request.method == 'POST':
        user_id = request.session.get('forgot_password_user_id')
        if user_id:
            user = UserDetails.objects.get(id=user_id)
            otp = generate_otp()
            send_otp_email(user.email,otp)
            request.session['forgot_password_otp'] = otp
            request.session['forgot_password_otp_creation_time'] = time.time()
            
            response_data = {'message': 'OTP has been resent to your email.'}
            return JsonResponse(response_data)
        else:
            response_data = {'error': 'User not found.'}
            return JsonResponse(response_data, status=400)  
    response_data = {'error': 'Method not allowed.'}
    return JsonResponse(response_data, status=405)

def reset_password(request):
    if request.method == 'POST':
        password1 = request.POST.get('new_password')
        password2 = request.POST.get('confirm_password')
        user_id = request.session.get('forgot_password_user_id')
 
        try:
            user = UserDetails.objects.get(id=user_id)

            if password1 == password2:
                user.set_password(password1)
                user.save()
                messages.success(request, ' Password reset successfull.')
                del request.session['forgot_password_user_id']
                return redirect('user:user_login')
            else:
                messages.error(request, 'Passwords do not match.')
                return redirect('user:reset_password')
        except UserDetails.DoesNotExist:
            messages.error(request, 'User not found.')
            return redirect('user:user_login')
    return render(request, 'user_side/reset_password.html')
                

def signout(request):
    logout(request)
    messages.success(request, 'Logged out successfully.')
    return redirect('user:home')

@login_required
def my_account(request):
    address = Address.objects.filter(user=request.user)
    orders = Order.objects.filter(user=request.user).prefetch_related('order_item').order_by('-created_at')
    wallet, created = Wallet.objects.get_or_create(user=request.user, defaults={'balance': 0})
    try:
        transactions = wallet.transactions.all().order_by('-id')
    except AttributeError:
        transactions = [] 

    context = {
        'address' : address,
        'orders' : orders,
        'wallet' : wallet,
        'transactions' : transactions,
    }
    return render(request, 'user_side/my_account.html', context)

def edit_profile(request):
    user = UserDetails.objects.get(email=request.user.email)
    if request.method == 'POST':
        fname = request.POST.get('fname')
        lname = request.POST.get('lname')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
    
        if fname and lname and phone and email:
        
            user.email = email 
            user.phone = phone
            user.first_name = fname
            user.last_name = lname
            user.save()
        
        else:
            messages.error(request,'Please fill all details')
            return redirect('user:edit_profile')
        messages.success(request,'Details updated successfully.')
        return redirect('user:my_account')
    return render(request,'user_side/my_account.html')

def edit_password(request):
    if request.method == 'POST':
        curnt_pass = request.POST.get('current_password')
        pass1 = request.POST.get('password1')
        pass2 = request.POST.get('password2')
        user = UserDetails.objects.get(email=request.user.email)
        if check_password(curnt_pass, user.password):
            if pass1 == pass2:
                user.set_password(pass1)
                update_session_auth_hash(request,user)
                user.save()
            else:
                messages.error(request,"Password doesn't match")
                return redirect('user:edit_password')
        else:
            messages.error(request,'Your password is not matching to your old password')
            return redirect('user:edit_password')
    return render(request,'user_side/my_account.html')

def add_address(request):
    if request.method == "POST":
        form = AddressForm(request.POST)
        if form.is_valid:
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request,'Address added succesfully')
            return redirect('user:my_account')
        else :
            messages.error(request,'fill all the fields properly')
    else:
        form = AddressForm()
    return render(request, 'user_side/add_address.html', {'form': form})


def edit_address(request, address_id):
    address = get_object_or_404(Address, id=address_id, user=request.user)
    if request.method == 'POST':
        form = AddressForm(request.POST, instance=address)
        if form.is_valid():
            form.save()
            messages.success(request,'Your Address editedsuccessfully')
            return redirect('user:my_account') 
        else:
            messages.error(request,'Check the errors given below')
            return redirect('user:edit_address')
    else:
        form = AddressForm(instance=address)
    return render(request, 'user_side/edit_address.html', {'form': form})