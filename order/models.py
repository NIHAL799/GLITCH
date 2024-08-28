from django.db import models
from products.models import Products,ProductSize
from user.models import Address
from django.conf import settings
from django.utils import timezone
from user.models import UserDetails
from django.utils.translation import gettext_lazy as _




class Order(models.Model):
    class PaymentStatus(models.TextChoices):
        PAID = 'paid', _('Paid')
        PENDING = 'pending', _('Pending')
        FAILED = 'failed', _('Faied')
        

    class PaymentMethod(models.TextChoices):
        COD = 'cod', _('Cash on Delivery')
        RAZORPAY = 'razorpay', _('Razorpay')
        WALLET = 'wallet', _('Wallet')

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    address = models.ForeignKey(Address, on_delete=models.SET_NULL, null=True)
    created_at = models.DateTimeField(default=timezone.now, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)
    order_notes = models.TextField(blank=True, null=True)
    payment_method = models.CharField(max_length=10, choices=PaymentMethod.choices, default=PaymentMethod.COD)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payable_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_status = models.CharField(max_length=10, choices=PaymentStatus.choices, default=PaymentStatus.PENDING)
    razorpay_order_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=255, blank=True, null=True)
    razorpay_signature = models.CharField(max_length=255, blank=True, null=True)


    def __str__(self):
        return f"Order {self.id}"

class OrderItem(models.Model):

    STATUS_CHOICES = [
        ('confirmed', _('Confirmed')),
        ('shipped', _('Shipped')),
        ('delivered', _('Delivered')),
        ('cancelled', _('Cancelled')),
        ('returned', _('Returned')),
        ('refunded', _('Refunded')),
        ('return_requested', 'Return Requested'),
        ('return_accepted', 'Return Accepted'),
        ('return_rejected', 'Return Rejected'),


    ]


    order = models.ForeignKey(Order,related_name='order_item', on_delete=models.CASCADE)
    product = models.ForeignKey(Products, on_delete=models.CASCADE)
    product_size = models.ForeignKey(ProductSize, on_delete=models.CASCADE,default=1)  
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed') 
    discount_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_after_discount = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def __str__(self):
        return f"OrderItem {self.id} for Order {self.order.id}"

    