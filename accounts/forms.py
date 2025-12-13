# accounts/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import User, RestaurantProfile

class CustomerRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username','email','password1','password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'customer'
        user.is_approved = True  # customers auto-approved
        if commit:
            user.save()
            # profile created by signal; optionally set phone
            if hasattr(user, 'customer_profile'):
                user.customer_profile.phone = self.cleaned_data.get('phone', '')
                user.customer_profile.save()
        return user

class DriverRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    phone = forms.CharField(required=True)
    vehicle_info = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username','email','password1','password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'driver'
        user.is_approved = False  # pending admin approval
        if commit:
            user.save()
            # set driver profile fields
            drv = user.driver_profile
            drv.phone = self.cleaned_data.get('phone', '')
            drv.vehicle_info = self.cleaned_data.get('vehicle_info', '')
            drv.save()
        return user

class RestaurantRegisterForm(UserCreationForm):
    email = forms.EmailField(required=True)
    name = forms.CharField(required=True)
    address = forms.CharField(widget=forms.Textarea, required=False)
    phone = forms.CharField(required=False)

    class Meta:
        model = User
        fields = ('username','email','password1','password2')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.role = 'restaurant'
        user.is_approved = False  # pending admin approval
        if commit:
            user.save()
            resto = user.restaurant_profile
            resto.name = self.cleaned_data.get('name')
            resto.address = self.cleaned_data.get('address', '')
            resto.phone = self.cleaned_data.get('phone', '')
            resto.save()
        return user
