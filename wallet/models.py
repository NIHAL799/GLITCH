from django.db import models
from django.conf import settings


class Wallet(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='wallets')
    balance = models.DecimalField(max_digits=10,decimal_places=2,default=0.00)


class Transaction(models.Model):
    wallet = models.ForeignKey(Wallet,related_name='transactions',on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10,decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)
    description = models.TextField()
