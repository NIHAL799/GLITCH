import calendar
import datetime
from django.db.models import Sum, Count, Prefetch
from django.shortcuts import redirect, render ,get_object_or_404
from django.http import HttpResponse
from django.contrib import messages,auth
from urllib import request
from django.db.models import Sum
from user.models import *
from django.contrib.auth import authenticate,login,logout
from django.contrib import messages,auth
from django.views.decorators.cache import cache_control, never_cache
from django.contrib.auth.decorators import login_required
from admin_side.models import *
from order.models import Order,OrderItem
from datetime import datetime, timedelta
from django.utils import timezone
from .forms import SalesReportFilterForm
import csv
import openpyxl
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from products.models import Products
from category.models import Category


def monthly_earnings():
    current_year = timezone.now().year
    current_month = timezone.now().month
    _, num_days = calendar.monthrange(current_year, current_month)
    start_date = timezone.datetime(current_year, current_month, 1)
    end_date = timezone.datetime(current_year, current_month, num_days, 23, 59, 59)
    monthly_earnings = (
        Order.objects.filter(created_at__range=(start_date, end_date)).aggregate(
            total_earnings=Sum("payable_amount")
        )["total_earnings"]
        or 0
    )
    return monthly_earnings

#============ Best selling PRODUCT ===================================================
def get_most_ordered_products_with_count():
    ordered_products = OrderItem.objects.values('product').annotate(total_orders=Count('product'))
    most_ordered_products = ordered_products.order_by('-total_orders')[:10]
    products_with_count = []
    for product_data in most_ordered_products:
        product_id = product_data['product']
        total_orders = product_data['total_orders']
        product_obj = Products.objects.get(pk=product_id)
        products_with_count.append((product_obj, total_orders))
    return products_with_count

#================== Best Selling CATEGORY ==============================================


def get_most_ordered_categories_with_count():
    ordered_categories = OrderItem.objects.values('product__category').annotate(total_orders=Count('product__category'))
    most_ordered_categories = ordered_categories.order_by('-total_orders')[:10]
    categories_with_count = []
    for category_data in most_ordered_categories:
        category_id = category_data['product__category']
        total_orders = category_data['total_orders']
        category_obj = Category.objects.get(pk=category_id)
        categories_with_count.append((category_obj, total_orders))
    return categories_with_count


def dashboard(request):

    if 'username' not in request.session :
        return redirect('superuser:admin_login')
    
    
    
    orders = OrderItem.objects.filter(status='delivered')
    order_count = orders.count()
    revenue = (
        Order.objects.aggregate(total=Sum('total_amount'))['total'] or 0
    )

    chart_month = [0] * 12
    new_users = [0] * 12
    orders_count = [0] * 12
    for order in orders:
        month = order.order.created_at.month - 1
        chart_month[month] += int(order.payment_after_discount * order.quantity)
        orders_count[month] += 1
    
    print(month, chart_month, orders_count)
    for user in UserDetails.objects.all():
        month = user.date_joined.month - 1
        new_users[month] += 1
    all_orders = Order.objects.all().order_by("-created_at")[:10]
    date = request.GET.get("date")
    
    products_count = Products.objects.all().count()
    categories_count = (
        Products.objects.values("category").distinct().count()
    )
    monthly_earning = monthly_earnings()
    most_ordered_products_with_count = get_most_ordered_products_with_count()
    most_ordered_categories_with_count = get_most_ordered_categories_with_count()


    total_earnings = Order.objects.aggregate(total=Sum('total_amount'))['total']
    total_order = OrderItem.objects.count()
    total_completed = OrderItem.objects.filter(status='delivered').count()
    total_cancelled = OrderItem.objects.filter(status='cancelled').count()
    total_pending = OrderItem.objects.filter(status='ordered').count()
    total_shipped = OrderItem.objects.filter(status='shipped').count()
    total_products = Products.objects.count()
    total_categories = Category.objects.count()
    sales_data = Order.objects.values('created_at__date').annotate(total=Sum('total_amount')).order_by('created_at__date')
    sales_dates = [data['created_at__date'].strftime('%Y-%m-%d') for data in sales_data]
    sales_totals = [data['total'] for data in sales_data]


    order_statuses = ['delivered', 'cancelled', 'ordered', 'shipped']
    order_counts = [
        total_completed,
        total_cancelled,
        total_pending,
        total_shipped
    ]
    context = {
        "revenue": revenue,
        "order_count": order_count,
        "products_count": products_count,
        "categories_count": categories_count,
        "monthly_earning": monthly_earning,
        "month": chart_month,
        "new_users": new_users,
        "orders_count": orders_count,
        "users": UserDetails.objects.filter(is_admin=False).order_by("-date_joined")[:5],
        "most_ordered_products_with_count":most_ordered_products_with_count,
        "most_ordered_categories_with_count":most_ordered_categories_with_count,

        'total_earnings':total_earnings,
        'total_order':total_order,
        'total_completed':total_completed,
        'total_cancelled':total_cancelled,
        'total_pending':total_pending,
        'total_shipped':total_shipped,
        'total_products':total_products,
        'total_categories':total_categories,
        'sales_dates':sales_dates,
        'sales_totals':sales_totals,
        'order_counts':order_counts,
        'order_statuses':order_statuses,


    }
    return render(request,'admin_side/index.html',context)

#======================================= Admin Validation and registrations =================================== #

@cache_control(no_cache=True, must_revalidate=True, no_store=True)
def admin_login(request):
    if 'username' in request.session:
        return redirect('superuser:dashboard')
    if request.method == 'POST':
        email=request.POST.get('email')
        password=request.POST.get('password')

        user = auth.authenticate(email=email,password=password)

        if user is not None and user.is_superuser:
            request.session['username'] = email
            return redirect('superuser:dashboard')
        else:
            messages.info(request,'Invalid Email or password.')
            return redirect('superuser:admin_login')
    return render(request,"admin_side/admin_login.html")

def admin_logout(request):
    if 'username' in request.session:
        request.session.flush()

    return redirect('superuser:admin_login')

#======================================= User Management =================================== #
def customer_view(request):
    if 'username' not in request.session:
        return redirect('superuser:admin_login')
    data = UserDetails.objects.all()
    
    context = {'data':data }
    return render (request,"admin_side/customer_view.html",context)
def block_user(request, user_id):
    user = get_object_or_404(UserDetails, id=user_id)
    user.is_active = False 
    user.save()
    messages.success(request,f'{user.last_name} Blocked successfully')
    return redirect('superuser:customer_view')
def unblock_user(request, user_id):
    user = get_object_or_404(UserDetails, id=user_id)
    user.is_active = True  
    user.save()
    messages.success(request,f'{user.last_name} UnBlocked successfully')
    return redirect('superuser:customer_view')


def sales_report(request):
    form = SalesReportFilterForm(request.GET or None)
    orders = Order.objects.all()

    if form.is_valid():
        date_filter = form.cleaned_data['date_filter']
        start_date = form.cleaned_data['start_date']
        end_date = form.cleaned_data['end_date']

        if start_date and end_date:
            if start_date > end_date:
                messages.error(request,'Start Date must before end date')
                orders = None
                total_sales = 0
                total_discount = 0
                order_count = 0
                context = {
                    'form': form,
                    'orders': orders,
                    'total_sales': total_sales,
                    'total_discount': total_discount,
                    'order_count': order_count,
                }
        
        
                return render(request, 'admin_side/sales_report.html', context)

        now = timezone.now()

        if date_filter == 'daily':
            start_date = timezone.localdate()  
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = start_date + timedelta(days=1)
        elif date_filter == 'weekly':
            start_date = now - timedelta(days=now.weekday())
            start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date + timedelta(days=7)
        elif date_filter == 'monthly':
            start_date = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            next_month = now.replace(day=28) + timedelta(days=4)  
            end_date = next_month - timedelta(days=next_month.day - 1)
        elif date_filter == 'yearly':
            start_date = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            end_date = start_date.replace(year=start_date.year + 1)
        elif date_filter == 'custom' and start_date and end_date:
            start_date = timezone.make_aware(datetime.combine(start_date, datetime.min.time()))
            end_date = timezone.make_aware(datetime.combine(end_date, datetime.max.time()))

        orders = orders.filter(created_at__range=[start_date, end_date])
    orders = orders.order_by('-created_at')
    total_sales = orders.aggregate(total_sales=Sum('total_amount'))['total_sales'] or 0

    total_discount = 0
    for order in orders:
        order_items = OrderItem.objects.filter(order=order)
        original_price_total = sum(item.price * item.quantity for item in order_items)
        order_discount = original_price_total - order.total_amount
        total_discount += order_discount

    total_sales = round(total_sales, 2)
    total_discount = round(total_discount, 2)
    order_count = orders.count()

    context = {
        'form': form,
        'orders': orders,
        'total_sales': total_sales,
        'total_discount': total_discount,
        'order_count': order_count,
    }
    
    
    return render(request, 'admin_side/sales_report.html', context)


def download_pdf_report(request):
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = 'attachment; filename="sales_report.pdf"'

    p = canvas.Canvas(response, pagesize=letter)
    p.drawString(100, 750, "Sales Report")
    
    orders = Order.objects.all()
    if request.GET:
        form = SalesReportFilterForm(request.GET)
        if form.is_valid():
            if form.cleaned_data['start_date']:
                orders = orders.filter(created_at__gte=form.cleaned_data['start_date'])
            if form.cleaned_data['end_date']:
                orders = orders.filter(created_at__lte=form.cleaned_data['end_date'])
    
    y = 700
    for order in orders:
        p.drawString(100, y, f"Order ID: {order.id} User: {order.user.username} Total: ${order.total_amount}")
        y -= 20
    
    p.showPage()
    p.save()
    return response


def download_excel_report(request):
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="sales_report.xlsx"'

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sales Report"

    ws.append(["Order ID", "User", "Total Price", "Item Status", "Return Status", "Coupon Code", "Discount Percentage"])

    orders = Order.objects.all()
    if request.GET:
        form = SalesReportFilterForm(request.GET)
        if form.is_valid():
            if form.cleaned_data['start_date']:
                orders = orders.filter(created_at__gte=form.cleaned_data['start_date'])
            if form.cleaned_data['end_date']:
                orders = orders.filter(created_at__lte=form.cleaned_data['end_date'])

    for order in orders:
        order_items = order.order_item.all()
        for item in order_items:
            ws.append([
                order.id,
                order.user.username,
                order.total_amount,
                item.status,  
                item.status,  
                getattr(item.product.coupon, 'code', 'N/A'),  
                item.discount_amount  
            ])

    wb.save(response)
    return response


def best_selling(request):
    products = Products.objects.all().order_by('-popularity')[:3]
    categories = Category.objects.annotate(total_sold=Sum('products__orderitem__quantity')).order_by('-total_sold')[:3]
    context = {
        'products':products,
        'categories':categories,
    }
    return render(request,'admin_side/best_selling.html',context)