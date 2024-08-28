from django import forms
from .models import Products,ProductSize,Rating
from django.core.exceptions import ValidationError
from django.forms import inlineformset_factory
from PIL import Image
from decimal import Decimal,InvalidOperation
import logging

logger = logging.getLogger(__name__)


class ProductForm(forms.ModelForm):
    class Meta:
        model = Products
        fields = [
            'product_name', 'category', 'description', 'price','is_offer_available',  
            'offer_percentage', 'product_image', 'product_image2',
            'product_image3', 'product_image4'
        ]
        widgets = {
            'description': forms.Textarea(attrs={'rows': 4}),
        }
    def clean(self):
        cleaned_data = super().clean()
        price = cleaned_data.get('price')
        offer_percentage = cleaned_data.get('offer_percentage')
        is_offer_available = cleaned_data.get('is_offer_available')
        print(f"Price in clean method: {price}, type: {type(price)}")
        

        if price:
            try:
                cleaned_data['price'] = Decimal(str(price))
                cleaned_data['discounted_price'] = cleaned_data['price']
            except InvalidOperation:
                self.add_error('price', "Invalid price format.")
        if is_offer_available:

            if offer_percentage < 1:
                print("Offer percentage is required if the product is in offer.")
                raise ValidationError("Offer percentage is required if the product is in offer.")
            elif offer_percentage <= 0:
                print("Offer percentage must be positive.")
                self.add_error('offer_percentage', "Offer percentage must be positive.")


        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        for field in ['product_image', 'product_image2', 'product_image3', 'product_image4']:
            image = getattr(instance, field)
            if image:
                cropped_image = self.crop_image(image)
                setattr(instance, field, cropped_image)
        if commit:
            instance.save()
        return instance

    def crop_image(self, image):
        img = Image.open(image)
        width, height = img.size
        new_width = new_height = min(width, height)
        left = (width - new_width) / 2
        top = (height - new_height) / 2
        right = (width + new_width) / 2
        bottom = (height + new_height) / 2
        img = img.crop((left, top, right, bottom))
        img = img.resize((2016, 2016), Image.Resampling.LANCZOS)
        img.save(image.path)
        return image


class EditStockForm(forms.ModelForm):
    class Meta:
        model = ProductSize
        fields = ['stock']