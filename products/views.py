
from django.shortcuts import render,redirect
from .models import Product


def product_list(request):
    products = Product.objects.all()
    return render(request, 'products/products.html', {'products': products})
def product_detail(request, id):
    product = Product.objects.get(id=id)
    return render(request, 'products/product_detail.html', {'product': product})
def add_to_cart(request, id):
    cart = request.session.get('cart', [])
    cart.append(id)
    request.session['cart'] = cart
    return redirect('/cart/')
def cart(request):
    cart_ids = request.session.get('cart', [])
    products = Product.objects.filter(id__in=cart_ids)
    total = sum(product.price for product in products)

    return render(
        request,
        'products/cart.html',
        {'products': products, 'total': total}
    )