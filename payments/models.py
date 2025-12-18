from django.db import models
from django.conf import settings # Untuk User
from drivers.models import Driver # Import model Driver yang sudah dibuat

class Withdrawal(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_APPROVED = 'approved'
    STATUS_REJECTED = 'rejected'
    
    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_APPROVED, 'Approved'),
        (STATUS_REJECTED, 'Rejected'),
    ]

    # Menggunakan OneToOneField ke Driver agar lebih mudah
    driver = models.ForeignKey(Driver, on_delete=models.CASCADE, related_name='withdrawals')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default=STATUS_PENDING)
    request_date = models.DateTimeField(auto_now_add=True)
    processed_date = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Withdrawal #{self.id} by {self.driver.user.username} - {self.amount}"

# Lakukan migrasi: python manage.py makemigrations payments && python manage.py migrate