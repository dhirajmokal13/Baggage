# Generated by Django 5.0.3 on 2024-03-05 14:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('customer', '0003_alter_user_mobile'),
    ]

    operations = [
        migrations.AlterField(
            model_name='product',
            name='Image',
            field=models.ImageField(default='', max_length=255, upload_to='product'),
        ),
    ]