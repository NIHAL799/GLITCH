# Generated by Django 4.2.13 on 2024-08-09 13:50

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('products', '0006_products_discounted_price'),
    ]

    operations = [
        migrations.AlterField(
            model_name='products',
            name='max_price',
            field=models.DecimalField(decimal_places=2, default=1, max_digits=10, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]
