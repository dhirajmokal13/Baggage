# Generated by Django 5.0.3 on 2024-03-08 03:33

import datetime
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0010_remove_productorders_product'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productorders',
            name='expected_delivery_date',
            field=models.DateField(default=datetime.date(2024, 3, 11)),
        ),
    ]
