from .utils import generate_otp,send_otp_email
from .models import UserDetails
from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth.models import User
from django.dispatch import receiver
from django.db.models.signals import post_save
from .utils import generate_referral_code

