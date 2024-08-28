from django.utils import timezone
from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from phonenumber_field.modelfields import PhoneNumberField
from django.conf import settings
from wallet.models import Wallet


class MyAccountManager(BaseUserManager):
    def create_user(self, first_name, last_name, username, email, password=None):
        if not email:
            raise ValueError('User must have an email address')

        if not username:
            raise ValueError('User must have a username')

        user = self.model(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, first_name, last_name, username, email, password):
        user = self.create_user(
            email=self.normalize_email(email),
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
        )
        user.is_admin = True
        user.is_staff = True
        user.is_active = True
        user.is_superuser = True
        user.save(using=self._db)
        return user

class UserDetails(AbstractBaseUser):
    first_name = models.CharField(max_length=30)
    last_name = models.CharField(max_length=30,blank = True,null=True)
    phone = PhoneNumberField()
    username = models.CharField(max_length=50, unique=True, null=False, blank=False)
    email = models.EmailField(max_length=100, unique=True)


    date_joined = models.DateTimeField(auto_now_add=True)
    last_login = models.DateTimeField(auto_now=True)
    is_admin = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)
    is_staff = models.BooleanField(default=False) 
    wallet = models.OneToOneField(Wallet, on_delete=models.CASCADE, null=True, blank=True, related_name='user_wallet')
    referral_code = models.CharField(max_length=50,unique=True,null=True,blank=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username', 'first_name', 'last_name']

    objects = MyAccountManager()

    def full_name(self):
        return f'{self.first_name} {self.last_name}'

    def __str__(self):
        return self.email

    def has_perm(self, perm, obj=None):
        return self.is_admin

    def has_module_perms(self, app_label):
        return True

    def activate_account(self,user):
        """
        Activate the user account.
        """
        self.is_active = True
        self.save()

    def deactivate_account(self):
        """
        Deactivate the user account.
        """
        self.is_active = False
        self.save()

    def get_full_name(self):
        return self.first_name + self.last_name



    def verify_account(self,user):
        """
        Activate the user account.
        """
        self.is_verified = True
        self.save()

    



class Address(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    company_name = models.CharField(max_length=100, blank=True, null=True)
    country = models.CharField(max_length=50)
    street_address = models.CharField(max_length=100)
    apartment_address = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=50)
    district = models.CharField(max_length=50)
    postcode = models.CharField(max_length=20)
    phone = models.CharField(max_length=20)
    email = models.EmailField()



    def __str__(self):
        return f"{self.user} , {self.street_address}, {self.city}"
    


