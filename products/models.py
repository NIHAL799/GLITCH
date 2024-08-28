from django.db import models
from django.db.models import CheckConstraint, Q, F
from django.core.validators import MinValueValidator
from category.models import Category
from user.models import UserDetails
from decimal import Decimal


class Products(models.Model):
    product_name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    description = models.CharField(max_length=500, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])
    is_offer_available = models.BooleanField(default=False)
    offer_percentage = models.IntegerField(default=33)
    product_image = models.ImageField(upload_to='images/product', null=True)
    is_available = models.BooleanField(default=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    created_date = models.DateField(auto_now_add=True)
    modified_date = models.DateField(auto_now=True)
    product_image2 = models.ImageField(upload_to='images/product', null=True)
    product_image3 = models.ImageField(upload_to='images/product', null=True)
    product_image4 = models.ImageField(upload_to='images/product', null=True)
    soft_deleted = models.BooleanField(default=False)
    popularity = models.IntegerField(default=0)
    discounted_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0)])

    

    def __str__(self):
        return self.product_name
    
    
    
    def calculate_discounted_price(self):
        """Calculate the discounted price based on category discount."""
        if self.category.is_offer_available:
            if self.category.discount_percentage:
                discount = self.price * (self.category.discount_percentage / 100)
                print(f"Original Price: {self.price}, Discount: {discount}, Discounted Price: {self.price - discount}")
                return self.price - discount
        print(f"No discount applied. Returning original price: {self.price}")
        return self.price
    
    def clean(self):
        super().clean()
        if self.price:
            self.price = Decimal(str(self.price))
        if not self.discounted_price:
            self.discounted_price = Decimal(str(self.price))
 


class ProductSize(models.Model):
    product = models.ForeignKey(Products, related_name='sizes', on_delete=models.CASCADE)
    size = models.IntegerField()
    stock = models.IntegerField(default=0)

    def __str__(self):
        return f"{self.product.product_name} - Size {self.size}"

class Rating(models.Model):
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='ratings')
    user = models.ForeignKey(UserDetails, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField()  
    review = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('product', 'user')