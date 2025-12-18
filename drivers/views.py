from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404, redirect
from orders.models import Order
from django.contrib.auth.decorators import login_required
from payments.models import Withdrawal
from drivers.models import Driver
from django.contrib import messages
from django.db import transaction
from django.utils import timezone


@login_required
def driver_dashboard(request):
    """Dashboard utama driver dengan statistik"""
    driver = request.user

    if driver.role != "driver":
        messages.error(request, "Access denied. Only drivers can access this page.")
        return redirect("home")

    # Get atau create driver profile
    driver_profile, created = Driver.objects.get_or_create(
        user=driver,
        defaults={'balance': 0.00, 'is_active': True}
    )

    # Active order (sedang dikerjakan)
    active_order = Order.objects.filter(
        driver=driver,
        status__in=[Order.STATUS_PICKED, Order.STATUS_DELIVERING]
    ).first()

    # Available orders (ready for pickup)
    available_orders = Order.objects.filter(
        driver__isnull=True,
        status=Order.STATUS_READY
    ).select_related('restaurant', 'customer').order_by('-created_at')[:5]

    # Delivery history (completed)
    history = Order.objects.filter(
        driver=driver,
        status=Order.STATUS_DELIVERED
    ).select_related('restaurant', 'customer').order_by('-delivered_at')[:5]

    # Statistics
    total_deliveries = Order.objects.filter(
        driver=driver, 
        status=Order.STATUS_DELIVERED
    ).count()
    
    pending_withdrawals = Withdrawal.objects.filter(
        driver=driver_profile,
        status=Withdrawal.STATUS_PENDING
    ).count()

    context = {
        "driver": driver_profile,
        "active_order": active_order,
        "available_orders": available_orders,
        "history": history,
        "total_deliveries": total_deliveries,
        "pending_withdrawals": pending_withdrawals,
    }

    return render(request, "driver/driver_dashboard.html", context)


@login_required
def driver_available_orders(request):
    """Halaman list semua order yang tersedia"""
    if request.user.role != "driver":
        messages.error(request, "Access denied.")
        return redirect("home")

    orders = Order.objects.filter(
        driver__isnull=True,
        status=Order.STATUS_READY
    ).select_related('restaurant', 'customer').order_by('-created_at')

    context = {
        'orders': orders
    }

    return render(request, "driver/available_orders.html", context)


@login_required
def take_order(request, order_id):
    """Driver mengambil order"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('drivers:driver_available_orders')

    driver = request.user
    if driver.role != "driver":
        messages.error(request, "Access denied.")
        return redirect("home")

    order = get_object_or_404(Order, id=order_id)

    # Validasi status order
    if order.status != Order.STATUS_READY:
        messages.error(request, f"Order status is '{order.get_status_display()}' and cannot be taken.")
        return redirect('drivers:driver_available_orders')
    
    # Validasi ketersediaan driver
    if order.driver is not None:
        messages.error(request, "Order already taken by another driver.")
        return redirect('drivers:driver_available_orders')

    # Cek apakah driver sudah punya order aktif
    has_active_order = Order.objects.filter(
        driver=driver,
        status__in=[Order.STATUS_PICKED, Order.STATUS_DELIVERING]
    ).exists()
    
    if has_active_order:
        messages.error(request, "You already have an active order. Complete it first before taking another.")
        return redirect('drivers:driver_dashboard')

    # Ambil order
    try:
        order.driver = driver
        order.status = Order.STATUS_PICKED
        order.mark_picked()
        messages.success(request, f"Successfully took Order #{order.id}!")
        return redirect('drivers:driver_dashboard')
    except Exception as e:
        messages.error(request, f"Failed to take order: {str(e)}")
        return redirect('drivers:driver_available_orders')


@login_required
def update_order_status(request, order_id):
    """Update status order pengantaran"""
    if request.method != 'POST':
        messages.error(request, "Invalid request method.")
        return redirect('drivers:driver_dashboard')

    driver = request.user
    if driver.role != "driver":
        messages.error(request, "Access denied.")
        return redirect('home')

    order = get_object_or_404(Order, id=order_id, driver=driver)

    # Dapatkan status baru dari POST data
    next_status = request.POST.get("status")
    
    if not next_status:
        messages.error(request, "Status not provided.")
        return redirect('drivers:driver_dashboard')

    # Transisi yang diizinkan: PICKED -> DELIVERING -> DELIVERED
    ALLOWED_TRANSITIONS = {
        Order.STATUS_PICKED: Order.STATUS_DELIVERING,
        Order.STATUS_DELIVERING: Order.STATUS_DELIVERED,
    }

    if order.status in ALLOWED_TRANSITIONS and next_status == ALLOWED_TRANSITIONS[order.status]:
        
        order.status = next_status
        
        # Jika sudah delivered
        if next_status == Order.STATUS_DELIVERED:
            order.mark_delivered()
            
            # Tambahkan komisi ke saldo driver
            driver_profile, created = Driver.objects.get_or_create(
                user=driver,
                defaults={'balance': 0.00, 'is_active': True}
            )
            
            DELIVERY_FEE = 10000.00  # Rp 10,000 per delivery
            
            with transaction.atomic():
                driver_profile.balance += DELIVERY_FEE
                driver_profile.save()
            
            messages.success(request, f"Order #{order.id} completed! Commission Rp {DELIVERY_FEE:,.0f} has been added to your balance.")
        else:
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f"Order status updated to {order.get_status_display()}.")

        return redirect('drivers:driver_dashboard')
    else:
        messages.error(request, f"Invalid status transition from {order.get_status_display()} to {next_status}.")
        return redirect('drivers:driver_dashboard')


@login_required
def driver_history(request):
    """Riwayat pengiriman lengkap"""
    if request.user.role != "driver":
        messages.error(request, "Access denied.")
        return redirect("home")
    
    history = Order.objects.filter(
        driver=request.user,
        status=Order.STATUS_DELIVERED
    ).select_related('restaurant', 'customer').order_by('-delivered_at')

    # Hitung total earnings
    total_orders = history.count()
    total_earnings = total_orders * 10000  # Rp 10,000 per order

    context = {
        "history": history,
        "total_orders": total_orders,
        "total_earnings": total_earnings,
    }

    return render(request, "driver/history.html", context)


@login_required
def request_withdrawal(request):
    """Ajukan penarikan dana"""
    if request.user.role != "driver":
        messages.error(request, "Access denied.")
        return redirect("home")
        
    driver_profile, created = Driver.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0.00, 'is_active': True}
    )
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount', 0))
            
            if amount <= 0:
                messages.error(request, "Withdrawal amount must be greater than zero.")
                return redirect('drivers:request_withdrawal')

            if amount > float(driver_profile.balance):
                messages.error(request, "Insufficient balance for this withdrawal.")
                return redirect('drivers:request_withdrawal')
            
            if amount < 10000:
                messages.error(request, "Minimum withdrawal amount is Rp 10,000.")
                return redirect('drivers:request_withdrawal')
            
            # Gunakan transaction untuk konsistensi
            with transaction.atomic():
                # Catat permintaan penarikan
                Withdrawal.objects.create(
                    driver=driver_profile,
                    amount=amount,
                    status=Withdrawal.STATUS_PENDING
                )
                
                # Kurangi saldo driver
                driver_profile.balance -= amount
                driver_profile.save()

                messages.success(request, f"Withdrawal request for Rp {amount:,.0f} has been submitted successfully.")
                return redirect('drivers:driver_withdrawal_history')
            
        except ValueError:
            messages.error(request, "Invalid amount format.")
        except Exception as e:
            messages.error(request, f"An error occurred: {e}")
    
    context = {
        "driver": driver_profile
    }
    
    return render(request, "driver/request_withdrawal.html", context)


@login_required
def driver_withdrawal_history(request):
    """Riwayat penarikan dana"""
    if request.user.role != "driver":
        messages.error(request, "Access denied.")
        return redirect("home")
        
    driver_profile, created = Driver.objects.get_or_create(
        user=request.user,
        defaults={'balance': 0.00, 'is_active': True}
    )
    
    history = Withdrawal.objects.filter(
        driver=driver_profile
    ).order_by('-request_date')
    
    context = {
        "history": history,
        "driver": driver_profile
    }
    
    return render(request, "driver/withdrawal_history.html", context)