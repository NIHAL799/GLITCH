# Generated by Django 4.2.13 on 2024-08-01 05:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0002_remove_products_product_image_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='products',
            name='default_image',
            field=models.ImageField(blank=True, null=True, upload_to='images/product'),
        ),
    ]
