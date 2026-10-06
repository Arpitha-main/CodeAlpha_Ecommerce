from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.db.models import Q

from .models import Product, Order, Wishlist ,Category


# =========================
# PRODUCT LIST
# =========================

def product_list(request):

    products = Product.objects.all()

    search_query = request.GET.get("q", "").strip()
    category_id = request.GET.get("category", "").strip()

    # SEARCH
    if search_query:
        products = products.filter(
            Q(name__icontains=search_query) |
            Q(description__icontains=search_query)
        )

    # CATEGORY FILTER
    if category_id:
        products = products.filter(
            category_id=category_id
        )

    categories = Category.objects.all()

    return render(
        request,
        "products/products.html",
        {
            "products": products,
            "categories": categories,
        }
    )


# =========================
# PRODUCT DETAIL
# =========================

def product_detail(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    return render(
        request,
        "products/product_detail.html",
        {
            "product": product
        }
    )


# =========================
# CART
# =========================

def cart(request):

    cart_data = request.session.get("cart", {})

    cart_items = []
    total = 0

    for product_id, quantity in cart_data.items():

        product = get_object_or_404(
            Product,
            id=int(product_id)
        )

        subtotal = product.price * quantity

        cart_items.append({
            "product": product,
            "quantity": quantity,
            "subtotal": subtotal,
        })

        total += subtotal

    return render(
        request,
        "products/cart.html",
        {
            "cart_items": cart_items,
            "total": total,
        }
    )


# =========================
# ADD TO CART
# =========================

def add_to_cart(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    # Don't add if out of stock
    if product.stock <= 0:
        return redirect(
            "product_detail",
            product_id=product.id
        )

    cart_data = request.session.get(
        "cart",
        {}
    )

    product_id = str(product_id)

    current_quantity = cart_data.get(
        product_id,
        0
    )

    # Don't allow cart quantity above available stock
    if current_quantity < product.stock:

        cart_data[product_id] = (
            current_quantity + 1
        )

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


# =========================
# REMOVE ONE FROM CART
# =========================

def remove_from_cart(request, product_id):

    cart_data = request.session.get(
        "cart",
        {}
    )

    product_id = str(product_id)

    if product_id in cart_data:

        if cart_data[product_id] > 1:

            cart_data[product_id] -= 1

        else:

            del cart_data[product_id]

    request.session["cart"] = cart_data
    request.session.modified = True

    return redirect("cart")


# =========================
# REGISTER
# =========================

def register(request):

    if request.method == "POST":

        form = UserCreationForm(
            request.POST
        )

        if form.is_valid():

            user = form.save()

            login(
                request,
                user
            )

            return redirect("/")

    else:

        form = UserCreationForm()

    return render(
        request,
        "products/register.html",
        {
            "form": form
        }
    )


# =========================
# LOGIN
# =========================

def login_view(request):

    if request.method == "POST":

        form = AuthenticationForm(
            request,
            data=request.POST
        )

        if form.is_valid():

            user = form.get_user()

            login(
                request,
                user
            )

            return redirect("/")

    else:

        form = AuthenticationForm()

    return render(
        request,
        "products/login.html",
        {
            "form": form
        }
    )


# =========================
# LOGOUT
# =========================

def logout_view(request):

    logout(request)

    return redirect("/")


# =========================
# CHECKOUT
# =========================

@login_required
def checkout(request):

    cart_data = request.session.get(
        "cart",
        {}
    )

    # Empty cart
    if not cart_data:
        return redirect("/cart/")

    total = 0

    # Calculate total
    for product_id, quantity in cart_data.items():

        product = get_object_or_404(
            Product,
            id=int(product_id)
        )

        total += product.price * quantity

    # PLACE ORDER
    if request.method == "POST":

        # Check stock before placing order
        for product_id, quantity in cart_data.items():

            product = get_object_or_404(
                Product,
                id=int(product_id)
            )

            if quantity > product.stock:

                return redirect("/cart/")

        # Reduce stock
        for product_id, quantity in cart_data.items():

            product = get_object_or_404(
                Product,
                id=int(product_id)
            )

            product.stock -= quantity

            product.save()

        # Create order
        Order.objects.create(
            user=request.user,
            total_price=total
        )

        # Empty cart
        request.session["cart"] = {}

        request.session.modified = True

        return redirect("/orders/")

    return render(
        request,
        "products/checkout.html",
        {
            "total": total
        }
    )


# =========================
# ORDERS
# =========================

@login_required
def orders(request):

    user_orders = Order.objects.filter(
        user=request.user
    ).order_by(
        "-created_at"
    )

    return render(
        request,
        "products/orders.html",
        {
            "orders": user_orders
        }
    )


# =========================
# WISHLIST
# =========================

@login_required
def wishlist(request):

    wishlist_items = Wishlist.objects.filter(
        user=request.user
    ).select_related(
        "product"
    )

    return render(
        request,
        "products/wishlist.html",
        {
            "wishlist_items": wishlist_items
        }
    )


# =========================
# ADD TO WISHLIST
# =========================

@login_required
def add_to_wishlist(request, product_id):

    product = get_object_or_404(
        Product,
        id=product_id
    )

    Wishlist.objects.get_or_create(
        user=request.user,
        product=product
    )

    return redirect(
        request.META.get(
            "HTTP_REFERER",
            "/"
        )
    )


# =========================
# REMOVE FROM WISHLIST
# =========================

@login_required
def remove_from_wishlist(
    request,
    product_id
):

    Wishlist.objects.filter(
        user=request.user,
        product_id=product_id
    ).delete()

    return redirect("wishlist")


# =========================
# CLEAR WISHLIST
# =========================

@login_required
def clear_wishlist(request):

    Wishlist.objects.filter(
        user=request.user
    ).delete()

    return redirect("wishlist")