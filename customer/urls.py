from django.urls import path
from customer import views

urlpatterns = [
    path("", views.index, name='Home'),
    path("about", views.about, name='About'),
    path("collections/<int:page>/<str:page_position>", views.collection, name='Collection'),
    path("collection/search", views.search_collection, name="SearchCollection"),
    path("cart", views.cart, name="Cart"),
    path("cart/checkout/<int:order_id>", views.checkout, name="checkout"),
    path("customer/orders", views.customer_orders, name="CustomerOrders"),
    path("customer/orders/invoice/<int:order_id>", views.download_invoice, name="Invoice"),
    path("payment/success/<int:order_id>/<str:razorpay_order_id>/<str:razorpay_payment_id>/<str:razorpay_signature>", views.handle_payment_success, name="paymentHandle"),
    path("product/cart/add/<int:product_id>", views.add_cart, name='AddCart'),
    path("product/cart/remove/<int:cart_id>", views.remove_cart, name='RemoveCart'),
    path("contact", views.contact, name='Contact'),
    path("login", views.login, name='Login'),
    path("signup", views.Signup, name='Signup'),
    path("order/<int:product_id>", views.Order, name='Order'),
    path("signout", views.Signout, name='Signout'),
    path("seller", views.Seller_panel, name="Seller"),
    path("seller/orders", views.seller_orders, name="SellerOrders"),
    path("seller/orders/delivery/status/<int:order_id>/<str:status>", views.delivery_status_change, name="DeliveryStatus"),
    path("seller/make", views.becomeSeller, name="makeseller"),
    path("seller/product/visiblity", views.change_product_visiblity, name="ChangeVisiblity"),
    path("seller/product/remove/<int:product_id>", views.remove_product, name="ProductRemove"),
    path("seller/product/update/<int:product_id>", views.product_update, name="ProductUpdate"),
]
