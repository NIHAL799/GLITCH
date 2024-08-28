from django import forms
from coupons.models import Coupon
import re


class CouponForm(forms.ModelForm):

    class Meta:
        model = Coupon
        exclude = ['usage_count','is_active']
        fields = ['code', 'start_date','expiry_date', 'offer_percentage', 'overall_usage_limit',
                   'limit_per_user','minimum_order_amount','maximum_order_amount']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'text', 'class': 'form-control', 'id': 'id_start_date'}),
            'expiry_date': forms.DateInput(attrs={'type': 'text', 'class': 'form-control', 'id': 'id_end_date'}),
        }
    

    def __init__(self, *args, **kwargs):
        super(CouponForm, self).__init__(*args, **kwargs)
        for field in self.fields:
            self.fields[field].widget.attrs['class'] = 'form-control'
    
    def clean_code(self):
        code = self.cleaned_data['code']

        min_length = 6
        max_length = 15
        if len(code) < min_length or len(code) > max_length:
            raise forms.ValidationError(f"Coupon code must be between {min_length} and {max_length} characters long.")

        if Coupon.objects.filter(code=code).exclude(id=self.instance.id).exists():
            raise forms.ValidationError("Coupon code must be unique.")

        if not re.match(r'^[a-zA-Z0-9]*$', code):
            raise forms.ValidationError("Coupon code must contain both letters and numbers.")

        excluded_characters = ['_', ' ']
        if any(char in code for char in excluded_characters):
            raise forms.ValidationError("Coupon code cannot contain underscores or spaces.")

        reserved_keywords = ['invalid', 'expired', 'test']
        if code.lower() in reserved_keywords:
            raise forms.ValidationError("Coupon code cannot be a reserved keyword.")

        return code
    
    def clean_start_date(self):
        start_date = self.cleaned_data['start_date']
        return start_date.replace(hour=0, minute=0, second=0, microsecond=0)

    def clean_expiry_date(self):
        expiry_date = self.cleaned_data['expiry_date']
        return expiry_date.replace(hour=23, minute=59, second=59, microsecond=999999)
    
    def clean_minimum_order_amount(self):
        minimum_order_amount = self.cleaned_data['minimum_order_amount']
        if str(minimum_order_amount).startswith('0'):
            raise forms.ValidationError("Minimum order amount should not start with 0.")
        if  minimum_order_amount < 0:
            raise forms.ValidationError("Minimum order amount cannot be negative.")
        return minimum_order_amount

    def maximum_order_amount(self):
        maximum_order_amount = self.cleaned_data['maximum_order_amount']
        if str(maximum_order_amount).startswith('0'):
            raise forms.ValidationError("Maximum offer price should not start with 0.")
        if  maximum_order_amount < 0:
            raise forms.ValidationError("Maximum offer price cannot be negative.")
        return maximum_order_amount