
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from .models import Cart, CartItem
from products.models import Products,ProductSize
from django.contrib import messages


# def _cart_id(request):
#     cart = request.session.session_key
#     if not cart:
#         cart = request.session.create()
#     return cart

    #======================================= User cart management =================================== #
@login_required
def add_to_cart(request, product_id):
    user = request.user
    product = get_object_or_404(Products, id=product_id)
    size = request.POST.get('size')
    quantity = int(request.POST.get('qtybutton', 1))

    

    
    if not size:
        messages.error(request, "Please select a size.")
        return redirect('product:product_details', id=product_id)

    try:
        size = int(size)
    except ValueError:
        messages.error(request, "Invalid size selected.")
        return redirect('product:product_details', id=product_id)

    try:
        product_size = ProductSize.objects.get(product=product, size=size)
        available_stock = product_size.stock
    except ProductSize.DoesNotExist:
        messages.info(request, "Selected size is not available.")
        return redirect('product:product_details', id=product_id)

    if quantity > available_stock:
        messages.info(request, f"Only {available_stock} in stock.")
        return redirect('product:product_details', id=product_id)

    cart, created = Cart.objects.get_or_create(user=user)

    if created:
        cart.user = user
        cart.save()

    try:
        cart_item = CartItem.objects.get(cart=cart, product=product, user=user, size=size)
        new_quantity = cart_item.quantity + quantity
        if new_quantity > available_stock:
            messages.info(request, f"Only {available_stock} in stock.")
            return redirect('cart:cart_detail')
        cart_item.quantity = new_quantity
        cart_item.save()
        messages.success(request, "Item quantity updated in cart.")
    except CartItem.DoesNotExist:
        CartItem.objects.create(
            cart=cart,
            product=product,
            user=user,
            quantity=quantity,
            size=size
        )
        messages.success(request, "Item added to cart successfully.")

    return redirect('cart:cart_detail')

@login_required
def cart_detail(request):

    cart = get_object_or_404(Cart, user=request.user)
    cart_items = CartItem.objects.filter(cart=cart).order_by('-id')
    subtoatal = sum(item.product.price * item.quantity for item in cart_items)
    total = sum(item.product.discounted_price * item.quantity for item in cart_items)
    discount = subtoatal - total
    Head = 'Cart'
    breadcrumbs = [
        ("Home", reverse('user:home')),
        ("Cart", request.path),
    ]
    if not cart_items.exists():
        if 'coupon_code' in request.session:
            del request.session['coupon_code']
            del request.session['discount']
            
    
    context = {
        'cart_items': cart_items,
        'total': total,
        'breadcrumbs' : breadcrumbs,
        'Head':Head,
        'subtoatal':subtoatal,
        'discount':discount,
    }
    
    return render(request, 'user_side/cart.html', context)

def update_cart_item(request, id):
    item = get_object_or_404(CartItem, id=id)
    if request.method == 'POST':
        quantity = int(request.POST.get('qtybutton', 1))
        item.quantity = quantity
        item.save()
        messages.success(request, "Cart item updated successfully")
    return redirect('cart:cart_detail')

@login_required
def remove_from_cart(request, cart_item_id):
    cart_item = get_object_or_404(CartItem, id=cart_item_id)
    
    if cart_item.cart.user != request.user:
        return redirect('cart:cart_detail')  
    
    cart_item.delete()
    messages.success(request, "Item removed from cart.")
    return redirect('cart:cart_detail')

def clear_cart(request):
    if request.user.is_authenticated:
        CartItem.objects.filter(user=request.user).delete()
        messages.success(request,'Cart is cleared')  
    return redirect('cart:cart_detail')

