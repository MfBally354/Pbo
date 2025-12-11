from django.urls import path
from django.shortcuts import redirect
from . import views

app_name = 'accounts'

urlpatterns = [
    # Auth
    path("login/", views.login_view, name="login"),
    path("logout/", views.logout_view, name="logout"),
    
    # Register
    path('register/customer/', views.register_customer, name='register_customer'),
    path('register/driver/', views.register_driver, name='register_driver'),
    path('register/restaurant/', views.register_restaurant, name='register_restaurant'),
    
    # Admin Dashboard
    path("admin-panel/", views.admin_dashboard, name="admin_dashboard"),
    path("dashboard/", views.admin_dashboard, name="dashboard"),
    
    # Approvals
    path("approvals/", views.account_approvals, name="approvals"),
    path("approve/<int:user_id>/", views.approve_user, name="approve_user"),
    path("reject/<int:user_id>/", views.reject_user, name="reject_user"),
    
    # Manage Pages
    path("drivers/", views.manage_drivers, name="drivers"),
    path("restaurants/", views.manage_restaurants, name="restaurants"),
    path("orders/", views.manage_orders, name="orders"),
    path("chat/", lambda request: redirect('/chats/admin/'), name="chat"),
    
    # Restaurant CRUD
    path("restaurants/add/", views.add_restaurant, name="add_restaurant"),
    path("restaurants/edit/<int:user_id>/", views.edit_restaurant, name="edit_restaurant"),
    path("restaurants/delete/<int:user_id>/", views.delete_restaurant, name="delete_restaurant"),
    path("api/restaurant/<int:user_id>/", views.get_restaurant_api, name="get_restaurant_api"),
    
    # Orders CRUD
    path("orders/add/", views.add_order, name="add_order"),
    path("orders/update-status/<int:order_id>/", views.update_order_status, name="update_order_status"),
    path("orders/assign-driver/<int:order_id>/", views.assign_driver, name="assign_driver"),
    path("orders/delete/<int:order_id>/", views.delete_order, name="delete_order"),
    path("api/order/<int:order_id>/", views.get_order_api, name="get_order_api"),
    

    # USERS FOR ORDER API (TIDAK ADA DUPLIKAT)
    path("api/usersfororder/", views.users_for_order_api, name="users_for_order_api"),

    # Drivers CRUD
    path("drivers/add/", views.add_driver, name="add_driver"),
    path("drivers/edit/<int:user_id>/", views.edit_driver, name="edit_driver"),
    path("drivers/delete/<int:user_id>/", views.delete_driver, name="delete_driver"),
    path("api/driver/<int:user_id>/", views.get_driver_api, name="get_driver_api"),

]
