# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, RestaurantProfile, DriverProfile, CustomerProfile

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        if instance.role == 'restaurant':
            RestaurantProfile.objects.create(user=instance, name=instance.username)
        elif instance.role == 'driver':
            DriverProfile.objects.create(user=instance)
        else:
            CustomerProfile.objects.create(user=instance)
