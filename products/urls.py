from django.urls import path
from .views import product_list, product_detail, add_to_cart, cart
urlpatterns = [
    path('', product_list, name='product_list'),
    path('product/<int:id>/', product_detail, name='product_detail'),
    path('cart/add/<int:id>/', add_to_cart, name='add_to_cart'),
    path('cart/', cart, name='cart'),
]