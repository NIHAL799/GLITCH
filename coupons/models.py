from django.db import models
from django.utils.translation import gettext_lazy as _
from django.core.validators import MinValueValidator, MaxValueValidator
from django.conf import settings
from django.utils import timezone
# Create your models here.

class Coupon(models.Model):
    code = models.CharField(max_length=50, unique=True)
    start_date = models.DateTimeField(default=timezone.now)
    expiry_date = models.DateTimeField()
    offer_percentage = models.DecimalField(max_digits=5, decimal_places=2, validators=[MinValueValidator(0), MaxValueValidator(50)])
    overall_usage_limit = models.PositiveIntegerField(default=0, help_text=_('Total number of times the coupon can be used'))
    limit_per_user = models.PositiveIntegerField(default=1, help_text=_('Maximum number of times a single user can use the coupon'))
    minimum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text=_('Minimum order amount required to use the coupon'))
    maximum_order_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0, help_text=_('Maximum order amount required to use the coupon'))
    usage_count = models.PositiveIntegerField(default=0, help_text=_('Total number of times the coupon has been used'))
    is_active = models.BooleanField(default=True)


    def remaining_usage(self):
        return self.overall_usage_limit - self.usage_count
    
    def is_expired(self):
        
        if self.expiry_date and self.expiry_date < timezone.now():
            return True
        return False

    def __str__(self):
        return self.code
    
class CouponUsage(models.Model):
    coupon = models.ForeignKey(Coupon, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    used_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Coupon {self.coupon.code} used by {self.user.username}"