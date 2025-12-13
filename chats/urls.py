from django.urls import path
from . import views

app_name = 'chats'

urlpatterns = [
    path('admin/', views.admin_chat_view, name='admin_chat'),
    path('api/messages/<int:user_id>/', views.get_chat_messages, name='get_messages'),
    path('api/send/', views.send_chat_message, name='send_message'),
    path('api/delete/<int:message_id>/', views.delete_chat_message, name='delete_message'),

    # Admin Support
    path('support/', views.admin_support_view, name='admin_support'),
    path('api/ticket/<int:ticket_id>/', views.get_ticket_details, name='get_ticket_details'),
    path('api/ticket/<int:ticket_id>/update/', views.update_ticket_status, name='update_ticket_status'),
    path('api/ticket/<int:ticket_id>/reply/', views.reply_to_ticket, name='reply_to_ticket'),
    path('api/ticket/<int:ticket_id>/delete/', views.delete_ticket, name='delete_ticket'),
]
