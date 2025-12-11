from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    path("dashboard/", views.driver_dashboard, name="driver_dashboard"),
    path("orders/available/", views.driver_available_orders, name="driver_available_orders"),
    path("orders/<int:order_id>/accept/", views.driver_accept_order, name="driver_accept_order"),
    path("orders/<int:order_id>/update/", views.driver_update_status, name="driver_update_status"),
    path("history/", views.driver_history, name="driver_history"),
]
