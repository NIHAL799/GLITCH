from django.db import models
from django.utils.text import slugify
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.utils import timezone

class Category(models.Model):
    category_name = models.CharField(max_length=50, unique=True, verbose_name="Category Name")
    slug = models.SlugField(max_length=100, unique=True)
    description = models.CharField(max_length=255, blank=True, null=True)
    cat_image = models.ImageField(upload_to='images', blank=True, null=True)
    is_deleted = models.BooleanField(default=False)
    is_offer_available = models.BooleanField(default=False)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    minimum_amount = models.IntegerField(default=100)
    end_date = models.DateField(null=True,blank=True)
    popularity = models.IntegerField(default=0)
    class Meta:
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['-id']

    def get_url(self):
            return reverse('product_list_by_category', args=[self.slug])
    
    # def soft_delete(self, *args, **kwargs):
    #     self.is_deleted = True
    #     self.save()
    
    # def restore(self):
    #     self.is_deleted = False
    #     self.save()
    
    def permanent_delete(self):
        super(Category, self).delete()
    
    objects = models.Manager()
    available_objects = models.Manager()  

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.category_name)
        super(Category, self).save(*args, **kwargs)

    def __str__(self):
        return self.category_name
    

    def clean(self):
        if self.is_offer_available and (self.discount <= 0 or not self.end_date):
            raise ValidationError("Active offers must have a positive discount and a valid end date.")
        if self.end_date and self.end_date < timezone.now().date():
            raise ValidationError("End date must be in the future.")
        super().clean()
        