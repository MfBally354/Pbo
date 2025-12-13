from django.db import models
from accounts.models import User
from django.conf import settings
from django.utils import timezone
from restaurants.models import Restaurant


# class Order(models.Model):
#     STATUS_CHOICES = [
#         ('pending', 'Pending'),
#         ('confirmed', 'Confirmed'),
#         ('preparing', 'Preparing'),
#         ('delivering', 'Delivering'),
#         ('completed', 'Completed'),
#         ('cancelled', 'Cancelled'),
#     ]
    
#     customer = models.ForeignKey(
#         'accounts.User', 
#         on_delete=models.CASCADE, 
#         related_name='customer_orders',
#         limit_choices_to={'role': 'customer'}
#     )
#     restaurant = models.ForeignKey(
#         'accounts.User', 
#         on_delete=models.CASCADE, 
#         related_name='restaurant_orders',
#         limit_choices_to={'role': 'restaurant'}
#     )
#     driver = models.ForeignKey(
#         'accounts.User', 
#         null=True, 
#         blank=True, 
#         on_delete=models.SET_NULL,
#         related_name='driver_orders',
#         limit_choices_to={'role': 'driver'}
#     )
    
#     status = models.CharField(max_length=50, choices=STATUS_CHOICES, default='pending')
#     total_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
#     delivery_address = models.TextField(blank=True, null=True)
#     notes = models.TextField(blank=True, null=True)
    
#     created_at = models.DateTimeField(auto_now_add=True)
#     updated_at = models.DateTimeField(auto_now=True)
    
#     class Meta:
#         ordering = ['-created_at']
    
#     def __str__(self):
#         return f"Order #{self.id} - {self.customer.username} from {self.restaurant.username}"
    
#     def is_active(self):
#         """Check if order is still active (not completed or cancelled)"""
#         return self.status not in ['completed', 'cancelled']


class Order(models.Model):
    STATUS_PENDING = 'pending'            # dibuat customer, menunggu restoran konfirmasi
    STATUS_ACCEPTED = 'accepted'          # restoran setuju
    STATUS_PREPARING = 'preparing'        # restoran menyiapkan
    STATUS_READY = 'ready_for_pickup'     # siap diambil driver
    STATUS_PICKED = 'picked'              # driver ambil
    STATUS_DELIVERING = 'delivering'      # driver mengantar
    STATUS_DELIVERED = 'delivered'        # driver sudah antar (tiba di customer)
    STATUS_COMPLETED = 'completed'        # transaksi selesai / sudah dibayar & konfirmasi
    STATUS_CANCELLED = 'cancelled'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_ACCEPTED, 'Accepted'),
        (STATUS_PREPARING, 'Preparing'),
        (STATUS_READY, 'Ready for pickup'),
        (STATUS_PICKED, 'Picked by driver'),
        (STATUS_DELIVERING, 'Delivering'),
        (STATUS_DELIVERED, 'Delivered'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_CANCELLED, 'Cancelled'),
    ]

    PAYMENT_UNPAID = 'unpaid'
    PAYMENT_PAID = 'paid'

    PAYMENT_CHOICES = [
        (PAYMENT_UNPAID, 'Unpaid'),
        (PAYMENT_PAID, 'Paid'),
    ]

    customer = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='customer_orders')
    restaurant = models.ForeignKey(Restaurant, on_delete=models.CASCADE, related_name='orders')
    driver = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_orders')

    # order details (contoh sederhana)
    total_price = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, default=STATUS_PENDING)
    payment_status = models.CharField(max_length=16, choices=PAYMENT_CHOICES, default=PAYMENT_UNPAID)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    picked_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    notes = models.TextField(blank=True, null=True)

    def mark_picked(self):
        self.status = self.STATUS_PICKED
        self.picked_at = timezone.now()
        self.save(update_fields=['status','picked_at','updated_at'])

    def mark_delivered(self):
        self.status = self.STATUS_DELIVERED
        self.delivered_at = timezone.now()
        self.save(update_fields=['status','delivered_at','updated_at'])

    def __str__(self):
        return f"Order #{self.id} ({self.status})"


class OrderItem(models.Model):
    """Items dalam order"""
    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name='items')
    item_name = models.CharField(max_length=200)
    quantity = models.IntegerField(default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    def __str__(self):
        return f"{self.quantity}x {self.item_name}"
    
    def subtotal(self):
        return self.quantity * self.price
    
# pembayaran resto-cust

class Payment(models.Model):
    order = models.OneToOneField(Order, on_delete=models.CASCADE, related_name="payment")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(max_length=20, choices=[
        ("cash", "Cash"),
        ("ewallet", "E-Wallet"),
        ("transfer", "Bank Transfer")
    ])
    status = models.CharField(max_length=20, choices=[
        ("unpaid", "Unpaid"),
        ("paid", "Paid")
    ], default="unpaid")

    paid_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"Payment for Order #{self.order.id}"

