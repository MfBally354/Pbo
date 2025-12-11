from django.http import JsonResponse
from django.shortcuts import render, get_object_or_404
from orders.models import Order
from django.contrib.auth.decorators import login_required



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

@login_required
def take_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)

    if order.status != "waiting":
        return JsonResponse({"success": False, "message": "Order no longer available."})

    order.driver = request.user
    order.status = "assigned"
    order.save()

    return JsonResponse({"success": True, "message": "Order taken!"})


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

@login_required
def driver_history(request):
    orders = Order.objects.filter(
        assigned_driver=request.user,
        status="delivered"
    )
    return render(request, "driver/history.html", {"orders": orders})

