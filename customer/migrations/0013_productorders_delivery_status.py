# Generated by Django 5.0.3 on 2024-03-08 08:06

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0012_productorders_razorpay_order_id_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='productorders',
            name='delivery_status',
            field=models.BooleanField(default=False),
        ),
    ]