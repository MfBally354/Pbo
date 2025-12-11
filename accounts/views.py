from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.views import LoginView
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomerRegisterForm, DriverRegisterForm, RestaurantRegisterForm
from .models import User
from django.http import JsonResponse
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from orders.models import Order


# =============================
# CUSTOM LOGIN VIEW
# =============================
class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'

    def form_valid(self, form):
        user = form.get_user()
        # jika role driver/resto harus approved
        if hasattr(user, 'role'):
            if user.role in ['driver', 'restaurant'] and not user.is_approved:
                messages.error(self.request, "Akun Anda belum disetujui admin.")
                return redirect('accounts:login')
        return super().form_valid(form)


# =============================
# REGISTRASI
# =============================
def register_customer(request):
    if request.method == 'POST':
        form = CustomerRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, "Registrasi sukses. Selamat datang!")
            return redirect('home')
    else:
        form = CustomerRegisterForm()
    return render(request, 'accounts/register_customer.html', {'form': form})


def register_driver(request):
    if request.method == 'POST':
        form = DriverRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registrasi driver berhasil. Menunggu persetujuan admin.")
            return redirect('accounts:login')
    else:
        form = DriverRegisterForm()
    return render(request, 'accounts/register_driver.html', {'form': form})


def register_restaurant(request):
    if request.method == 'POST':
        form = RestaurantRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            messages.success(request, "Registrasi restoran berhasil. Menunggu persetujuan admin.")
            return redirect('accounts:login')
    else:
        form = RestaurantRegisterForm()
    return render(request, 'accounts/register_restaurant.html', {'form': form})


# =============================
# LOGIN / LOGOUT
# =============================
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)

            # Admin masuk ke admin panel
            if user.role == "admin":
                return redirect("accounts:admin_dashboard")

            # Driver
            if user.role == "driver":
                return redirect("drivers:dashboard")

            # Restaurant
            if user.role == "restaurant":
                return redirect("restaurants:dashboard")

            # Customer
            return redirect("home")

        return render(request, "accounts/login.html", {
            "error": "Username atau password salah"
        })

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


# =============================
# DECORATOR ADMIN
# =============================
def admin_required(view_func):
    return user_passes_test(lambda u: u.is_authenticated and u.role == "admin")(view_func)


# =============================
# DASHBOARD ADMIN
# =============================
@admin_required
def admin_dashboard(request):
    from orders.models import Order
    from chats.models import SupportTicket
    
    # Count statistics
    pending_count = User.objects.filter(is_approved=False, role__in=["driver", "restaurant"]).count()
    drivers_count = User.objects.filter(role="driver").count()
    restaurants_count = User.objects.filter(role="restaurant").count()
    
    # Active orders
    active_orders = Order.objects.filter(status__in=['pending', 'confirmed', 'preparing', 'delivering']).count()
    
    # Support tickets
    support_count = SupportTicket.objects.filter(status__in=['open', 'in_progress']).count()
    
    context = {
        'pending_count': pending_count,
        'drivers_count': drivers_count,
        'restaurants_count': restaurants_count,
        'active_orders': active_orders,
        'support_count': support_count,
    }
    
    return render(request, "adminpanel/dashboard.html", context)


# =============================
# APPROVAL AKUN
# =============================
# =============================
# APPROVAL AKUN
# =============================
@admin_required
def account_approvals(request):
    pending = User.objects.filter(is_approved=False, role__in=["driver", "restaurant"])
    
    # Statistics
    pending_count = pending.count()
    pending_drivers = pending.filter(role='driver').count()
    pending_restaurants = pending.filter(role='restaurant').count()
    
    context = {
        "pending": pending,
        "pending_count": pending_count,
        "pending_drivers": pending_drivers,
        "pending_restaurants": pending_restaurants,
    }
    
    return render(request, "adminpanel/approvals.html", context)


@admin_required
def approve_user(request, user_id):
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            user.is_approved = True
            user.save()
            messages.success(request, f"User '{user.username}' approved successfully!")
        except User.DoesNotExist:
            messages.error(request, "User not found!")
    return redirect("accounts:approvals")


@admin_required
def reject_user(request, user_id):
    """Reject dan hapus user yang belum approved"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            username = user.username
            user.delete()
            messages.success(request, f"User '{username}' rejected and removed!")
        except User.DoesNotExist:
            messages.error(request, "User not found!")
    return redirect("accounts:approvals")


# =============================
# MANAGE DRIVERS
# =============================
@admin_required
def manage_drivers(request):
    drivers = User.objects.filter(role="driver")
    return render(request, "adminpanel/drivers.html", {"drivers": drivers})


# =============================
# MANAGE RESTAURANTS
# =============================
@admin_required
def manage_restaurants(request):
    restos = User.objects.filter(role="restaurant")
    return render(request, "adminpanel/restaurants.html", {"restaurants": restos})


# =============================
# MANAGE ORDERS
# =============================
@admin_required
# GANTI fungsi manage_orders yang lama dengan ini
# DAN TAMBAHKAN fungsi-fungsi baru di bawahnya

@admin_required
def manage_orders(request):
    """Halaman manage orders untuk admin"""
    from orders.models import Order
    
    # Get all orders
    orders = Order.objects.select_related('customer', 'restaurant', 'driver').prefetch_related('items').all()
    
    # Statistics
    total_orders = orders.count()
    pending_orders = orders.filter(status='pending').count()
    delivering_orders = orders.filter(status='delivering').count()
    completed_orders = orders.filter(status='completed').count()
    active_orders = orders.filter(status__in=['pending', 'confirmed', 'preparing', 'delivering']).count()
    
    context = {
        'orders': orders,
        'total_orders': total_orders,
        'pending_orders': pending_orders,
        'delivering_orders': delivering_orders,
        'completed_orders': completed_orders,
        'active_orders': active_orders,
    }
    
    return render(request, "adminpanel/orders.html", context)


@admin_required
def add_order(request):
    """Tambah order baru (manual oleh admin)"""
    if request.method == 'POST':
        from orders.models import Order, OrderItem
        
        try:
            customer_id = request.POST.get('customer_id')
            restaurant_id = request.POST.get('restaurant_id')
            driver_id = request.POST.get('driver_id')
            total_price = request.POST.get('total_price')
            delivery_address = request.POST.get('delivery_address')
            notes = request.POST.get('notes')
            
            # Create order
            order = Order.objects.create(
                customer_id=customer_id,
                restaurant_id=restaurant_id,
                driver_id=driver_id if driver_id else None,
                total_price=total_price,
                delivery_address=delivery_address,
                notes=notes,
                status='pending'
            )
            
            messages.success(request, f"Order #{order.id} created successfully!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('accounts:orders')
    
    return redirect('accounts:orders')


@admin_required
def update_order_status(request, order_id):
    """Update status order"""
    if request.method == 'POST':
        from orders.models import Order
        
        try:
            order = Order.objects.get(id=order_id)
            new_status = request.POST.get('status')
            
            if new_status in dict(Order.STATUS_CHOICES):
                order.status = new_status
                order.save()
                messages.success(request, f"Order #{order_id} status updated to {new_status}!")
            else:
                messages.error(request, "Invalid status!")
        except Order.DoesNotExist:
            messages.error(request, "Order not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('accounts:orders')


@admin_required
def assign_driver(request, order_id):
    """Assign driver ke order"""
    if request.method == 'POST':
        from orders.models import Order
        
        try:
            order = Order.objects.get(id=order_id)
            driver_id = request.POST.get('driver_id')
            
            if driver_id:
                order.driver_id = driver_id
                order.status = 'confirmed'  # Auto confirm when driver assigned
                order.save()
                messages.success(request, f"Driver assigned to Order #{order_id}!")
            else:
                messages.error(request, "Please select a driver!")
        except Order.DoesNotExist:
            messages.error(request, "Order not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('accounts:orders')


@admin_required
def delete_order(request, order_id):
    """Hapus order"""
    if request.method == 'POST':
        from orders.models import Order
        
        try:
            order = Order.objects.get(id=order_id)
            order.delete()
            messages.success(request, f"Order #{order_id} deleted successfully!")
        except Order.DoesNotExist:
            messages.error(request, "Order not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('accounts:orders')


@admin_required
def get_order_api(request, order_id):
    """API untuk ambil detail order"""
    from orders.models import Order
    
    try:
        order = Order.objects.select_related('customer', 'restaurant', 'driver').prefetch_related('items').get(id=order_id)
        
        items_data = []
        for item in order.items.all():
            items_data.append({
                'name': item.item_name,
                'quantity': item.quantity,
                'price': str(item.price),
                'subtotal': str(item.subtotal())
            })
        
        data = {
            'id': order.id,
            'customer': {
                'id': order.customer.id,
                'name': order.customer.username,
                'email': order.customer.email,
            },
            'restaurant': {
                'id': order.restaurant.id,
                'name': order.restaurant.username,
            },
            'driver': {
                'id': order.driver.id if order.driver else None,
                'name': order.driver.username if order.driver else 'Not assigned',
            },
            'status': order.status,
            'total_price': str(order.total_price),
            'delivery_address': order.delivery_address or 'N/A',
            'notes': order.notes or 'No notes',
            'items': items_data,
            'created_at': order.created_at.strftime('%d %b %Y %H:%M'),
            'updated_at': order.updated_at.strftime('%d %b %Y %H:%M'),
        }
        
        return JsonResponse(data)
    except Order.DoesNotExist:
        return JsonResponse({'error': 'Order not found'}, status=404)


@admin_required
def get_users_for_order(request):
    """API untuk ambil list users (customer, restaurant, driver) untuk form add order"""
    customers = User.objects.filter(role='customer').values('id', 'username', 'email')
    restaurants = User.objects.filter(role='restaurant', is_approved=True).values('id', 'username')
    drivers = User.objects.filter(role='driver', is_approved=True).values('id', 'username')
    
    return JsonResponse({
        'customers': list(customers),
        'restaurants': list(restaurants),
        'drivers': list(drivers),
    })

@admin_required
def users_for_order_api(request):
    customers = User.objects.filter(role="customer")
    restaurants = User.objects.filter(role="restaurant")
    drivers = User.objects.filter(role="driver")

    data = {
        "customers": [
            {"id": c.id, "username": c.username, "email": c.email}
        for c in customers],

        "restaurants": [
            {"id": r.id, "username": r.username}
        for r in restaurants],

        "drivers": [
            {"id": d.id, "username": d.username}
        for d in drivers]
    }

    return JsonResponse(data)


# =============================
# ADMIN CHAT
# =============================
@admin_required
def admin_chat(request):
    return render(request, "adminpanel/chat.html")


# =============================
# CRUD RESTAURANTS
# =============================

@admin_required
def add_restaurant(request):
    """Tambah restaurant baru"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        restaurant_name = request.POST.get('restaurant_name')
        phone = request.POST.get('phone')
        address = request.POST.get('address')

        try:
            # Cek username sudah ada atau belum
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists!")
                return redirect('accounts:restaurants')

            # Buat user baru
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                role='restaurant',
                is_approved=True  # Langsung approved karena dibuat admin
            )

            # Buat atau update profile
            from accounts.models import RestaurantProfile
            RestaurantProfile.objects.update_or_create(
                user=user,
                defaults={
                    'restaurant_name': restaurant_name,
                    'phone': phone,
                    'address': address,
                }
            )

            messages.success(request, f"Restaurant '{restaurant_name}' added successfully!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('accounts:restaurants')

    return redirect('accounts:restaurants')


@admin_required
def edit_restaurant(request, user_id):
    """Edit restaurant"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)

            # Update user
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')

            # Update password hanya jika diisi
            new_password = request.POST.get('password')
            if new_password:
                user.password = make_password(new_password)

            user.save()

            # Update profile
            from accounts.models import RestaurantProfile
            profile, created = RestaurantProfile.objects.get_or_create(user=user)
            profile.restaurant_name = request.POST.get('restaurant_name')
            profile.phone = request.POST.get('phone')
            profile.address = request.POST.get('address')
            profile.save()

            messages.success(request, "Restaurant updated successfully!")
        except User.DoesNotExist:
            messages.error(request, "Restaurant not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

        return redirect('accounts:restaurants')

    return redirect('accounts:restaurants')


@admin_required
def delete_restaurant(request, user_id):
    """Hapus restaurant"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, role='restaurant')
            restaurant_name = user.username
            user.delete()
            messages.success(request, f"Restaurant '{restaurant_name}' deleted successfully!")
        except User.DoesNotExist:
            messages.error(request, "Restaurant not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")

    return redirect('accounts:restaurants')


@admin_required
def get_restaurant_api(request, user_id):
    """API untuk ambil data restaurant (untuk edit modal)"""
    try:
        user = User.objects.get(id=user_id, role='restaurant')

        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_approved': user.is_approved,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime('%d %b %Y'),
            'restaurant_name': '',
            'phone': '',
            'address': '',
        }

        # Ambil data profile jika ada
        if hasattr(user, 'restaurantprofile'):
            profile = user.restaurantprofile
            data.update({
                'restaurant_name': profile.restaurant_name or '',
                'phone': profile.phone or '',
                'address': profile.address or '',
            })

        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Restaurant not found'}, status=404)

@admin_required
def get_users_for_order(request):
    """API untuk ambil list users (customer, restaurant, driver) untuk form add order"""
    customers = User.objects.filter(role='customer').values('id', 'username', 'email')
    restaurants = User.objects.filter(role='restaurant', is_approved=True).values('id', 'username')
    drivers = User.objects.filter(role='driver', is_approved=True).values('id', 'username')
    
    return JsonResponse({
        'customers': list(customers),
        'restaurants': list(restaurants),
        'drivers': list(drivers),
    })

# =============================
# CRUD DRIVERS
# =============================

@admin_required
def add_driver(request):
    """Tambah driver baru"""
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        full_name = request.POST.get('full_name')
        phone = request.POST.get('phone')
        vehicle_type = request.POST.get('vehicle_type')
        vehicle_number = request.POST.get('vehicle_number')
        
        try:
            if User.objects.filter(username=username).exists():
                messages.error(request, f"Username '{username}' already exists!")
                return redirect('accounts:drivers')
            
            user = User.objects.create(
                username=username,
                email=email,
                password=make_password(password),
                role='driver',
                is_approved=True
            )
            
            from accounts.models import DriverProfile
            DriverProfile.objects.update_or_create(
                user=user,
                defaults={
                    'full_name': full_name,
                    'phone': phone,
                    'vehicle_type': vehicle_type,
                    'vehicle_number': vehicle_number,
                }
            )
            
            messages.success(request, f"Driver '{full_name}' added successfully!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('accounts:drivers')
    
    return redirect('accounts:drivers')


@admin_required
def edit_driver(request, user_id):
    """Edit driver"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id)
            
            user.username = request.POST.get('username')
            user.email = request.POST.get('email')
            
            new_password = request.POST.get('password')
            if new_password:
                user.password = make_password(new_password)
            
            user.save()
            
            from accounts.models import DriverProfile
            profile, created = DriverProfile.objects.get_or_create(user=user)
            profile.full_name = request.POST.get('full_name')
            profile.phone = request.POST.get('phone')
            profile.vehicle_type = request.POST.get('vehicle_type')
            profile.vehicle_number = request.POST.get('vehicle_number')
            profile.save()
            
            messages.success(request, "Driver updated successfully!")
        except User.DoesNotExist:
            messages.error(request, "Driver not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
        
        return redirect('accounts:drivers')
    
    return redirect('accounts:drivers')


@admin_required
def delete_driver(request, user_id):
    """Hapus driver"""
    if request.method == 'POST':
        try:
            user = User.objects.get(id=user_id, role='driver')
            driver_name = user.username
            user.delete()
            messages.success(request, f"Driver '{driver_name}' deleted successfully!")
        except User.DoesNotExist:
            messages.error(request, "Driver not found!")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    
    return redirect('accounts:drivers')


@admin_required
def get_driver_api(request, user_id):
    """API untuk ambil data driver"""
    try:
        user = User.objects.get(id=user_id, role='driver')
        
        data = {
            'id': user.id,
            'username': user.username,
            'email': user.email,
            'is_approved': user.is_approved,
            'is_active': user.is_active,
            'date_joined': user.date_joined.strftime('%d %b %Y'),
            'full_name': '',
            'phone': '',
            'vehicle_type': '',
            'vehicle_number': '',
        }
        
        if hasattr(user, 'driverprofile'):
            profile = user.driverprofile
            data.update({
                'full_name': profile.full_name or '',
                'phone': profile.phone or '',
                'vehicle_type': profile.vehicle_type or '',
                'vehicle_number': profile.vehicle_number or '',
            })
        
        return JsonResponse(data)
    except User.DoesNotExist:
        return JsonResponse({'error': 'Driver not found'}, status=404)


# =============================
# DRIVER VIEW FUNCTIONS
# =============================

# Halaman Dashboard Driver

# @login_required
# def driver_dashboard(request):
#     driver = request.user

#     if driver.role != 'driver':
#         return redirect('accounts:dashboard')

#     # ACTIVE ORDER
#     active_order = Order.objects.filter(
#         driver=driver,
#         status__in=['confirmed', 'preparing', 'delivering']
#     ).first()

#     # ORDERS AVAILABLE TO TAKE
#     available_orders = Order.objects.filter(
#         driver__isnull=True,
#         status='pending'
#     ).order_by('-created_at')

#     # DRIVER HISTORY
#     history = Order.objects.filter(
#         driver=driver,
#         status='completed'
#     ).order_by('-updated_at')

#     return render(request, "dashboard/driver_dashboard.html", {
#         "driver": driver,
#         "active_order": active_order,
#         "available_orders": available_orders,
#         "history": history,
#     })


# # Menampilkan Order yang Belum Punya Driver

# @login_required
# def driver_available_orders(request):
#     orders = Order.objects.filter(assigned_driver=None, status="pending")
#     return render(request, "driver/available_orders.html", {"orders": orders})

# # Driver Menerima Order

# @login_required
# def driver_accept_order(request, order_id):
#     driver = request.user
#     order = get_object_or_404(Order, id=order_id)

#     if driver.role != 'driver':
#         messages.error(request, "Access denied!")
#         return redirect('accounts:dashboard')

#     if order.driver is not None:
#         messages.error(request, "Order already taken by another driver!")
#         return redirect('accounts:driver_dashboard')

#     # Driver ambil order
#     order.driver = driver
#     order.status = "confirmed"
#     order.save()

#     messages.success(request, f"You accepted order #{order.id}")
#     return redirect('accounts:driver_dashboard')

# # Dashboard Order Aktif Driver

# @login_required
# def driver_my_orders(request):
#     orders = Order.objects.filter(
#         assigned_driver=request.user,
#         status__in=["accepted", "delivering"]
#     )
#     return render(request, "driver/my_orders.html", {"orders": orders})

# # Driver Update Status Pengantaran

# @login_required
# def driver_update_status(request, order_id):
#     driver = request.user
#     order = get_object_or_404(Order, id=order_id)

#     if order.driver != driver:
#         messages.error(request, "You cannot update this order.")
#         return redirect('accounts:driver_dashboard')

#     next_status = request.GET.get("to")

#     allowed = {
#         "confirmed": "preparing",
#         "preparing": "delivering",
#         "delivering": "completed",
#     }

#     if order.status not in allowed:
#         messages.error(request, "Invalid status change.")
#         return redirect('accounts:driver_dashboard')

#     # Status update
#     if allowed[order.status] == next_status:
#         order.status = next_status
#         order.save()
#         messages.success(request, f"Order status updated to {next_status}!")
#     else:
#         messages.error(request, "Invalid status transition.")

#     return redirect('accounts:driver_dashboard')

# # Riwayat Pengiriman Driver

# @login_required
# def driver_history(request):
#     orders = Order.objects.filter(
#         assigned_driver=request.user,
#         status="delivered"
#     )
#     return render(request, "driver/history.html", {"orders": orders})
