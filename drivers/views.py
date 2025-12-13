from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from orders.models import Order
from django.contrib.auth.decorators import login_required
from payments.models import Withdrawal # Import model Withdrawal yang baru
from drivers.models import Driver # Import model Driver yang sudah dibuat
from django.contrib import messages
from django.db import transaction
from django.shortcuts import redirect
from orders.models import Order


@login_required
def driver_dashboard(request):
    driver = request.user

    # hanya role driver yang boleh
    if driver.role != "driver":
        return redirect("accounts:dashboard")

    active_order = Order.objects.filter(
        driver=driver,
        status__in=["accepted", "picked", "delivering"]
    ).first()

    available_orders = Order.objects.filter(
        driver__isnull=True,
        status="waiting"
    )

    history = Order.objects.filter(
        driver=driver,
        status="delivered"
    )

    return render(request, "dashboard/driver_dashboard.html", {
        "active_order": active_order,
        "available_orders": available_orders,
        "history": history,
    })

# File: drivers/views.py

@login_required
def take_order(request, order_id):
    # Pastikan ini POST request untuk keamanan
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed."})

    driver = request.user
    if driver.role != "driver":
        return JsonResponse({"success": False, "message": "Access denied."})

    order = get_object_or_404(Order, id=order_id)

    # Cek status: hanya pesanan yang READY yang bisa diambil
    if order.status != Order.STATUS_READY:
        return JsonResponse({"success": False, "message": f"Order status is {order.get_status_display()} and cannot be taken."})
    
    # Cek ketersediaan driver
    if order.driver is not None:
        return JsonResponse({"success": False, "message": "Order already taken by another driver."})

    # Logika Menerima Order
    try:
        order.driver = driver
        # Setelah diambil, status pindah ke picked
        order.status = Order.STATUS_PICKED
        order.mark_picked() # Memanfaatkan method di Model Anda untuk set picked_at
        
        # messages.success(request, f"Anda berhasil mengambil Order #{order.id}!")
        return JsonResponse({"success": True, "message": f"Order #{order.id} berhasil diambil. Status: {order.get_status_display()}"})
    except Exception as e:
        return JsonResponse({"success": False, "message": f"Gagal mengambil order: {str(e)}"})



@login_required
def update_status(request, order_id):
    import json
    body = json.loads(request.body)

    order = get_object_or_404(Order, id=order_id, driver=request.user)

    order.status = body.get("status")
    order.save()

    return JsonResponse({"success": True, "message": "Status updated!"})




# Menampilkan Order yang Belum Punya Driver

@login_required
def driver_available_orders(request):
    orders = Order.objects.filter(assigned_driver=None, status="pending")
    return render(request, "driver/available_orders.html", {"orders": orders})



# # Driver Menerima Order

@login_required
def driver_accept_order(request, order_id):
    driver = request.user
    order = get_object_or_404(Order, id=order_id)

    if driver.role != 'driver':
        messages.error(request, "Access denied!")
        return redirect('accounts:dashboard')

    if order.driver is not None:
        messages.error(request, "Order already taken by another driver!")
        return redirect('accounts:driver_dashboard')

    # Driver ambil order
    order.driver = driver
    order.status = "confirmed"
    order.save()

    messages.success(request, f"You accepted order #{order.id}")
    return redirect('accounts:driver_dashboard')

# # Dashboard Order Aktif Driver

@login_required
def driver_my_orders(request):
    orders = Order.objects.filter(
        assigned_driver=request.user,
        status__in=["accepted", "delivering"]
    )
    return render(request, "driver/my_orders.html", {"orders": orders})

# # Driver Update Status Pengantaran

@login_required
def driver_update_status(request, order_id):
    driver = request.user
    order = get_object_or_404(Order, id=order_id)

    if order.driver != driver:
        messages.error(request, "You cannot update this order.")
        return redirect('accounts:driver_dashboard')

    next_status = request.GET.get("to")

    allowed = {
        "confirmed": "preparing",
        "preparing": "delivering",
        "delivering": "completed",
    }

    if order.status not in allowed:
        messages.error(request, "Invalid status change.")
        return redirect('accounts:driver_dashboard')

    # Status update
    if allowed[order.status] == next_status:
        order.status = next_status
        order.save()
        messages.success(request, f"Order status updated to {next_status}!")
    else:
        messages.error(request, "Invalid status transition.")

    return redirect('accounts:driver_dashboard')

# # Riwayat Pengiriman Driver

from orders.models import Order 
# ... tambahkan import lainnya jika belum ada

@login_required
def driver_history(request):
    # Pastikan Anda mengimpor Order dari orders.models
    
    # Ambil semua order yang drivernya adalah user yang sedang login, dan statusnya 'delivered'
    history = Order.objects.filter(
        driver=request.user,
        status=Order.STATUS_DELIVERED # Gunakan konstanta dari model Order
    ).order_by('-delivered_at') # Urutkan dari yang terbaru selesai

    return render(request, "driver/history.html", {
        "history": history
    })


@login_required
def request_withdrawal(request):
    driver_profile = get_object_or_404(Driver, user=request.user)
    
    if request.method == 'POST':
        try:
            amount = float(request.POST.get('amount'))
            
            if amount <= 0:
                messages.error(request, "Jumlah penarikan harus lebih dari nol.")
                return redirect('drivers:driver_dashboard')

            if amount > float(driver_profile.balance):
                messages.error(request, "Saldo tidak mencukupi untuk penarikan ini.")
                return redirect('drivers:driver_dashboard')
            
            # Gunakan transaction untuk memastikan konsistensi data
            with transaction.atomic():
                # 1. Catat permintaan penarikan
                Withdrawal.objects.create(
                    driver=driver_profile,
                    amount=amount,
                    status=Withdrawal.STATUS_PENDING
                )
                
                # 2. Kurangi saldo driver
                driver_profile.balance -= amount
                driver_profile.save()

                messages.success(request, f"Permintaan penarikan dana sebesar Rp{amount:,.2f} berhasil diajukan. Status: Menunggu persetujuan Admin.")
                return redirect('drivers:driver_withdrawal_history')
            
        except ValueError:
            messages.error(request, "Input jumlah tidak valid.")
        except Exception as e:
            messages.error(request, f"Terjadi kesalahan: {e}")
            
    return render(request, "driver/request_withdrawal.html", {"driver": driver_profile})

@login_required
def driver_withdrawal_history(request):
    driver_profile = get_object_or_404(Driver, user=request.user)
    history = Withdrawal.objects.filter(driver=driver_profile).order_by('-request_date')
    
    return render(request, "driver/withdrawal_history.html", {"history": history, "driver": driver_profile})



@login_required
def update_order_status(request, order_id):
    # Pastikan ini POST request (biasanya AJAX/form)
    if request.method != 'POST':
        return JsonResponse({"success": False, "message": "Method not allowed."})

    driver = request.user
    if driver.role != "driver":
        return JsonResponse({"success": False, "message": "Access denied."})

    order = get_object_or_404(Order, id=order_id, driver=driver)

    # Dapatkan status baru dari POST data
    import json
    try:
        data = json.loads(request.body)
        next_status = data.get("status")
    except:
        return JsonResponse({"success": False, "message": "Invalid request body."})

    
    # Tentukan transisi yang diizinkan untuk Driver:
    # PICKED -> DELIVERING -> DELIVERED
    ALLOWED_TRANSITIONS = {
        Order.STATUS_PICKED: Order.STATUS_DELIVERING,
        Order.STATUS_DELIVERING: Order.STATUS_DELIVERED,
    }

    if order.status in ALLOWED_TRANSITIONS and next_status == ALLOWED_TRANSITIONS[order.status]:
        
        order.status = next_status
        
        # Jika status terakhir, panggil method di Model
        if next_status == Order.STATUS_DELIVERED:
            order.mark_delivered() # Memanggil method yang sudah Anda buat
            # Logika penting: Tambahkan komisi ke Saldo Driver
            # Asumsi: Komisi Pengiriman = 10.00
            # Anda perlu menentukan di mana biaya pengiriman disimpan
            
            driver_profile = get_object_or_404(Driver, user=driver)
            DELIVERY_FEE = 10.00 # Ganti dengan logika komisi yang sebenarnya!

            with transaction.atomic():
                driver_profile.balance += DELIVERY_FEE
                driver_profile.save()
            
            messages.success(request, f"Order #{order.id} Selesai! Komisi {DELIVERY_FEE} telah ditambahkan ke saldo Anda.")
        else:
            order.save(update_fields=['status', 'updated_at'])
            messages.success(request, f"Status Order #{order.id} berhasil diperbarui ke {order.get_status_display()}.")

        return JsonResponse({"success": True, "message": "Status berhasil diperbarui."})

    else:
        messages.error(request, f"Transisi status dari {order.get_status_display()} ke {next_status} tidak diizinkan.")
        return JsonResponse({"success": False, "message": "Transisi status tidak diizinkan."})