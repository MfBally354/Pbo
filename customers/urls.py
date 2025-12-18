from django.urls import path
from . import views

app_name = 'customers'

urlpatterns = [
    # Dashboard Customer
    path('dashboard/', views.customer_dashboard, name='customer_dashboard'),
    
    # Browse Restaurants
    path('restaurants/', views.browse_restaurants, name='browse_restaurants'),
    path('restaurants/<int:restaurant_id>/menu/', views.view_restaurant_menu, name='view_restaurant_menu'),
    
    # Cart & Checkout
    path('cart/', views.view_cart, name='view_cart'),
    path('cart/add/', views.add_to_cart, name='add_to_cart'),
    path('cart/remove/<int:item_id>/', views.remove_from_cart, name='remove_from_cart'),
    path('cart/update/<int:item_id>/', views.update_cart_item, name='update_cart_item'),
    path('checkout/', views.checkout, name='checkout'),
    
    # Orders
    path('orders/', views.customer_orders, name='customer_orders'),
    path('orders/<int:order_id>/', views.order_detail, name='order_detail'),
    path('orders/<int:order_id>/track/', views.track_order, name='track_order'),
]