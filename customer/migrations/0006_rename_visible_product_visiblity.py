# Generated by Django 5.0.3 on 2024-03-06 01:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0005_product_visible'),
    ]

    operations = [
        migrations.RenameField(
            model_name='product',
            old_name='visible',
            new_name='visiblity',
        ),
    ]
