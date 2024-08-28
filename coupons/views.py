from django.shortcuts import render,redirect,get_object_or_404
from .models import Coupon
from django.utils import timezone
from .forms import CouponForm

    #======================================= Admin Coupon management =================================== #


def coupon_list(request):
    if 'username' not in request.session:
        return redirect('superuser:admin_login')
    coupons = Coupon.objects.all().order_by('-id')
    current_time = timezone.now()
    for coupon in coupons:

        if coupon.is_active and coupon.is_expired():
            coupon.is_active = False
            coupon.save()
    return render(request, 'admin_side/coupon_list.html', {'coupons': coupons})

def create_coupon(request):
    if 'username' not in request.session:
        return redirect('superuser:admin_login')
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            instance = form.save()  
            return redirect('coupons:coupon_list')  
        else:
            pass
    else:
        form = CouponForm()
    return render(request, 'admin_side/create_coupon.html', {'form': form})

def edit_coupon(request, coupon_id):
    if 'username' not in request.session:
        return redirect('superuser:admin_login')
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            instance = form.save()  
            return redirect('coupons:coupon_list')  
        else:
            pass  
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'admin_side/coupon_edit.html', {'form': form})

def delete_coupon(request, coupon_id):
    if 'username' not in request.session:
        return redirect('superuser:admin_login')
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if request.method == 'POST':
        coupon.delete()
        return redirect('coupons:coupon_list')
    
def activate_deactivate(request,coupon_id):
    if 'username' not in request.session:
        return redirect('superuser:admin_login')
    coupon = get_object_or_404(Coupon, id=coupon_id)
    if coupon.is_active:
        coupon.is_active = False
        coupon.save()
    else:
        coupon.is_active = True
        coupon.save()
    return redirect('coupons:coupon_list')