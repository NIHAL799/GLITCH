# Generated by Django 4.2.13 on 2024-07-31 14:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0005_alter_orderitem_product_size'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='orderitem',
            name='product_size',
        ),
    ]
