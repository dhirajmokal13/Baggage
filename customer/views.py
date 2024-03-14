from django.shortcuts import render, HttpResponse, redirect
from django.urls import resolve
from django.contrib import messages
from customer.models import Contact, User, Product, Cart, ProductOrders
from django.db.models import Q
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from functools import reduce
import razorpay
from .utils.calculate_actual_cost import calculate_current_price
from reportlab.pdfgen import canvas
import environ
import datetime
env = environ.Env()
environ.Env.read_env()

# Create your views here.


def collection(req, page, page_position):
    if page_position == "Previous" or page_position == "Next":
        if page_position == "Next":
            page += 1
        else:
            page -= 1
    product = Product.objects.filter(visiblity=True)
    items_per_page = 10
    paginator = Paginator(product, items_per_page)
    total_pages = paginator.num_pages
    page_obj = paginator.page(page)
    if page > total_pages or page == 0:
        page = 1
    page_position_current = {
        'next': page_obj.has_next(),
        'previous': page_obj.has_previous()
    }
    return render(req, 'collection.html', {
        'url': resolve(req.path_info).url_name,
        'session': req.session,
        'total_pages': range(1, total_pages+1),
        'product': page_obj,
        'page_position': page_position_current,
        'current_page': page
    })


def search_collection(req):
    search_query = req.GET['searchText']
    product = Product.objects.filter(
        Name__icontains=search_query, visiblity=True)
    return render(req, 'collection.html', {'url': resolve(req.path_info).url_name, 'session': req.session, 'product': product, 'search_query': search_query})


def cart(req):
    if not req.session['loggedIn']:
        messages.error(req, "Login Required for add to cart")
        return JsonResponse({'status': 401, 'message': 'Login Required'})
    user_id = req.session['user']['id']
    cart_item = Cart.objects.select_related(
        'product').filter(created_by_id=user_id)
    total_cost = reduce(lambda acc, item: acc +
                        calculate_current_price(item.product), cart_item, 0)
    if req.method == 'POST' and req.POST.get('checkout'):
        user = User.objects.get(id=user_id)
        delivery_address = req.POST.get('delivery_address')
        cart_product_id = map(lambda item: item.product_id, cart_item)
        result = ProductOrders.objects.create(
            address=delivery_address,
            order_amount=total_cost,
            order=cart_product_id,
            created_by=user
        )
        return redirect(f"cart/checkout/{result.id}")
    return render(req, 'cart.html', {
        'url': resolve(req.path_info).url_name,
        'session': req.session,
        'cart_items': cart_item,
        'total_cost': round(total_cost, 2)
    })


def checkout(req, order_id):
    order = ProductOrders.objects.select_related(
        'created_by').get(id=order_id)
    client = razorpay.Client(
        auth=(env('RAZORPAY_KEY_ID'), env('RAZORPAY_KEY_SECRET')))
    payment = client.order.create(
        {'amount': int(order.order_amount*100), 'currency': 'INR', 'payment_capture': 1})
    order.razorpay_order_id = payment['id']
    order.save()

    return render(req, 'cart.html', {
        'url': resolve(req.path_info).url_name,
        'session': req.session,
        'order_id': order_id,
        'razorpay_key_id': env('RAZORPAY_KEY_ID'),
        'user_info': {
            'username': order.created_by.username,
            'email': order.created_by.email,
            'mobile': order.created_by.mobile
        },
        'payment': payment
    })
    
def handle_payment_success(req, order_id, razorpay_order_id, razorpay_payment_id, razorpay_signature):
    order = ProductOrders.objects.get(id=order_id, razorpay_order_id=razorpay_order_id)
    order.razorpay_payment_id = razorpay_payment_id
    order.razorpay_order_signature = razorpay_signature
    order.payment_paid = True
    order.save()
    messages.success(req, "Order Placed Successfully")
    Cart.objects.filter(created_by_id=req.session['user']['id']).delete()
    return redirect("/customer/orders")

def customer_orders(req):
    if not req.session['loggedIn']:
        messages.error(req, "Login Required for add to cart")
        return JsonResponse({'status': 401, 'message': 'Login Required'})
    user_id = req.session['user']['id']
    orders = ProductOrders.objects.filter(created_by_id=user_id)
    new_orders = list(map(lambda item: item.serialize_products(), orders))
    return render(req, 'orders.html', {'url': resolve(req.path_info).url_name, 'session': req.session, 'Orders': new_orders, 'user_type': 'Customer'})

def download_invoice(req, order_id):
    if not req.session['loggedIn']:
        messages.error(req, "Login Required for add to cart")
        return JsonResponse({'status': 401, 'message': 'Login Required'})
    user_id = req.session['user']['id']
    order = ProductOrders.objects.select_related('created_by').get(id=order_id, created_by_id=user_id).serialize_products()
    response = HttpResponse(content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="invoice {order.created_by.username}-{order.created_at}.pdf"'
    canvas_obj = canvas.Canvas(response)
    canvas_obj.setFont("Times-Roman", 20)
    canvas_obj.drawString(250, 800, "Invoice")
    canvas_obj.setFont("Times-Roman", 15)
    canvas_obj.drawString(50, 750, f"Username: {order.created_by.username}")
    canvas_obj.drawString(200, 750, f"Address: {order.address}")
    canvas_obj.drawString(350, 750, f"Mobile: {order.created_by.mobile}")
    canvas_obj.drawString(50, 720, f"Payment Mode: {'Online' if order.payment_paid else 'Cash on Delivery'}")
    canvas_obj.drawString(200, 720, f"Order Date: {order.created_at.strftime('%Y-%m-%d')}") 
    canvas_item_position = 690
    for item in order.order:
        canvas_obj.drawString(50, canvas_item_position, f"Name: {item.Name}")
        canvas_obj.drawString(300, canvas_item_position, f"price: {calculate_current_price(item)}")
        canvas_item_position-=30
    canvas_obj.drawString(300, canvas_item_position, f"Final Amount: {order.order_amount}")
    canvas_obj.showPage()
    canvas_obj.save()
    return response

def add_cart(req, product_id):
    if not req.session['loggedIn']:
        messages.error(req, "Login Required for add to cart")
        return JsonResponse({'status': 401, 'message': 'Login Required'})
    try:
        user = User.objects.get(id=req.session['user']['id'])
        product = Product.objects.get(id=product_id)
        Cart(
            created_by=user,
            product=product
        ).save()
        messages.success(req, "Product Added to cart successfully")
    except:
        messages.error(req, "Something Went Wrong")
    return redirect(f"/order/{product_id}")


def remove_cart(req, cart_id):
    if not req.session['loggedIn']:
        messages.error(req, "Login Required for add to cart")
        return JsonResponse({'status': 401, 'message': 'Login Required'})
    try:
        Cart.objects.filter(
            id=cart_id, created_by_id=req.session['user']['id']).delete()
        messages.success(req, "Product Removed Successfully")
    except:
        messages.error(req, "Something Wrong")
    return redirect("/cart")


def about(req):
    return render(req, 'about.html', {'url': resolve(req.path_info).url_name, 'session': req.session})


def index(req):
    return render(req, 'Home.html', {'url': resolve(req.path_info).url_name, 'session': req.session})


def contact(req):
    if req.method == 'POST':
        name = req.POST.get('name')
        email = req.POST.get('email')
        msg = req.POST.get('msg')
        result = Contact(name=name, email=email, comment=msg).save()
        print(result)
        messages.success(req, "Contact Form Filled Successfully")
        return redirect('/contact')
    return render(req, 'contact.html', {'url': resolve(req.path_info).url_name, 'session': req.session})


def becomeSeller(req):
    try:
        id = int(req.session['user']['id'])
        user = User.objects.get(id=id)
        new_status = not user.__dict__['isSeller']
        User.objects.filter(id=id).update(isSeller=new_status)
        req.session['user'] = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'mobile': user.mobile,
            'isSeller': new_status
        }
        return JsonResponse({
            "success": True,
            "operation": new_status
        })
    except:
        return JsonResponse({"success": False})


def login(req):
    if req.method == 'POST' and req.POST.get('login'):
        user = req.POST.get('username')
        password = req.POST.get('password')
        keep_logged_in = req.POST.get('keep_logged_in')
        try:
            user_exists = User.objects.get(Q(username=user) | Q(email=user))
            if (user_exists.validate_password(password)):
                res = redirect('/')
                req.session['loggedIn'] = True
                req.session['user'] = {
                    'id': user_exists.id,
                    'username': user_exists.username,
                    'email': user_exists.email,
                    'mobile': user_exists.mobile,
                    'isSeller': user_exists.isSeller
                }

                messages.success(req, "Logged In Success")
                cookie_age = 0

                if keep_logged_in is not None:
                    cookie_age = 36000  # This cookies will activate for 10hrs

                res.set_cookie('username', user, max_age=cookie_age)
                res.set_cookie('password', password, max_age=cookie_age)
                return res
            messages.error(req, "Invalid Credentials")
            return redirect('/login')
        except Exception as e:
            print(e)
            messages.error(req, "Invalid Credentials")
            return redirect('/login')
    userDataCookie = {}
    if req.COOKIES.get('username') and req.COOKIES.get('password'):
        userDataCookie['username'] = req.COOKIES.get('username')
        userDataCookie['password'] = req.COOKIES.get('password')
    return render(req, 'login.html', {'url': resolve(req.path_info).url_name, 'session': req.session, 'cookie': userDataCookie})


def Seller_panel(req):
    if not req.session['loggedIn'] or len(User.objects.filter(Q(id=req.session['user']['id']) & Q(isSeller=True))) == 0:
        messages.error(req, "Ensure login and Seller status")
        return redirect('/')

    if req.method == 'POST' and req.POST.get('productAdd'):
        try:
            product_name = req.POST.get('name')
            price = req.POST.get('price')
            discount = req.POST.get('discount')
            image = req.FILES['image']
            description = req.POST.get('description')
            user = User.objects.get(id=req.session['user']['id'])
            Product(
                Name=product_name,
                Image=image,
                price=price,
                discount=discount,
                description=description,
                uploaded_by=user
            ).save()
            messages.success(req, "Product Added Successfully")
        except Exception as e:
            print(e)
            messages.error(req, "Something Went Wrong")
        finally:
            return redirect('/seller')

    products = Product.objects.filter(uploaded_by_id=req.session['user']['id'])
    return render(req, 'seller_panel.html', {'url': resolve(req.path_info).url_name, 'session': req.session, 'Products': products})

def seller_orders(req):
    if not req.session['loggedIn'] or len(User.objects.filter(Q(id=req.session['user']['id']) & Q(isSeller=True))) == 0:
        messages.error(req, "Ensure login and Seller status")
        return redirect('/')
    seller_id = req.session['user']['id']
    orders = ProductOrders.objects.filter(created_by_id=seller_id)
    new_orders = list(map(lambda item: item.serialize_products(), orders))
    return render(req, 'orders.html', {'url': resolve(req.path_info).url_name, 'session': req.session, 'Orders': new_orders, 'user_type': 'Seller'})

def delivery_status_change(req, order_id, status):
    ProductOrders.objects.filter(id=order_id).update(delivery_status=status)
    return JsonResponse({ 'status' : 200 })

def product_update(req, product_id):
    if not req.session['loggedIn'] or len(User.objects.filter(Q(id=req.session['user']['id']) & Q(isSeller=True))) == 0:
        messages.error(req, "Ensure login and Seller status")
        return redirect('/')

    if req.method == 'POST' and req.POST.get('productUpdate'):
        try:
            product_name = req.POST.get('name')
            price = req.POST.get('price')
            discount = req.POST.get('discount')
            description = req.POST.get('description')
            product = Product.objects.get(
                id=product_id, uploaded_by_id=req.session['user']['id'])
            if 'image' in req.FILES:
                # product.Image.delete()
                uploaded_image = req.FILES['image']
                fs = FileSystemStorage(
                    location=settings.MEDIA_ROOT + '/product/')
                filename = fs.save(uploaded_image.name, uploaded_image)
                product.Image = 'product/' + filename

            product.Name = product_name
            product.price = price
            product.discount = discount
            product.description = description
            product.save()
            messages.success(req, "Product Updated Successfully")
        except:
            messages.error(req, "Something Went To Wrong")
        return redirect('/seller')

    update_product = {}

    try:
        update_product = Product.objects.get(
            id=product_id, uploaded_by_id=req.session['user']['id'])
    except:
        messages.error(req, "Product Not Found")

    return render(req, 'update_product.html', {'url': resolve(req.path_info).url_name, 'session': req.session, 'update_product': update_product, 'product_id': product_id})


def change_product_visiblity(req):
    responce = {}
    product_visiblity = True if req.GET.get('visiblity') == "True" else False
    product_id = req.GET.get('product-id', None)
    try:
        Product.objects.filter(Q(uploaded_by_id=req.session['user']['id']) & Q(
            id=product_id)).update(visiblity=(not product_visiblity))
        print(req.GET.get('visiblity'))
        responce['status'] = 200
        responce['product_visiblity'] = not product_visiblity
    except:
        responce['status'] = 500
        responce['product_visiblity'] = product_visiblity
    finally:
        return JsonResponse(responce)


def remove_product(req, product_id):
    try:
        product = Product.objects.get(
            id=product_id, uploaded_by_id=req.session['user']['id'])
        product.Image.delete()
        product.delete()
        messages.success(req, 'Product Removed Successfully')
    except Product.DoesNotExist:
        messages.error(
            req, 'Product does not exist or you are not authorized to delete it')
    except:
        messages.error(req, 'Something Went Wrong')

    return redirect('/seller')


def Signout(req):
    req.session['loggedIn'] = False
    req.session['user'] = {}
    res = redirect('/')
    res.set_cookie('username', '', max_age=0)
    res.set_cookie('password', '', max_age=0)
    messages.success(req, 'Signout successfully')
    return res


def Signup(req):
    if req.method == 'POST' and req.POST.get('signupFrm'):
        username = req.POST.get('name')
        mobile = int(req.POST.get('mobile'))
        email = req.POST.get('email')
        password = req.POST.get('password')
        exist = User.objects.filter(
            Q(username=username) | Q(email=email)).exists()
        if not exist:
            try:
                User(username=username, email=email,
                     mobile=mobile, password=password).save()
                messages.success(req, "Account Created Successfully")
            except:
                messages.error(req, 'Something Went Wrong')
            finally:
                return redirect('/signup')
        messages.error(req, "Username or Password Already Registered")
        return redirect('/signup')
    return render(req, 'signup.html', {'url': resolve(req.path_info).url_name, 'session': req.session}, status=201)


def Order(req, product_id):
    featured_product = Product.objects.order_by("-rating")[:3]
    try:
        current_product = Product.objects.get(id=product_id)
    except:
        messages.error(req, 'Product Not Found')
        return redirect('/collections/1/None')

    return render(req, 'order.html', {
        'url': resolve(req.path_info).url_name,
        'session': req.session,
        'featured_product': featured_product,
        'current_product': current_product
    })
