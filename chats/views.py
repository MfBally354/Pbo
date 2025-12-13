from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from .models import ChatRoom, ChatMessage
from accounts.models import User
from django.db.models import Q

@login_required
def admin_chat_view(request):
    """
    Halaman chat untuk admin
    """
    if request.user.role != 'admin':
        return redirect('home')
    
    # Ambil semua user yang pernah chat atau bisa di-chat
    users = User.objects.exclude(role='admin').exclude(id=request.user.id)
    
    # Ambil chat rooms yang sudah ada
    chat_rooms = ChatRoom.objects.filter(admin=request.user)
    
    # Buat dictionary untuk unread count
    users_with_chats = []
    for user in users:
        room = chat_rooms.filter(user=user).first()
        unread_count = 0
        last_message = None
        
        if room:
            unread_count = room.get_unread_count(request.user)
            last_message = room.get_last_message()
        
        users_with_chats.append({
            'user': user,
            'room': room,
            'unread_count': unread_count,
            'last_message': last_message
        })
    
    # Sort by last message time
    users_with_chats.sort(key=lambda x: x['room'].updated_at if x['room'] else x['user'].date_joined, reverse=True)
    
    context = {
        'users_with_chats': users_with_chats,
    }
    
    return render(request, 'adminpanel/chat.html', context)


@login_required
def get_chat_messages(request, user_id):
    """
    API untuk ambil pesan chat dengan user tertentu
    """
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    other_user = get_object_or_404(User, id=user_id)
    
    # Cari atau buat chat room
    room, created = ChatRoom.objects.get_or_create(
        admin=request.user,
        user=other_user
    )
    
    # Ambil semua pesan
    messages = room.messages.all()
    
    # Mark sebagai sudah dibaca
    room.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # Format response
    messages_data = []
    for msg in messages:
        messages_data.append({
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.username,
            'message': msg.message,
            'is_admin': msg.sender.role == 'admin',
            'created_at': msg.created_at.strftime('%I:%M %p'),
            'is_read': msg.is_read
        })
    
    return JsonResponse({
        'messages': messages_data,
        'room_id': room.id,
        'other_user': {
            'id': other_user.id,
            'name': other_user.username,
            'role': other_user.role
        }
    })


@require_POST
@login_required
def send_chat_message(request):
    """
    API untuk kirim pesan
    """
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    user_id = request.POST.get('user_id')
    message_text = request.POST.get('message')
    
    if not user_id or not message_text:
        return JsonResponse({'error': 'Missing data'}, status=400)
    
    other_user = get_object_or_404(User, id=user_id)
    
    # Cari atau buat chat room
    room, created = ChatRoom.objects.get_or_create(
        admin=request.user,
        user=other_user
    )
    
    # Simpan pesan
    msg = ChatMessage.objects.create(
        room=room,
        sender=request.user,
        message=message_text
    )
    
    return JsonResponse({
        'success': True,
        'message': {
            'id': msg.id,
            'sender_id': msg.sender.id,
            'sender_name': msg.sender.username,
            'message': msg.message,
            'is_admin': True,
            'created_at': msg.created_at.strftime('%I:%M %p'),
        }
    })


@require_POST
@login_required
def delete_chat_message(request, message_id):
    """
    Hapus pesan
    """
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    message = get_object_or_404(ChatMessage, id=message_id)
    
    # Cek apakah pesan ini milik room yang dikelola admin ini
    if message.room.admin != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    message.delete()
    
    return JsonResponse({'success': True})

from django.utils import timezone
from .models import SupportTicket, TicketReply

@login_required
def admin_support_view(request):
    """Halaman admin support untuk manage tickets"""
    if request.user.role != 'admin':
        return redirect('home')
    
    # Get all tickets
    tickets = SupportTicket.objects.select_related('user', 'assigned_to').all()
    
    # Statistics
    total_tickets = tickets.count()
    open_tickets = tickets.filter(status='open').count()
    in_progress_tickets = tickets.filter(status='in_progress').count()
    resolved_tickets = tickets.filter(status='resolved').count()
    
    context = {
        'tickets': tickets,
        'total_tickets': total_tickets,
        'open_tickets': open_tickets,
        'in_progress_tickets': in_progress_tickets,
        'resolved_tickets': resolved_tickets,
    }
    
    return render(request, 'adminpanel/support.html', context)


@login_required
def get_ticket_details(request, ticket_id):
    """API untuk ambil detail ticket dan replies"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        ticket = SupportTicket.objects.select_related('user', 'assigned_to').get(id=ticket_id)
        
        replies_data = []
        for reply in ticket.replies.select_related('user').all():
            replies_data.append({
                'id': reply.id,
                'user': reply.user.username,
                'user_role': reply.user.role,
                'message': reply.message,
                'created_at': reply.created_at.strftime('%d %b %Y %H:%M'),
            })
        
        data = {
            'id': ticket.id,
            'user': {
                'id': ticket.user.id,
                'username': ticket.user.username,
                'email': ticket.user.email,
                'role': ticket.user.role,
            },
            'subject': ticket.subject,
            'description': ticket.description,
            'status': ticket.status,
            'priority': ticket.priority,
            'assigned_to': ticket.assigned_to.username if ticket.assigned_to else 'Unassigned',
            'created_at': ticket.created_at.strftime('%d %b %Y %H:%M'),
            'updated_at': ticket.updated_at.strftime('%d %b %Y %H:%M'),
            'replies': replies_data,
        }
        
        return JsonResponse(data)
    except SupportTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)


@require_POST
@login_required
def update_ticket_status(request, ticket_id):
    """Update status ticket"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
        new_status = request.POST.get('status')
        
        if new_status in dict(SupportTicket.STATUS_CHOICES):
            ticket.status = new_status
            if new_status == 'resolved':
                ticket.resolved_at = timezone.now()
            ticket.save()
            return JsonResponse({'success': True})
        else:
            return JsonResponse({'error': 'Invalid status'}, status=400)
    except SupportTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)


@require_POST
@login_required
def reply_to_ticket(request, ticket_id):
    """Reply ke ticket"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
        message = request.POST.get('message')
        
        if not message:
            return JsonResponse({'error': 'Message is required'}, status=400)
        
        reply = TicketReply.objects.create(
            ticket=ticket,
            user=request.user,
            message=message
        )
        
        # Update ticket status to in_progress if it's open
        if ticket.status == 'open':
            ticket.status = 'in_progress'
            ticket.save()
        
        return JsonResponse({
            'success': True,
            'reply': {
                'id': reply.id,
                'user': reply.user.username,
                'user_role': reply.user.role,
                'message': reply.message,
                'created_at': reply.created_at.strftime('%d %b %Y %H:%M'),
            }
        })
    except SupportTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)


@require_POST
@login_required
def delete_ticket(request, ticket_id):
    """Hapus ticket"""
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    try:
        ticket = SupportTicket.objects.get(id=ticket_id)
        ticket.delete()
        return JsonResponse({'success': True})
    except SupportTicket.DoesNotExist:
        return JsonResponse({'error': 'Ticket not found'}, status=404)
