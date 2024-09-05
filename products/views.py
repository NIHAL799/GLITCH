from django.shortcuts import render,redirect,get_object_or_404,HttpResponseRedirect
from .models import *
from django.contrib import messages
from django.utils.text import slugify
from django.views.decorators.cache import cache_control
from django.contrib.auth.decorators import login_required
from .forms import ProductForm,EditStockForm
from django.forms import modelformset_factory
from django.db.models.signals import pre_save
from PIL import Image
from django.dispatch import receiver
import os
from django.db.models import Min, Max, Avg,Count,Sum
from django.db.models import Q,F
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from order.models import Order,OrderItem
from decimal import Decimal
import logging
from django.core.exceptions import ValidationError



def product_details(request, id):
    user = request.user
    product = Products.objects.get(id=id)
    ratings = Rating.objects.filter(product=product).select_related('user')
    avg_rating = product.ratings.aggregate(Avg('rating'))['rating__avg'] or 0
    review_count = Rating.objects.filter(product=product, review__isnull=False).count()
    discounted_price = product.calculate_discounted_price()
    discount_percentage = product.category.discount_percentage
    
    cat_products = Products.objects.filter(category=product.category, is_available=True)
    
    breadcrumbs = [
        ("Home", reverse('user:home')),
        ('Products', reverse('product:all_products')),
        ("Product View", request.path),
    ]
    
    context = {
        'review_count':review_count,
        'product': product,
        'ratings': ratings,
        'average_rating': avg_rating,
        'cat_products': cat_products,
        'breadcrumbs': breadcrumbs,
        'discounted_price': discounted_price,
        'discount_percentage': discount_percentage,
        'user':user,
    }

    return render(request, 'user_side/product_detail_2.html', context)

        

@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def admin_product_list(request):

    user = request.user
    if not user.is_authenticated:
        return redirect('superuser:admin_login')
    elif not user.is_superuser:
        return redirect('superuser:admin_login')
    
    products = Products.objects.all().order_by('-created_date')
    context = {'products':products }

    return render(request,'admin_side/product_list.html',context)

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_add_products(request):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)   
        if form.is_valid():
            try:  
                product = form.save(commit=False)
                product.slug = slugify(product.product_name)

                if not product.discounted_price:
                    product.discounted_price = product.price 

                product.price = Decimal(str(product.price))
                
                count = 1
                while Products.objects.filter(slug=product.slug).exists():
                    product.slug = f"{product.slug}-{count}"
                    count += 1
                product.save()
            
                messages.success(request, 'Product added successfully.')
                return redirect('product:admin_product_list')
            except ValidationError as e:
                messages.error(request, e.messages)
            except Exception as e:
                messages.error(request, "An unexpected error occurred. Please try again.")
        
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = ProductForm()

    categories = Category.objects.all()
    context = {
        'form': form,
        'categories': categories,
    }
    return render(request, 'admin_side/add_products.html', context)


def manage_sizes(request, id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    product = get_object_or_404(Products, id=id)
    sizes = ProductSize.objects.filter(product=product)

    if request.method == 'POST':
        stocks = request.POST.getlist('stocks')
        size_ids = request.POST.getlist('size_ids')

        
        for size_id, stock in zip(size_ids, stocks):
            if int(stock) < 0:
                messages.error(request,'Available stock should be a positive number')
                return redirect('product:manage_sizes', id=product.id)
            size = get_object_or_404(ProductSize, id=size_id)
            size.stock = int(stock)
            size.save()
        messages.success(request, 'Stocks updated successfully')
        return redirect('product:manage_sizes', id=product.id)

    context = {
        'product': product,
        'sizes': sizes,
    }
    return render(request, 'admin_side/manage_sizes.html', context)

def add_size(request, id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    product = get_object_or_404(Products, id=id)
    sizes = [7,8,9]  

    if request.method == 'POST':
        for size in sizes:
            stock = request.POST.get(f'stock_{size}')
            if int(stock) < 0:
                messages.error(request,'Available stock should be a positive number')
                return redirect('product:manage_sizes', id=product.id)
            if stock:
                size_obj, created = ProductSize.objects.get_or_create(product=product, size=size)
                if created:
                    size_obj.stock = stock
                else:
                    size_obj.stock = F('stock') + int(stock)
                size_obj.save()

        messages.success(request, 'Sizes and stocks added/updated successfully.')
        return redirect('product:manage_sizes', id=product.id)

    context = {
        'product': product,
        'sizes': sizes,
    }
    return render(request, 'admin_side/add_sizes.html', context)


def delete_size(request, id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    size = get_object_or_404(ProductSize, id=id)
    product = size.product

    if request.method == 'POST':
        size.delete()
        messages.success(request, 'Size and stock deleted successfully.')
        return redirect('product:manage_sizes', id=product.id)

    context = {
        'size': size,
        'product': product,
    }
    return render(request, 'admin_side/confirm_delete.html', context)

            
def admin_delete_product(request,id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    product=get_object_or_404(Products,id=id)
    if product.soft_deleted:
        product.soft_deleted=False
        product.is_available=True
        messages.success(request,f'{product.product_name} listed Successfully.')

    else:
        product.soft_deleted=True
        product.is_available=False
        messages.warning(request,f'{product.product_name} unlisted Successfully.')
    product.save()
    return redirect('product:admin_product_list')


@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def admin_edit_product(request,id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    product=Products.objects.get(id=id)
    categories=Category.objects.all()

    if request.method=='POST':

        product.product_name=request.POST.get('product_name')
        category_id=request.POST.get('category')
        product.category = Category.objects.get(id=category_id) 
        product.description=request.POST.get('description')
        product.price=request.POST.get('price')
        price_str = request.POST.get('price')

        try:
            price = float(price_str)
        except ValueError:
            messages.warning(request, "Price must be a valid number.")
            return redirect('product:admin_edit_product', id=id)

        if price < 0:
            messages.warning(request, "Price must be greater than or equal to 0")
            return redirect('product:admin_edit_product', id=id)
        
        
        if 'product_image' in request.FILES:
            product.product_image = request.FILES['product_image']

        else:
            product.product_image = product.product_image
        if 'product_image2' in request.FILES:
            product.product_image2 = request.FILES['product_image2']

        else:
            product.product_image2 = product.product_image2

        if 'product_image3' in request.FILES:
            product.product_image3 = request.FILES['product_image3']
        else:
            product.product_image3 = product.product_image3

        if 'product_image4' in request.FILES:
            product.product_image4 = request.FILES['product_image4']
        else:
            product.product_image4 = product.product_image4
        
        
        product.save()
        messages.success(request,'Product Edited Succcessfully..')
        return redirect('product:admin_product_list')
    return render(request, 'admin_side/edit_product.html', {'product': product,'categories': categories})




def all_products(request):
    sort_by = request.GET.get('sort_by', 'default')
    category_ids = request.GET.getlist('category')
    price_ranges = request.GET.getlist('price_range')
    sizes = request.GET.getlist('size')
    query = request.GET.get('q', '')
    breadcrumbs = [
        ("Home", reverse('user:home')),
        ("Products", request.path),
    ]

    products = Products.objects.filter(
        soft_deleted=False,
        is_available=True,
    ).annotate(total_stock=Count('sizes__stock')).filter(total_stock__gt=0)

    for product in products:
        product.discounted_price = product.calculate_discounted_price()

    if query:
        products = products.filter(product_name__icontains=query)

    if category_ids:
        try:
            category_ids = [int(cat_id) for cat_id in category_ids]
            products = products.filter(category_id__in=category_ids)
        except ValueError:
            messages.warning(request, 'Invalid category filter')
            products = Products.objects.none()

    if price_ranges:
        price_query = Q()
        for price_range in price_ranges:
            try:
                min_price, max_price = map(float, price_range.split('-'))
                price_query |= Q(price__gte=min_price, price__lte=max_price)
            except ValueError:
                continue
        products = products.filter(price_query)

    if sizes:
        try:
            sizes = [int(size) for size in sizes]
            products = products.filter(sizes__size__in=sizes).distinct()
        except ValueError:
            messages.warning(request, 'Filtered sizes are not in stock')
            products = Products.objects.none()

    if sort_by == 'name_a_to_z':
        products = Products.objects.all().order_by('product_name')
    elif sort_by == 'name_z_to_a':
        products = Products.objects.all().order_by('-product_name')

    if sort_by == 'popularity':
        products = products.order_by('-popularity')
    elif sort_by == 'rating':
        products = products.order_by('-ratings__rating')
    elif sort_by == 'latest':
        products = products.order_by('-created_date')
    elif sort_by == 'price_low_to_high':
        products = products.order_by('price')
    elif sort_by == 'price_high_to_low':
        products = products.order_by('-price')

    categories = Category.objects.filter(is_deleted=False)

    context = {
        'products': products,
        'categories': categories,
        'sort_by': sort_by,
        'price_ranges': price_ranges,
        'sizes': sizes,
        'query': query,
        'category_ids': category_ids,
        'breadcrumbs': breadcrumbs,
    }

    return render(request, 'user_side/shop.html', context)


def clear_filters(request):
    return redirect('product:all_products')
    
def resize_image(image_path, size=(800, 800)):
    if not os.path.exists(image_path):
        return
    with Image.open(image_path) as img:
        img = img.resize(size)
        img.save(image_path)

@receiver(pre_save, sender=Products)
def resize_product_image(sender, instance, **kwargs):
    image_fields = ['product_image', 'product_image2', 'product_image3']
    for field in image_fields:
        image = getattr(instance, field)
        if image:
            resize_image(image.path)

def search_view(request):
    query = request.GET.get('q')

    if query:
        return HttpResponseRedirect(reverse('product:all_products') + f'?q={query}')
    query = ''
    return HttpResponseRedirect(reverse('product:all_products'))




def post_review(request,product_id):
    if request.method == 'POST':
        product = Products.objects.get(id=product_id) 
        user = request.user

        rating = request.POST.get('rating')
        review = request.POST.get('review','')
        if not rating:
            messages.info(request,'Please select a rating...')
            return redirect('product:product_details',id=product_id)
        
        if not Order.objects.filter(user=user, order_item__product=product).exists():
            messages.error(request, "You must order the product before you can give rating or a review.")
            return redirect('product:product_details',id=product_id)
        
        existing_rating = Rating.objects.filter(product=product, user=user).first()
        if existing_rating:
            messages.error(request, "You have already Rated this product.")
            return redirect('product:product_details', id=product_id)
        
        rating = Rating(
            product = product,
            user = user,
            rating = rating,
            review = review,

        )
        rating.save()
        
        messages.success(request,'Thank you for giving your review!')

        return redirect('product:product_details',id=product_id)
    else:
        return redirect('product:product_details',id=product_id)
    


@cache_control(no_cache=True,must_revalidate=True,no_store=True)
def admin_edit_best(request,id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    product=Products.objects.get(id=id)
    categories=Category.objects.all()

    if request.method=='POST':

        product.product_name=request.POST.get('product_name')
        category_id=request.POST.get('category')
        product.category = Category.objects.get(id=category_id) 
        product.description=request.POST.get('description')
        product.price=request.POST.get('price')
        price_str = request.POST.get('price')

        try:
            price = float(price_str)
        except ValueError:
            messages.warning(request, "Price must be a valid number.")
            return redirect('product:admin_edit_best', id=id)

        if price < 0:
            messages.warning(request, "Price must be greater than or equal to 0")
            return redirect('product:admin_edit_best', id=id)
        
        
        if 'product_image' in request.FILES:
            product.product_image = request.FILES['product_image']

        else:
            product.product_image = product.product_image
        if 'product_image2' in request.FILES:
            product.product_image2 = request.FILES['product_image2']

        else:
            product.product_image2 = product.product_image2

        if 'product_image3' in request.FILES:
            product.product_image3 = request.FILES['product_image3']
        else:
            product.product_image3 = product.product_image3

        if 'product_image4' in request.FILES:
            product.product_image4 = request.FILES['product_image4']
        else:
            product.product_image4 = product.product_image4
        
        
        product.save()
        messages.success(request,'Product Edited Succcessfully..')
        return redirect('superuser:best_selling')
    return render(request, 'admin_side/edit_product.html', {'product': product,'categories': categories})