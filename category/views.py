from django.shortcuts import render,redirect,HttpResponse,get_object_or_404
from .models import *
from django.contrib import messages
import re
from products.models import Products
from django.db.models import Count, F, ExpressionWrapper, DecimalField
from datetime import datetime
from django.utils import timezone
from datetime import timedelta


    #======================================= Admin Category management =================================== #

def category_list(request):
    user = request.user
    if not user.is_authenticated:
        return redirect('superuser:admin_login')
    elif not user.is_superuser:
        return redirect('superuser:admin_login')

    if request.method == 'POST':
        category_name = request.POST.get('cat_name')
        catog = Category(category_name = category_name)
        catog.save()
        messages.success(request,'New Category created successfully.')
        return redirect('catogery_list')
    categories = Category.objects.all()
    date = datetime.now().date()
    for cat in categories:
        if cat.is_offer_available:
            if cat.end_date <= date:
                cat.is_offer_available = False
                cat.save()

    context = {"categories":categories}
    return render(request,'admin_side/categories.html',context)


def add_category(request):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        description = request.POST.get('description', '')
        discount = request.POST.get('discount')
        minimum_amount = request.POST.get('minimum_amount')
        end_date = request.POST.get('end_date')
        cat_image = request.FILES.get('cat_image')

        if any(char.isspace() or re.match(r'[@#$%^@%@#%&]', char) for char in category_name):
            messages.error(request, 'Category name should not contain spaces or special characters')
        elif any(char.isspace() or re.match(r'[@#$%^@%@#%&]', char) for char in slug):
            messages.error(request, 'Slug should only contain alphabets and hyphens')
        else:
            categories = Category(
                category_name=category_name,
                slug=slug,
                description=description,
                cat_image=cat_image,
                discount_percentage=discount,
                minimum_amount=minimum_amount,
                end_date=end_date,
            )
            categories.save()
            messages.success(request, f'{category_name} added successfully.')
            return redirect('category:category_list')
    return render(request, 'admin_side/categories_add.html')



def category_edit(request, id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    
    category = get_object_or_404(Category, id=id)
    
    if request.method == 'POST':
        category_name = request.POST.get('category_name')
        slug = request.POST.get('slug')
        description = request.POST.get('description')
        minimum_amount = request.POST.get('minimum_amount')
        end_date = request.POST.get('end_date')
        cat_image = request.FILES.get('cat_image')
        offer = request.POST.get('is_offer_available')
        category_discount = request.POST.get('discount_percentage')

        if offer == 'True':
            products = Products.objects.filter(soft_deleted=False, is_available=True).annotate(total_stock=Count('sizes__stock')).filter(total_stock__gt=0)
            for product in products:
                product.discounted_price = product.calculate_discounted_price()
                product.save()
            if not end_date:
                messages.error(request, 'Select a end date for offer.')
                return render(request, 'admin_side/categories_edit.html', {'category': category})
        
        if not all([category_name,slug,description, minimum_amount]) :
            messages.error(request, 'Please fill out all fields.')
            return render(request, 'admin_side/categories_edit.html', {'category': category})
        
        if not cat_image:
            cat_image = category.cat_image

        if offer == 'False':
            products = Products.objects.filter(soft_deleted=False, is_available=True).annotate(total_stock=Count('sizes__stock')).filter(total_stock__gt=0)
            
            for product in products:
                product.discounted_price = product.price
                product.save()
        

        category.category_name = category_name
        category.slug = slug
        category.description = description
        category.minimum_amount = minimum_amount
        if offer == 'True':
            category.end_date = end_date
        category.cat_image = cat_image
        category.is_offer_available = offer
        category.discount_percentage = category_discount

        category.save()
        messages.success(request, f'Category {category.category_name} modified successfully.')
        return redirect('category:category_list')
    
    context = {'category': category}
    return render(request, 'admin_side/categories_edit.html', context)


def category_soft_delete(request,id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    category = Category.objects.get(id=id)
    if category.is_deleted:
        category.is_deleted=False
        category.save()
        messages.success(request,f'Category {category.category_name} Is Enabled')
        return redirect('category:category_list')
    else:
        category.is_deleted=True
        category.save()
        messages.warning(request,f'Category {category.category_name} Is Disabled ')
        
    return redirect('category:category_list')


def category_delete(request,id):
    user = request.user
    if not user.is_authenticated or not user.is_superuser:
        return redirect('superuser:admin_login')
    category = Category.objects.get(id)
    category.is_deleted = True
    return redirect('category:catogery_list')

    #======================================= User Category Viewws =================================== #


    
def shop_by_category(request, category_name):
    category = Category.objects.get(category_name=category_name)
    
    products = Products.objects.filter(
        soft_deleted=False,
        is_available=True,
        category__category_name=category_name
    ).annotate(total_stock=Count('sizes__stock')).filter(total_stock__gt=0)
    categories = Category.objects.filter(is_deleted=False)
    if category.is_offer_available == True:
        for product in products:
            product.discounted_price = product.calculate_discounted_price()
            product.save()
    else:
        for product in products:
            product.discounted_price = product.price
            product.save()

    breadcrumbs = [
        ("Home", reverse('user:home')),
        ("Category", request.path),
    ]

    context = {
        'breadcrumbs': breadcrumbs,
        'products': products,
        'categories':categories,
    }
    return render(request, "user_side/categories_products.html", context)













