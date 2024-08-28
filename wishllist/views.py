from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from .models import Wishlist
from products.models import Products
from django.contrib import messages
from django.contrib.auth.decorators import login_required


@login_required
def wishlist_view(request):
    wishlist_items = Wishlist.objects.filter(user=request.user)
    breadcrumbs = [
        ("Home", reverse('user:home')),
        ("Wishlist", request.path),
    ]
    context = {
        'wishlist_items':wishlist_items,
        'breadcrumbs':breadcrumbs,
    }
    return render(request,'user_side/wishlist.html',context)

def add_to_wishlist(request,product_id):
    product = get_object_or_404(Products,id=product_id)
    wishlist,created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if created:
        messages.success(request,'Product added to your wishlist.')
    else:
        messages.info(request,'Product is aleready in your wishlist.')
    return redirect('wishlist:wishlist_view')

def remove_from_wishlist(request,product_id):
    product = get_object_or_404(Products,id=product_id)
    wishlist = Wishlist.objects.filter(user=request.user,product=product)
    if wishlist.exists():
        wishlist.delete()
        messages.success(request, 'Product removed from your wishlist.')
    else:
        messages.info(request, 'Product was not in your wishlist.')
    return redirect('wishlist:wishlist_view')