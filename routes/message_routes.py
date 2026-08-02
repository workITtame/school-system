from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from flask_login import login_required, current_user
from models import db, User, Message
from sqlalchemy import or_, and_, desc

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

@messages_bp.route('/')
@login_required
def index():
    # Get all potential users to message (other admins and teachers)
    other_users = User.query.filter(User.id != current_user.id).all()
    return render_template('messages/index.html', other_users=other_users)

@messages_bp.route('/api/conversations')
@login_required
def get_conversations():
    # Fetch recent conversations for current_user
    users = User.query.filter(User.id != current_user.id).all()
    conversations = []
    
    for u in users:
        last_msg = Message.query.filter(
            or_(
                and_(Message.sender_id == current_user.id, Message.recipient_id == u.id),
                and_(Message.sender_id == u.id, Message.recipient_id == current_user.id)
            )
        ).order_by(Message.timestamp.desc()).first()
        
        unread_count = Message.query.filter_by(
            sender_id=u.id, 
            recipient_id=current_user.id, 
            is_read=False
        ).count()
        
        conversations.append({
            'user_id': u.id,
            'name': u.name,
            'role': 'مدير النظام' if u.role == 'admin' else 'معلم',
            'last_message': last_msg.content if last_msg else 'ابدأ المحادثة الآن',
            'last_time': last_msg.timestamp.strftime('%H:%M %Y-%m-%d') if last_msg else '',
            'unread_count': unread_count
        })
        
    return jsonify({'success': True, 'conversations': conversations})

@messages_bp.route('/api/thread/<int:user_id>')
@login_required
def get_thread(user_id):
    target_user = User.query.get_or_404(user_id)
    
    # Mark incoming unread messages as read
    unread = Message.query.filter_by(sender_id=user_id, recipient_id=current_user.id, is_read=False).all()
    for m in unread:
        m.is_read = True
    db.session.commit()
    
    messages = Message.query.filter(
        or_(
            and_(Message.sender_id == current_user.id, Message.recipient_id == user_id),
            and_(Message.sender_id == user_id, Message.recipient_id == current_user.id)
        )
    ).order_by(Message.timestamp.asc()).all()
    
    chat_history = []
    for m in messages:
        chat_history.append({
            'id': m.id,
            'sender_id': m.sender_id,
            'is_mine': m.sender_id == current_user.id,
            'content': m.content,
            'time': m.timestamp.strftime('%H:%M')
        })
        
    return jsonify({
        'success': True,
        'target_user': {'id': target_user.id, 'name': target_user.name, 'role': 'مدير النظام' if target_user.role == 'admin' else 'معلم'},
        'messages': chat_history
    })

@messages_bp.route('/api/send', methods=['POST'])
@login_required
def send_message():
    data = request.get_json()
    recipient_id = data.get('recipient_id')
    content = data.get('content')
    
    if not recipient_id or not content or not content.strip():
        return jsonify({'success': False, 'message': 'محتوى الرسالة والمستلم مطلوبان'}), 400
        
    if int(recipient_id) == current_user.id:
        return jsonify({'success': False, 'message': 'لا يمكن إرسال رسالة لنفسك'}), 400
        
    recipient_user = User.query.get(recipient_id)
    if not recipient_user or getattr(recipient_user, 'is_deleted', False):
        return jsonify({'success': False, 'message': 'المستلم غير موجود أو تم إغلاق حسابه'}), 404
        
    msg = Message(
        sender_id=current_user.id,
        recipient_id=recipient_id,
        content=content.strip()
    )
    db.session.add(msg)
    db.session.commit()
    
    return jsonify({
        'success': True,
        'message': 'تم إرسال الرسالة بنجاح',
        'data': {
            'id': msg.id,
            'sender_id': msg.sender_id,
            'is_mine': True,
            'content': msg.content,
            'time': msg.timestamp.strftime('%H:%M')
        }
    })
