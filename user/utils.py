from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.conf import settings
from django.utils.encoding import smart_str
import random
import string


# Function to generate random 4 digit number
def generate_otp(length=4):
    return get_random_string(length, '1234567890')


# Function to send OTP through email
def send_otp_email(email, otp):
    subject = 'Verification OTP for Your Account'
    message = f'Your OTP for account verification is: {otp}'
    from_email = settings.EMAIL_HOST_USER  
    recipient_list = [email]

    subject = smart_str(subject)
    message = smart_str(message)
    from_email = smart_str(from_email)

    send_mail(subject, message, from_email, recipient_list)

def generate_referral_code(length=8):
    """Generate a unique referral code."""
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=length))