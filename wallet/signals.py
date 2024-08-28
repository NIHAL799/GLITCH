from django.db.models.signals import post_save
from .models import Wallet 
from django.dispatch import receiver
from django.conf import settings
from user.models import UserDetails



@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_wallet(sender, instance, created, **kwargs):
    if created:
        Wallet.objects.create(user=instance)
        instance.userdetails.wallet = Wallet.objects.get(user=instance)
        instance.userdetails.save()

@receiver(post_save, sender=UserDetails)
def save_user_wallet(sender, instance, **kwargs):
    if not instance.wallet:
        wallet = Wallet.objects.create(user=instance.user)
        instance.wallet = wallet
        instance.save()
        

    