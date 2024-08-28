from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from django.core.validators import validate_email
from user.models import UserDetails,Address
from phonenumber_field.formfields import PhoneNumberField
from phonenumber_field.validators import validate_international_phonenumber



class SignUpForm(UserCreationForm):
    first_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder": "First Name"}),
                                 required=True, help_text='Required. 30 characters or fewer.')
    last_name = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder": "Last Name"}),
                                required=True, help_text='Required. 30 characters or fewer.')
    email = forms.EmailField(max_length=254, widget=forms.EmailInput(attrs={"placeholder": "Email"}), required=True,
                             help_text='Required. Enter a valid email address.')
    phone = PhoneNumberField(widget=forms.TextInput(attrs={"placeholder": "Phone(+91)"}), required=True,
                             validators=[validate_international_phonenumber])

    password1 = forms.CharField(max_length=30, widget=forms.PasswordInput(attrs={"placeholder": "Password"}),
                                required=True, help_text='Required. 30 characters or fewer.')
    password2 = forms.CharField(max_length=30, widget=forms.PasswordInput(attrs={"placeholder": "Confirm Password"}),
                                required=True, help_text='Required. 30 characters or fewer.')
    username = forms.CharField(max_length=30, widget=forms.TextInput(attrs={"placeholder": "Username"}), required=True,
                               help_text='Required. 30 characters or fewer.')
    referral_coupon = forms.CharField(required=False, max_length=50, label="Referral Coupon (Optional)")


    class Meta:
        model = UserDetails
        fields = ['username', 'first_name', 'last_name', 'email', 'phone', 'password1', 'password2']
        labels = {'email': 'Email'}

    def clean_first_name(self):
        first_name = self.cleaned_data.get('first_name')
        if first_name.strip() != first_name:
            raise ValidationError(_('First name should not contain leading spaces.'))
        if not first_name.isalpha():
            raise ValidationError(_('First name should only contain letters.'))
        return first_name

    def clean_last_name(self):
        last_name = self.cleaned_data.get('last_name')
        if last_name.strip() != last_name:
            raise ValidationError(_('Last name should not contain leading spaces.'))
        if not last_name.isalpha():
            raise ValidationError(_('Last name should only contain letters.'))
        return last_name

    def clean_username(self):
        username = self.cleaned_data.get("username")
        if not username.isalnum():
            raise ValidationError('Username should only contain letters and/or numbers.')
        return username




class AddressForm(forms.ModelForm):
    class Meta:
        model = Address
        fields = [
            'first_name', 'last_name', 'company_name', 'country',
            'street_address', 'apartment_address', 'city', 'district',
            'postcode', 'phone', 'email'
        ]













