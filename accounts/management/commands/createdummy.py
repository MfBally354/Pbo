from django.core.management.base import BaseCommand
from accounts.models import User

class Command(BaseCommand):
    help = "Generate dummy users"

    def handle(self, *args, **kwargs):
        User.objects.create_superuser(username="admin", password="admin123", email="admin@mail.com", role="admin")

        User.objects.create_user(username="resto1", password="12345", email="resto@mail.com", role="restaurant", is_approved=True)
        User.objects.create_user(username="driver1", password="12345", email="driver@mail.com", role="driver", is_approved=True)
        User.objects.create_user(username="customer1", password="12345", email="customer@mail.com", role="customer", is_approved=True)

        self.stdout.write(self.style.SUCCESS("Dummy accounts created!"))
