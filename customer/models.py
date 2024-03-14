from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.auth.hashers import make_password, check_password
from datetime import date, timedelta

# Create your models here.


class Contact(models.Model):
    name = models.CharField(max_length=40, default='')
    email = models.EmailField(max_length=40)
    comment = models.TextField(default=None)


class User(models.Model):
    username = models.CharField(max_length=40, unique=True, default=None)
    email = models.EmailField(unique=True, default=None)
    mobile = models.CharField(max_length=20)
    password = models.CharField(max_length=300, default=None)
    isSeller = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        if self.password:
            self.password = make_password(self.password)
        super().save(*args, **kwargs)

    def validate_password(self, pwd):
        return check_password(pwd, self.password)


class Product(models.Model):
    Name = models.CharField(max_length=40, default='')
    Image = models.ImageField(max_length=255, default='', upload_to='product')
    price = models.IntegerField()
    discount = models.FloatField()
    description = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(5)], default=0)
    visiblity = models.BooleanField(default=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE)


class Cart(models.Model):
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)


class ProductOrders(models.Model):
    address = models.CharField(max_length=300, default=None)
    order_amount = models.FloatField(blank=False, null=False)
    # expected delivery date will assign 3 days ahead from now
    expected_delivery_date = models.DateField(
        default=date.today() + timedelta(days=3))
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(
        max_length=100, blank=True, null=True)
    razorpay_order_signature = models.CharField(
        max_length=100, blank=True, null=True)
    payment_paid = models.BooleanField(default=False)
    delivery_status = models.BooleanField(default=False)
    order = models.TextField()
    created_by = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if isinstance(self.order, map):
            order_id_str = map(lambda item: str(item), self.order)
            self.order = ';'.join(order_id_str)
        super().save(*args, **kwargs)

    def _get_product(self, product_id):
        return Product.objects.get(id=product_id)
    
    def _make_dict_unique_products(self, product_id):
        initial_dict = {}
        for id in product_id:
            initial_dict[id] = self._get_product(id)
        return initial_dict

    def serialize_products(self):
        order_id = list(map(lambda id: int(id), (self.order).split(";")))
        unique_product_id = list(set(order_id)) #for better data operations remove duplicate id
        unique_products = self._make_dict_unique_products(unique_product_id) #call the function which make dictionary of unique products for better accessiblity
        products = list(map(lambda item: unique_products[item], order_id))
        self.order = products
        self.delivery_status = "Pending" if not self.delivery_status else "Delivered"
        self.payment_paid = "Pending" if not self.payment_paid else "Done"
        self.order_amount = round(self.order_amount, 2)
        return self