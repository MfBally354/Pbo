from django.urls import path
from . import views

app_name = 'restaurants'

urlpatterns = [
    path('', views.restaurant_list, name='list'),
    path('create/', views.restaurant_create, name='create'),

    path('<int:id>/edit/', views.restaurant_edit, name='edit'),
    path('<int:id>/delete/', views.restaurant_delete, name='delete'),

    path('dashboard/', views.dashboard, name='dashboard'),

    # menu
    path('<int:resto_id>/menus/', views.menu_list, name='menu_list'),
    path('<int:restaurant_id>/menus/add/', views.menu_add, name='menu_add'),
    path('<int:resto_id>/menus/create/', views.menu_create, name='menu_create'),
    path('<int:resto_id>/menus/<int:id>/edit/', views.menu_edit, name='menu_edit'),
    path('<int:resto_id>/menus/<int:id>/delete/', views.menu_delete, name='menu_delete'),

    # ORDER MANAGEMENT
    path('restaurants/<int:resto_id>/orders/', views.restaurant_orders, name='restaurant_orders'), 
    path("orders/<int:order_id>/accept/", views.accept_order, name="accept_order"),
    path("orders/<int:order_id>/prepare/", views.prepare_order, name="prepare_order"),
    path("orders/<int:order_id>/ready/", views.ready_order, name="ready_order"),

    # PAYMENT
    path('<int:resto_id>/orders/', views.restaurant_orders, name='restaurant_orders'),
    path('payment/<int:order_id>/', views.payment_view, name='payment_view'),
    path('<int:restaurant_id>/payments/', views.restaurant_payments, name='restaurant_payments'),

]
