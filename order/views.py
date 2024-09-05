from datetime import timezone
from django.shortcuts import render, redirect,get_object_or_404,HttpResponse
from django.urls import reverse
from products.models import Products, ProductSize
from django.contrib import messages
from user.models import Address
from django.db import transaction
from cart.models import CartItem,Cart
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from . models import *
from django.contrib.auth import get_user_model
from coupons.models import Coupon,CouponUsage
from user.forms import AddressForm
from django.db.models import Q,Sum,F
from django.core.exceptions import FieldError
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from wallet.models import Wallet,Transaction
import json
from django.utils.functional import SimpleLazyObject
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage

from decimal import Decimal
from fpdf import FPDF
from io import BytesIO

from django.contrib.sites.shortcuts import get_current_site
from django.conf import settings
import razorpay 

razorpay_client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

@login_required
@csrf_exempt
def checkout(request):
    user = request.user
    delivery_charge = 110
    user_id = user.id

    try:
        cart = Cart.objects.get(user=user)
        cart_items = CartItem.objects.filter(cart=cart)
        subtoatal = sum(item.product.discounted_price * item.quantity for item in cart_items)
        if not cart_items.exists():
            messages.error(request, "Your cart is empty.")
            return redirect('cart:cart_detail')

        out_of_stock_items = [
            item.product.product_name for item in cart_items
            if ProductSize.objects.filter(product=item.product, size=item.size, stock__lt=item.quantity).exists()
        ]
        if out_of_stock_items:
            messages.error(request, f"Insufficient stock for the following products: {', '.join(out_of_stock_items)}.")
            return redirect('cart:cart_detail')

        total_amount = sum(Decimal(item.product.discounted_price) * Decimal(item.quantity) for item in cart_items)
        discount_percentage = request.session.get('discount', 0)
        discount_amount = total_amount * (Decimal(discount_percentage) / Decimal(100)) * 100
        final_total = (total_amount - discount_amount) + delivery_charge
        coupon_code = request.session.get('coupon_code', '')
        coupon = Coupon.objects.filter(code=coupon_code).first()

        if request.method == 'POST':
            selected_address_id = request.POST.get('selected_address')
            
            order_notes = request.POST.get('order_notes', '')
            payment_method = request.POST.get('payment_method')

            if not selected_address_id:
                messages.error(request, "Please select an address.")
                return redirect('order:checkout')

            address = Address.objects.filter(id=selected_address_id, user=user).first()
            if not address:
                messages.error(request, "Selected address does not exist.")
                return redirect('order:checkout')
            
            if payment_method == 'razorpay':
                request.session['selected_address_id'] = selected_address_id
                print('selected_address_id',selected_address_id)
                request.session['order_notes'] = order_notes
                notes = {'order-type':'basic order from the website'}
                receipt_maker = 'text'
                razorpay_order = razorpay_client.order.create(dict(
                    amount = int(final_total * 100),
                    currency = 'INR',
                    notes = notes,
                    receipt = receipt_maker,
                    payment_capture  = '1'
                ))
                
                callback_url = f'http://127.0.0.1:8000/order/payment_success/?address_id={selected_address_id}&user_id={user_id}'
                print('user_iddddddddddd',user_id)
                context={
                    'key' : settings.RAZORPAY_KEY_ID,
                    'amount': int(final_total * 100),
                    'razorpay_order_id':razorpay_order['id'],
                    'callback_url':callback_url,
                    'user':user
                }    
                return render(request,'user_side/razorpay.html',context)


            
            elif payment_method == 'wallet':
                wallet = Wallet.objects.get(user=user)
                wallet_balance = wallet.balance
                if wallet_balance < final_total:
                    messages.error(request, f'Your wallet balance is {wallet_balance}. Add {float(final_total) - float(wallet_balance)} to the wallet or choose another payment method.')
                    return redirect('order:checkout')

                with transaction.atomic():
                    order = Order.objects.create(
                        user=user,
                        address=address,
                        order_notes=order_notes,
                        payment_method=payment_method,
                        total_amount=total_amount,
                        payable_amount=final_total,
                        payment_status='paid',
                        coupon=coupon,
                    )

                    for item in cart_items:
                        try:
                            product_size = ProductSize.objects.select_for_update().get(product=item.product, size=item.size)
                            product = Products.objects.select_for_update().get(id=item.product.id)
                            if product_size.stock < item.quantity:
                                messages.error(request, f"Insufficient stock for product {product_size.product.product_name}.")
                                transaction.set_rollback(True)
                                return redirect('order:checkout')

                            item_total_price = item.product.price * item.quantity
                            item_discount_amount = (Decimal(item_total_price) / Decimal(total_amount)) * discount_amount
                            payment_after_discount = Decimal(item_total_price) - item_discount_amount
                            OrderItem.objects.create(
                                order=order,
                                product=product_size.product,
                                product_size=product_size,
                                quantity=item.quantity,
                                price=product_size.product.price,
                                payment_after_discount=payment_after_discount,
                            )
                            product_size.stock -= item.quantity

                            product_size.save()
                            product.popularity += item.quantity
                            product.save()

                        except ProductSize.DoesNotExist:
                            messages.error(request, "Product size not found.")
                            transaction.set_rollback(True)
                            return redirect('order:checkout')

                    if coupon_code:
                        try:
                            coupon = Coupon.objects.get(code=coupon_code)
                            if coupon.is_active and not coupon.is_expired():
                                coupon.usage_count += 1
                                coupon.save()

                                user_coupon_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
                                if user_coupon_usage < coupon.limit_per_user:
                                    CouponUsage.objects.create(coupon=coupon, user=user)
                                else:
                                    messages.error(request, "You have exceeded the usage limit for this coupon.")
                                    transaction.set_rollback(True)
                                    return redirect('order:checkout')

                        except Coupon.DoesNotExist:
                            messages.error(request, "Invalid coupon code.")
                            transaction.set_rollback(True)
                            return redirect('order:checkout')

                    wallet.balance -= final_total
                    wallet.save()

                    Transaction.objects.create(
                        wallet=wallet,
                        amount=final_total,
                        description=f'Payment using wallet for order {order.id}',
                    )

                    cart_items.delete()
                    if 'discount' in request.session:
                        del request.session['discount']
                        del request.session['coupon_code']

                    messages.success(request, 'Your order has been placed successfully!')
                    return redirect('order:order_confirmation', order_id=order.id)

            elif payment_method == 'cod':
                if final_total < 20000:
                    with transaction.atomic():
                        order = Order.objects.create(
                            user=user,
                            address=address,
                            order_notes=order_notes,
                            payment_method=payment_method,
                            total_amount=total_amount,
                            payable_amount=final_total,
                            coupon=coupon,
                        )

                        for item in cart_items:
                            try:
                                product_size = ProductSize.objects.select_for_update().get(product=item.product, size=item.size)
                                if product_size.stock < item.quantity:
                                    messages.error(request, f"Insufficient stock for product {product_size.product.product_name}.")
                                    transaction.set_rollback(True)
                                    return redirect('order:checkout')

                                item_total_price = item.product.price * item.quantity
                                item_discount_amount = (item_total_price / total_amount) * discount_amount
                                payment_after_discount = item_total_price - item_discount_amount

                                OrderItem.objects.create(
                                    order=order,
                                    product=product_size.product,
                                    product_size=product_size,
                                    quantity=item.quantity,
                                    price=product_size.product.price,
                                    discount_amount=item_discount_amount,
                                    payment_after_discount=payment_after_discount,
                                )
                                product_size.stock -= item.quantity
                                product_size.save()

                            except ProductSize.DoesNotExist:
                                messages.error(request, "Product size not found.")
                                transaction.set_rollback(True)
                                return redirect('order:checkout')

                        if coupon_code:
                            try:
                                coupon = Coupon.objects.get(code=coupon_code)
                                if coupon.is_active and not coupon.is_expired():
                                    coupon.usage_count += 1
                                    coupon.save()

                                    user_coupon_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
                                    if user_coupon_usage < coupon.limit_per_user:
                                        CouponUsage.objects.create(coupon=coupon, user=user)
                                    else:
                                        messages.error(request, "You have exceeded the usage limit for this coupon.")
                                        transaction.set_rollback(True)
                                        return redirect('order:checkout')

                            except Coupon.DoesNotExist:
                                messages.error(request, "Invalid coupon code.")
                                transaction.set_rollback(True)
                                return redirect('order:checkout')

                        cart_items.delete()
                        if 'discount' in request.session:
                            del request.session['discount']
                            del request.session['coupon_code']

                        messages.success(request, 'Your order has been placed successfully!')
                        return redirect('order:order_confirmation', order_id=order.id)
                else:
                    messages.info(request,'Cash on Delivery order is not allowed for payment above 20000.. Choose any other payment option')
                    return redirect('order:checkout')

            else:
                messages.error(request, 'Please select a payment method')
                return redirect('order:checkout')

        context = {
            'user_addresses': Address.objects.filter(user=user),
            'cart_items': cart_items,
            'total': total_amount, 
            'final_total': final_total,
            'discount': discount_amount,
            'coupon_code': coupon_code,
            'available_coupons': Coupon.objects.filter(is_active=True, expiry_date__gte=timezone.now()),
            'subtoatal':subtoatal,
            'delivery_charge':delivery_charge,
        }

        return render(request, 'user_side/checkout.html', context)

    except Exception as e:
        messages.error(request, f"An error occurred: {str(e)}")
        return redirect('order:checkout')



@login_required
def apply_coupon(request):
    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip()
        if coupon_code:
            try:
                coupon = Coupon.objects.get(code=coupon_code)
                
                if not coupon.is_active:
                    messages.error(request, "This coupon is not active.")
                    return redirect('order:checkout')

                if coupon.is_expired():
                    messages.error(request, "Coupon code has expired.")
                    return redirect('order:checkout')

                if coupon.usage_count >= coupon.overall_usage_limit:
                    messages.error(request, "Coupon code usage limit reached.")
                    return redirect('order:checkout')

                user_coupon_usage = CouponUsage.objects.filter(coupon=coupon, user=request.user).count()
                if user_coupon_usage >= coupon.limit_per_user:
                    messages.error(request, "You have exceeded the usage limit for this coupon.")
                    return redirect('order:checkout')

                cart = get_object_or_404(Cart, user=request.user)
                cart_items = CartItem.objects.filter(cart=cart)
                total_amount = sum(item.product.price * item.quantity for item in cart_items)

                if total_amount < coupon.minimum_order_amount:
                    messages.error(request, f"Minimum order amount of {coupon.minimum_order_amount} is required to use this coupon.")
                    return redirect('order:checkout')

                if coupon.maximum_order_amount and total_amount > coupon.maximum_order_amount:
                    messages.error(request, f"Order amount exceeds the maximum limit of {coupon.maximum_order_amount} for this coupon.")
                    return redirect('order:checkout')

                request.session['discount'] = float(coupon.offer_percentage / 100)
                request.session['coupon_code'] = coupon_code
                messages.success(request, f"Coupon applied! You saved {coupon.offer_percentage}%.")  
            except Coupon.DoesNotExist:
                messages.error(request, "Invalid coupon code.")
        return redirect('order:checkout')
    return redirect('order:checkout')



def order_confirmation(request,order_id):
    order = Order.objects.get(id=order_id)
    context ={
        'order':order
    }
    return render(request,'user_side/order_confirmed.html',context)


@login_required
def cancel_order(request, item_id):
    order_item = get_object_or_404(OrderItem, id=item_id)
    
    if order_item.status == 'confirmed':
        order_item.status = 'cancelled'
        order_item.save()

        order = order_item.order 
        total_discount_amount = order_item.discount_amount
        item_price_before_discount = order_item.price * order_item.quantity
        proportional_discount = (total_discount_amount / order.total_amount) * item_price_before_discount
        item_refund_amount = item_price_before_discount - proportional_discount

        product_size = order_item.product_size
        product_size.stock += order_item.quantity
        product_size.save()
        order_item.product.popularity -= order_item.quantity
        order_item.save()

        if order.payment_status == Order.PaymentStatus.PAID:
            wallet = Wallet.objects.get(user=request.user)
            wallet.balance += item_refund_amount
            wallet.save()

            Transaction.objects.create(
                wallet=wallet,
                amount=item_refund_amount,
                description=f'Refund for order item {order_item.id} of order {order.id}',
            )
            messages.success(request, 'Order item has been cancelled successfully. The amount has been credited to your wallet.')
        else:
            messages.success(request, 'Order item has been cancelled successfully.')
    else:
        messages.error(request, 'Order item cannot be cancelled.')
    
    return redirect('user:my_account')



def order_list_admin(request):
    user = request.user
    print(user)
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    elif not user.is_superuser:
        return redirect('superuser:admin_login')

    search_query = request.GET.get('search', '')
    sort_by = request.GET.get('sort_by', '-id')  
    orders = Order.objects.all().order_by('-created_at')
    if search_query:
        orders = orders.filter(
            Q(address__first_name__icontains=search_query) |
            Q(address__last_name__icontains=search_query)
        )
    try:
        orders = orders.order_by(sort_by)
    except FieldError:
        orders = orders.order_by('-id')

    paginator = Paginator(orders, 10)  
    page_number = request.GET.get('page', 1)

    try:
        orders = paginator.page(page_number)
    except PageNotAnInteger:
        orders = paginator.page(1)
    except EmptyPage:
        orders = paginator.page(paginator.num_pages)

    context = {
        'orders': orders,
    }
    return render(request, 'admin_side/orders.html', context)

def update_order_status(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('superuser:admin_login')
    elif not user.is_superuser:
        return redirect('superuser:admin_login')

    if request.method == 'POST':
        item_id = request.POST.get('OrderID')
        status = request.POST.get('status')

        if not item_id or not status:
            messages.error(request, 'Invalid data')
            return redirect('order:order_detail_admin',order_id = item_id)

        try:
            item = get_object_or_404(OrderItem, id=item_id)
            old_status = item.status

            valid_transitions = {
                'confirmed': ['shipped', 'cancelled'],
                'shipped': ['delivered', 'returned'],
                'delivered': ['returned'],
                'cancelled': [],
                'returned': ['refunded'],
                'refunded': [],
                'return_requested': ['return_accepted', 'return_rejected'],
                'return_accepted': ['returned'],
                'return_rejected': [],
            }
            

            if status not in valid_transitions[old_status]:
                messages.error(request, f"Cannot change status from {old_status} to {status}")
                return redirect('order:order_detail_admin', order_id=item.order.id)

            item.status = status
            item.save()

            if status == 'returned':
                product_size = get_object_or_404(ProductSize, product=item.product, size=item.product_size.size)
                product_size.stock += item.quantity
                product_size.save()

                user = item.order.user
                wallet = Wallet.objects.get(user=user)
                refund_amount = item.price * item.quantity
                wallet.balance += refund_amount
                wallet.save()

                Transaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    description=f'Refund for returned order item {item.id}',
                )

            elif status == 'cancelled':
                product_size = get_object_or_404(ProductSize, product=item.product, size=item.product_size.size)
                product_size.stock += item.quantity
                product_size.save()

                order = item.order
                
                refund_amount = item.price * item.quantity

                user = item.order.user
                wallet = Wallet.objects.get(user=user)
                wallet.balance += refund_amount
                wallet.save()

                Transaction.objects.create(
                    wallet=wallet,
                    amount=refund_amount,
                    description=f'Refund for cancelled order item {item.id}',
                )

            messages.success(request, 'Order status updated successfully')
            return redirect('order:order_detail_admin', order_id=item.order.id)
        except OrderItem.DoesNotExist:
            messages.error(request, 'Item not found')
            return redirect('order:order_list_admin')
        except Wallet.DoesNotExist:
            messages.error(request, 'User wallet not found')
            return redirect('order:order_list_admin')
        except Exception as e:
            messages.error(request, f'An error occurred: {e}')
            return redirect('order:order_list_admin')

    return redirect('order:order_list_admin')

def order_detail(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    context = {
        'order': order, 
        'order_items': order_items,
    }
    return render(request, 'user_side/orders_detail.html', context)

def add_address_checkout(request):
    if request.method == 'POST':
        form = AddressForm(request.POST)
        if form.is_valid:
            address = form.save(commit=False)
            address.user = request.user
            address.save()
            messages.success(request,'Address added successfully')
            return redirect('order:checkout')
        else:
            messages.error(request,'fill all the fields')
    else:
        form = AddressForm()
    return render(request, 'user_side/add_address.html', {'form': form})


def order_detail_admin(request, order_id):
    user = request.user
    if not user.is_authenticated:
        return redirect('superuser:admin_login')
    elif not user.is_superuser:
        return redirect('superuser:admin_login')

    order = get_object_or_404(Order, id=order_id)
    order_items = OrderItem.objects.filter(order=order)
    total_amount = sum(item.price * item.quantity for item in order_items)
    
    context = {
        'order': order,
        'order_items': order_items,
        'total_amount': total_amount,
        'status_choices': OrderItem.STATUS_CHOICES,
    }
    return render(request, 'admin_side/order_details.html', context)

def return_request(request, item_id):
    if request.method == 'GET':
        item = get_object_or_404(OrderItem, id=item_id)
        item.status = 'return_requested'
        item.save()
        messages.success(request, 'Return request submitted successfully')
    return redirect('order:order_detail', order_id=item.order.id)

def accept_return(request, item_id):

    user = request.user
    if not user.is_authenticated:
        return redirect('superuser:admin_login')
    elif not user.is_superuser:
        return redirect('superuser:admin_login')

    item = get_object_or_404(OrderItem, id=item_id)

    item.status = 'return_accepted'
    item.save()
    messages.success(request, 'Return accepted successfully')
    return redirect('order:order_detail_admin', order_id=item.order.id)

def reject_return(request, item_id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    item = get_object_or_404(OrderItem, id=item_id)
    item.status = 'return_rejected'
    item.save()
    messages.success(request, 'Return rejected successfully')
    return redirect('order:order_detail_admin', order_id=item.order.id)

import traceback


@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        print('Request GET data:', request.GET)
        user_id = request.GET.get('amp;user_id')
        print('user_iddddddddddd',user_id)
        user = UserDetails.objects.get(id=user_id)

        try:
            razorpay_payment_id = request.POST.get('razorpay_payment_id')
            razorpay_order_id = request.POST.get('razorpay_order_id')
            razorpay_signature = request.POST.get('razorpay_signature')

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            try:
                if razorpay_payment_id and razorpay_order_id and razorpay_signature:
                    client.utility.verify_payment_signature({
                        'razorpay_order_id': razorpay_order_id,
                        'razorpay_payment_id': razorpay_payment_id,
                        'razorpay_signature': razorpay_signature
                    })
                    payment_status = 'paid'
                else:
                    payment_status = 'failed'
            except razorpay.errors.SignatureVerificationError:
                return JsonResponse({'status': 'failure'}, status=400)

      
            selected_address_id = request.GET.get('address_id')
            print('selected_address_id',selected_address_id)
            order_notes = request.session.get('order_notes')
            address = Address.objects.filter(id=selected_address_id, user=user).first()

            cart = Cart.objects.get(user=user)
            cart_items = CartItem.objects.filter(cart=cart)
            subtoatal = sum(item.product.price * item.quantity for item in cart_items)
            if not cart_items.exists():
                messages.error(request, "Your cart is empty.")
                return redirect('cart:cart_detail')

            out_of_stock_items = [
                item.product.product_name for item in cart_items
                if ProductSize.objects.filter(product=item.product, size=item.size, stock__lt=item.quantity).exists()
            ]
            if out_of_stock_items:
                messages.error(request, f"Insufficient stock for the following products: {', '.join(out_of_stock_items)}.")
                return redirect('cart:cart_detail')

            total_amount = sum(Decimal(item.product.discounted_price) * Decimal(item.quantity) for item in cart_items)
            discount_percentage = request.session.get('discount', 0)
            discount_amount = total_amount * (Decimal(discount_percentage) / Decimal(100))
            final_total = total_amount - discount_amount
            coupon_code = request.session.get('coupon_code', '')
            coupon = Coupon.objects.filter(code=coupon_code).first()
            with transaction.atomic():
                order = Order.objects.create(
                    user=user,
                    address=address,
                    order_notes=order_notes,
                    payment_method='razorpay',
                    total_amount=total_amount,
                    payable_amount=final_total,
                    razorpay_order_id=razorpay_order_id,
                    payment_status = payment_status,
                    coupon=coupon,
                )
                for item in cart_items:
                    try:
                        product_size = ProductSize.objects.select_for_update().get(product=item.product, size=item.size)
                        if product_size.stock < item.quantity:
                            messages.error(request, f"Insufficient stock for product {product_size.product.product_name}.")
                            transaction.set_rollback(True)
                            return redirect('order:checkout')
                        item_total_price = item.product.price * item.quantity
                        item_discount_amount = (item_total_price / total_amount) * discount_amount
                        payment_after_discount = item_total_price - item_discount_amount
                        OrderItem.objects.create(
                            order=order,
                            product=product_size.product,
                            product_size=product_size,
                            quantity=item.quantity,
                            price=product_size.product.price,
                            discount_amount=item_discount_amount,
                            payment_after_discount=payment_after_discount,
                            
                        )
                        product_size.stock -= item.quantity
                        product_size.save()
                    except ProductSize.DoesNotExist:
                        messages.error(request, "Product size not found.")
                        transaction.set_rollback(True)
                        return redirect('order:checkout')
                if coupon_code:
                    try:
                        coupon = Coupon.objects.get(code=coupon_code)
                        if coupon.is_active and not coupon.is_expired():
                            coupon.usage_count += 1
                            coupon.save()
                            user_coupon_usage = CouponUsage.objects.filter(coupon=coupon, user=user).count()
                            if user_coupon_usage < coupon.limit_per_user:
                                CouponUsage.objects.create(coupon=coupon, user=user)
                            else:
                                messages.error(request, "You have exceeded the usage limit for this coupon.")
                                transaction.set_rollback(True)
                                return redirect('order:checkout')
                    except Coupon.DoesNotExist:
                        messages.error(request, "Invalid coupon code.")
                        transaction.set_rollback(True)
                        return redirect('order:checkout')
                cart_items.delete()
                if 'discount' in request.session:
                    del request.session['discount']
                    del request.session['coupon_code']
                if 'selected_address' in request.session:
                    del request.session['selected_address']
                if 'order_notes' in request.session:
                    del request.session['order_notes']
            context ={
                'order_id': order.id,
                'payment_id':razorpay_payment_id,
                'order':order
            }
            return render(request, "user_side/order_confirmed.html", context)

        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
        except razorpay.errors.SignatureVerificationError as e:
            return JsonResponse({'success': False, 'message': str(e)}, status=400)
        except Exception as e:
            print(traceback.format_exc()) 

            return JsonResponse({'success': False, 'message': 'An unexpected error occurred.'}, status=500)
    context = {
        'razorpay_key' : settings.RAZORPAY_KEY_ID,
        'total_amount' : final_total,
        'order':order,
    }
    return render(request,'user_side/razorpay.html',context)


def retry_payment(request,order_id):

    order = Order.objects.get(id=order_id)
    final_total = order.payable_amount
    user = request.user
    

    callback_url = 'http://127.0.0.1:8000/order/retry_payment_success/'

    razorpay_order = razorpay_client.order.create({
        'amount' :int(order.payable_amount * 100),
        'currency' : 'INR',
        'payment_capture'  : '1'
    })
    request.session['order_id'] = order.id

    order.razorpay_order_id = razorpay_order['id']
    order.save()
    context={
        'key' : settings.RAZORPAY_KEY_ID,
        'amount': int(final_total * 100),
        'razorpay_order_id':razorpay_order['id'],
        'callback_url':callback_url,
        'user':user
    }    
    return render(request,'user_side/razorpay.html',context)


@csrf_exempt
def retry_payment_success(request):
    if request.method == "POST":
        user = request.user
        order_id = request.session.get('order_id')
        order = Order.objects.get(id=order_id) 
        final_total = order.payable_amount
        try:
            razorpay_payment_id = request.POST.get('razorpay_payment_id', None)
            razorpay_order_id = request.POST.get('razorpay_order_id', None)
            razorpay_signature = request.POST.get('razorpay_signature', None)

            client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
            try:
                if razorpay_payment_id and razorpay_order_id and razorpay_signature:
                    client.utility.verify_payment_signature({
                        'razorpay_order_id': razorpay_order_id,
                        'razorpay_payment_id': razorpay_payment_id,
                        'razorpay_signature': razorpay_signature
                    })
                    order.payment_status = 'paid'
                    order.save()
                else:
                    order.payment_status = 'failed'
                    order.save()
            except razorpay.errors.SignatureVerificationError:
                return JsonResponse({'status': 'failure'}, status=400)
            context ={
                'order_id': order,
                'payment_id':razorpay_payment_id,
                'order':order
            }
            return render(request, "user_side/order_confirmed.html", context)
        except json.JSONDecodeError:
            return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
        
    context = {
        'razorpay_key' : settings.RAZORPAY_KEY_ID,
        'total_amount' : final_total,
        'order':order,
    }
    return render(request,'user_side/razorpay.html',context)

class InvoicePDF(FPDF):
    def header(self):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, 'Invoice', 0, 1, 'C')

    def footer(self):
        self.set_y(-15)
        self.set_font('Arial', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

    def chapter_title(self, title):
        self.set_font('Arial', 'B', 12)
        self.cell(0, 10, title, 0, 1, 'L')
        self.ln(10)

    def chapter_body(self, body):
        self.set_font('Arial', '', 12)
        self.multi_cell(0, 10, body)
        self.ln()

    
    def add_order_items(self, items):
        self.set_font('Arial', 'B', 10)
        self.cell(60, 10, 'Product', 1)
        self.cell(30, 10, 'Price', 1)
        self.cell(20, 10, 'Quantity', 1)
        self.cell(30, 10, 'Subtotal', 1)
        self.ln()

        self.set_font('Arial', '', 10)
        for item in items:
            self.cell(60, 10, item.product.product_name, 1)
            self.cell(30, 10, f"${item.price}", 1)
            self.cell(20, 10, str(item.quantity), 1)
            self.cell(30, 10, f"${item.payment_after_discount * item.quantity}", 1)
            self.ln()


@login_required
def download_invoice(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    items = order.order_item.all()  

    pdf = InvoicePDF()
    pdf.add_page()
    pdf.chapter_title(f'Invoice for Order {order.id}')
    pdf.chapter_body(f'Order Date: {order.created_at.strftime("%Y-%m-%d")}\n'
                     f'Address: {order.address.street_address}, {order.address.apartment_address}, {order.address.city}, {order.address.country}, {order.address.postcode}\n'
                     f'Order Status: {order.payment_status}\n'
                     f'Total Amount: ${order.total_amount}\n'
                     f'Amount After Discount: ${order.payable_amount}\n'
                     f'Payment Method: {order.payment_method}')

    pdf.add_order_items(items)

    pdf_output = BytesIO()
    pdf_content = pdf.output(dest='S').encode('latin1')  
    pdf_output.write(pdf_content)


    response = HttpResponse(pdf_output.getvalue(), content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice_{order.id}.pdf"'
    return response
