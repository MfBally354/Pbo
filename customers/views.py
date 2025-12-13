from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db import transaction
from restaurants.models import Restaurant, MenuItem
from orders.models import Order, OrderItem
from accounts.decorators import role_required
import json


# ============================
# CUSTOMER DASHBOARD
# ============================
@login_required
@role_required(['customer'])
def customer_dashboard(request):
    """Dashboard utama customer"""
    # Ambil pesanan aktif customer
    active_orders = Order.objects.filter(
        customer=request.user,
        status__in=['pending', 'accepted', 'preparing', 'ready_for_pickup', 'picked', 'delivering']
    ).order_by('-created_at')
    
    # Ambil riwayat pesanan
    completed_orders = Order.objects.filter(
        customer=request.user,
        status__in=['delivered', 'completed']
    ).order_by('-created_at')[:5]
    
    context = {
        'active_orders': active_orders,
        'completed_orders': completed_orders,
    }
    
    return render(request, 'customer/dashboard.html', context)


# ============================
# BROWSE RESTAURANTS
# ============================
@login_required
@role_required(['customer'])
def browse_restaurants(request):
    """Lihat daftar restoran yang tersedia"""
    restaurants = Restaurant.objects.all()
    
    context = {
        'restaurants': restaurants,
    }
    
    return render(request, 'customer/browse_restaurants.html', context)


@login_required
@role_required(['customer'])
def view_restaurant_menu(request, restaurant_id):
    """Lihat menu dari restoran tertentu"""
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)
    menu_items = MenuItem.objects.filter(restaurant=restaurant, is_available=True)
    
    context = {
        'restaurant': restaurant,
        'menu_items': menu_items,
    }
    
    return render(request, 'customer/restaurant_menu.html', context)


# ============================
# SHOPPING CART (SESSION-BASED)
# ============================
@login_required
@role_required(['customer'])
def add_to_cart(request):
    """Tambah item ke cart"""
    if request.method == 'POST':
        menu_item_id = request.POST.get('menu_item_id')
        quantity = int(request.POST.get('quantity', 1))
        
        menu_item = get_object_or_404(MenuItem, id=menu_item_id)
        
        # Ambil cart dari session
        cart = request.session.get('cart', {})
        
        # Key berdasarkan menu_item_id
        item_key = str(menu_item_id)
        
        if item_key in cart:
            cart[item_key]['quantity'] += quantity
        else:
            cart[item_key] = {
                'menu_item_id': menu_item.id,
                'name': menu_item.name,
                'price': str(menu_item.price),
                'quantity': quantity,
                'restaurant_id': menu_item.restaurant.id,
                'restaurant_name': menu_item.restaurant.name
            }
        
        request.session['cart'] = cart
        request.session.modified = True
        
        messages.success(request, f"{menu_item.name} ditambahkan ke keranjang!")
        return redirect('customers:view_restaurant_menu', restaurant_id=menu_item.restaurant.id)
    
    return redirect('customers:browse_restaurants')


@login_required
@role_required(['customer'])
def view_cart(request):
    """Lihat isi cart"""
    cart = request.session.get('cart', {})
    
    total_price = 0
    cart_items = []
    
    for item_key, item_data in cart.items():
        subtotal = float(item_data['price']) * item_data['quantity']
        total_price += subtotal
        
        cart_items.append({
            'id': item_key,
            'name': item_data['name'],
            'price': item_data['price'],
            'quantity': item_data['quantity'],
            'subtotal': subtotal,
            'restaurant_name': item_data['restaurant_name']
        })
    
    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    
    return render(request, 'customer/cart.html', context)


@login_required
@role_required(['customer'])
def remove_from_cart(request, item_id):
    """Hapus item dari cart"""
    cart = request.session.get('cart', {})
    
    if str(item_id) in cart:
        del cart[str(item_id)]
        request.session['cart'] = cart
        request.session.modified = True
        messages.success(request, "Item dihapus dari keranjang!")
    
    return redirect('customers:view_cart')


@login_required
@role_required(['customer'])
def update_cart_item(request, item_id):
    """Update quantity item di cart"""
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity', 1))
        cart = request.session.get('cart', {})
        
        if str(item_id) in cart:
            if quantity > 0:
                cart[str(item_id)]['quantity'] = quantity
            else:
                del cart[str(item_id)]
            
            request.session['cart'] = cart
            request.session.modified = True
    
    return redirect('customers:view_cart')


# ============================
# CHECKOUT & ORDER
# ============================
@login_required
@role_required(['customer'])
def checkout(request):
    """Checkout dan buat order"""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        
        if not cart:
            messages.error(request, "Keranjang kosong!")
            return redirect('customers:view_cart')
        
        # Ambil data dari form
        delivery_address = request.POST.get('delivery_address')
        notes = request.POST.get('notes', '')
        
        # Hitung total harga
        total_price = sum(
            float(item['price']) * item['quantity'] 
            for item in cart.values()
        )
        
        # Ambil restaurant_id (asumsi: semua item dari resto yang sama)
        first_item = next(iter(cart.values()))
        restaurant = get_object_or_404(Restaurant, id=first_item['restaurant_id'])
        
        try:
            with transaction.atomic():
                # Buat order
                order = Order.objects.create(
                    customer=request.user,
                    restaurant=restaurant,
                    total_price=total_price,
                    notes=notes,
                    status=Order.STATUS_PENDING
                )
                
                # Buat order items
                for item_data in cart.values():
                    OrderItem.objects.create(
                        order=order,
                        item_name=item_data['name'],
                        quantity=item_data['quantity'],
                        price=item_data['price']
                    )
                
                # Kosongkan cart
                request.session['cart'] = {}
                request.session.modified = True
                
                messages.success(request, f"Pesanan #{order.id} berhasil dibuat!")
                return redirect('customers:order_detail', order_id=order.id)
        
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect('customers:view_cart')
    
    # GET request - tampilkan form checkout
    cart = request.session.get('cart', {})
    
    if not cart:
        messages.error(request, "Keranjang kosong!")
        return redirect('customers:browse_restaurants')
    
    total_price = sum(
        float(item['price']) * item['quantity'] 
        for item in cart.values()
    )
    
    context = {
        'cart': cart,
        'total_price': total_price,
    }
    
    return render(request, 'customer/checkout.html', context)


# ============================
# ORDER MANAGEMENT
# ============================
@login_required
@role_required(['customer'])
def customer_orders(request):
    """Lihat semua pesanan customer"""
    orders = Order.objects.filter(customer=request.user).order_by('-created_at')
    
    context = {
        'orders': orders,
    }
    
    return render(request, 'customer/orders.html', context)


@login_required
@role_required(['customer'])
def order_detail(request, order_id):
    """Detail pesanan"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    context = {
        'order': order,
    }
    
    return render(request, 'customer/order_detail.html', context)


@login_required
@role_required(['customer'])
def track_order(request, order_id):
    """Track status pesanan (AJAX)"""
    order = get_object_or_404(Order, id=order_id, customer=request.user)
    
    data = {
        'order_id': order.id,
        'status': order.status,
        'status_display': order.get_status_display(),
        'restaurant': order.restaurant.name,
        'driver': order.driver.username if order.driver else 'Belum ada driver',
        'total_price': str(order.total_price),
        'created_at': order.created_at.strftime('%d %b %Y %H:%M'),
    }
    
    return JsonResponse(data)