from django.contrib import admin
from django.urls import path, include
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static

def home(request):
    return render(request, "home.html")

urlpatterns = [
    path('admin/', admin.site.urls),

    # home page
    path("", home, name="home"),

    # accounts
    path("", include("accounts.urls", namespace="accounts")),

    # restaurants
    path("restaurants/", include("restaurants.urls", namespace="restaurants")),

    # browser reload
    path("django-browser-reload/", include("django_browser_reload.urls")),

    # admin panel
    # path("adminpanel/", include("accounts.urls", namespace="accounts")),
    
    # chats
    path('chats/', include('chats.urls')),

    # drivers
    path('drivers/', include('drivers.urls', namespace='drivers')), # PASTIKAN ADA INI

    path("customers/", include("customers.urls", namespace='customers')),

   
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)  
