from django.urls import path
from . import views

app_name = 'drivers'

urlpatterns = [
    # Dashboard
    path("dashboard/", views.driver_dashboard, name="driver_dashboard"),
    
    # Orders Management
    path("orders/available/", views.driver_available_orders, name="driver_available_orders"),
    path("take-order/<int:order_id>/", views.take_order, name="take_order"),
    path("update-status/<int:order_id>/", views.update_order_status, name="update_order_status"),
    path("history/", views.driver_history, name="driver_history"),
    
    # Withdrawal Management
    path("withdraw/request/", views.request_withdrawal, name="request_withdrawal"),
    path("withdraw/history/", views.driver_withdrawal_history, name="driver_withdrawal_history"),
]