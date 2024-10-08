# Generated by Django 4.2.13 on 2024-08-07 05:25

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('order', '0021_remove_order_razorpay_order_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='order',
            name='razorpay_order_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_payment_id',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
        migrations.AddField(
            model_name='order',
            name='razorpay_signature',
            field=models.CharField(blank=True, max_length=255, null=True),
        ),
    ]
