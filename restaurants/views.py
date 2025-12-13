from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from .models import Restaurant, MenuItem, MenuCategory
from orders.models import Order, Payment
from django.utils import timezone


# ============================
# OWNER: MENU CRUD
# ============================

@role_required(['restaurant'])
def menu_list(request, resto_id):
    resto = get_object_or_404(Restaurant, id=resto_id, owner=request.user)
    menus = resto.menu_items.all()
    return render(request, 'restaurants/menu_list.html', {
        'resto': resto,
        'menus': menus
    })


@role_required(['restaurant'])
def menu_create(request, resto_id):
    resto = get_object_or_404(Restaurant, id=resto_id, owner=request.user)

    if request.method == 'POST':
        MenuItem.objects.create(
            restaurant=resto,
            name=request.POST.get('name'),
            price=request.POST.get('price'),
            description=request.POST.get('description')
        )
        return redirect('restaurants:menu_list', resto_id=resto.id)

    return render(request, 'restaurants/menu_create.html', {
        'resto': resto
    })


@role_required(['restaurant'])
def menu_edit(request, resto_id, id):
    resto = get_object_or_404(Restaurant, id=resto_id, owner=request.user)
    menu = get_object_or_404(MenuItem, id=id, restaurant=resto)

    if request.method == 'POST':
        # Update field dasar
        menu.name = request.POST.get('name')
        menu.price = request.POST.get('price')
        menu.description = request.POST.get('description')
        menu.stock = request.POST.get('stock')
        menu.is_available = 'is_available' in request.POST

        # Update gambar jika diupload
        if request.FILES.get("image"):
            menu.image = request.FILES.get("image")

        menu.save()
        return redirect('restaurants:menu_list', resto_id=resto.id)

    return render(request, 'restaurants/menu_edit.html', {
        'resto': resto,
        'menu': menu,
    })


@role_required(['restaurant'])
def menu_delete(request, resto_id, id):
    resto = get_object_or_404(Restaurant, id=resto_id, owner=request.user)
    menu = get_object_or_404(MenuItem, id=id, restaurant=resto)
    menu.delete()

    return redirect('restaurants:menu_list', resto_id=resto.id)


# ============================
# ADMIN: RESTO CRUD
# ============================

@role_required(['admin'])
def restaurant_list(request):
    restos = Restaurant.objects.all()
    return render(request, 'restaurants/list.html', {'restos': restos})


@role_required(['admin', 'restaurant'])
def restaurant_create(request):

    # CEK: Jika user restaurant sudah punya resto → langsung ke dashboard
    if request.user.role == "restaurant":
        existing = Restaurant.objects.filter(owner=request.user).first()
        if existing:
            return redirect('restaurants:dashboard')

    if request.method == 'POST':
        # owner
        if request.user.role == 'restaurant':
            owner = request.user
        else:
            owner = User.objects.get(id=request.POST.get('owner'))

        # Buat restaurant baru
        Restaurant.objects.create(
            owner=owner,
            name=request.POST.get('name'),
            address=request.POST.get('address'),
            description=request.POST.get('description')
        )

        return redirect('restaurants:dashboard')

    # GET request
    users = None if request.user.role == "restaurant" else User.objects.filter(role='restaurant')
    return render(request, 'restaurants/create.html', {'users': users})



@role_required(['admin'])
def restaurant_edit(request, id):
    resto = get_object_or_404(Restaurant, id=id)

    if request.method == 'POST':
        resto.name = request.POST.get('name')
        resto.address = request.POST.get('address')
        resto.description = request.POST.get('description')
        resto.save()

        return redirect('restaurants:list')

    return render(request, 'restaurants/edit.html', {'resto': resto})


@role_required(['admin'])
def restaurant_delete(request, id):
    resto = get_object_or_404(Restaurant, id=id)
    resto.delete()

    return redirect('restaurants:list')



@role_required(['restaurant'])  # Perbaiki: tambahkan allowed_roles
def dashboard(request):
    # HAPUS baris ini: from accounts.decorators import role_required
    # HAPUS baris ini: decorated_view = role_required(allowed_roles=['Restaurant'])(dashboard)
    
    # Logika untuk mengambil data dashboard (misalnya pesanan, menu, dll.)
    # Contoh: ambil resto milik user
    try:
        resto = Restaurant.objects.get(owner=request.user)
    except Restaurant.DoesNotExist:
       return redirect('restaurants:create')
    
    context = {
        'greeting': 'Selamat datang di Dashboard Restoran Anda!',
        'resto': resto,  # Tambahkan data relevan
        # ... data lainnya, misalnya menus = resto.menu_items.all() jika perlu
    }
    return render(request, 'dashboard/restaurant_dashboard.html', context)  # Perbaiki path template jika perlu



# ============================
# ORDER MANAGEMENT RESTAURANT
# ============================

def restaurant_orders(request, resto_id):
    restaurant = get_object_or_404(Restaurant, id=resto_id)

    orders = Order.objects.filter(
        restaurant=restaurant
    ).order_by("-created_at")

    return render(request, "restaurants/orders.html", {
        "orders": orders,
        "restaurant": restaurant,
    })


def accept_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "accepted"
    order.save()
    return redirect("restaurants:restaurant_orders", resto_id=order.restaurant.id)


def prepare_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "preparing"
    order.save()
    return redirect("restaurants:restaurant_orders", resto_id=order.restaurant.id)


def ready_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.status = "ready_for_pickup"
    order.save()
    return redirect("restaurants:restaurant_orders", resto_id=order.restaurant.id)


def payment_view(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if request.method == "POST":
        method = request.POST["method"]
        amount = order.total_price

        Payment.objects.update_or_create(
            order=order,
            defaults={
                "method": method,
                "status": "paid",
                "amount": amount,
                "paid_at": timezone.now()
            }
        )

        order.payment_status = "paid"
        order.save()

        messages.success(request, "Payment confirmed!")
        return redirect("restaurants:restaurant_orders", resto_id=order.restaurant.id)

    return render(request, "restaurants/payments.html", {"order": order})


@role_required(['restaurant'])
def menu_add(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    if request.method == 'POST':
        name = request.POST.get("name")
        price = request.POST.get("price")
        description = request.POST.get("description")
        stock = request.POST.get("stock")
        image = request.FILES.get("image")

        # Buat menu baru
        new_item = MenuItem(
            restaurant=restaurant,
            name=name,
            price=price,
            description=description,
            stock=stock,
        )

        # Simpan gambar jika ada upload
        if image:
            new_item.image = image

        new_item.save()

        return redirect('restaurants:menu_list', resto_id=restaurant.id)

    return render(request, 'restaurants/menu_add.html', {
        "restaurant": restaurant
    })

@role_required(['restaurant'])
def restaurant_payments(request, restaurant_id):
    restaurant = get_object_or_404(Restaurant, id=restaurant_id)

    payments = Payment.objects.filter(
        order__restaurant=restaurant
    ).order_by("-paid_at")

    return render(request, "restaurants/payments.html", {
        "restaurant": restaurant,
        "payments": payments,
    })

