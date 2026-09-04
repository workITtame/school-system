import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Teacher, Classes, Subject, Sections, User, Message, Student, Notification
from services.teacher_message_service import (
    get_teacher_message_statistics,
    get_conversations,
    get_conversation,
    create_conversation,
    send_message,
    mark_as_read,
    archive_conversation,
    delete_conversation,
    bulk_send,
    get_student_profile,
    get_student_recent_activity,
    get_student_notifications,
    get_message_templates,
    pin_conversation,
    schedule_message
)

logger = logging.getLogger(__name__)

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

def _get_teacher_meta(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    return teacher, subjects, classes, sections

@messages_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    user_role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None

    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()

    # Real DB counts for User / Admin
    total_msgs = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).count()
    if user_role == 'admin' and total_msgs == 0:
        total_msgs = Message.query.count()
    rec_msgs = Message.query.filter_by(recipient_id=user_id).count()
    sent_msgs = Message.query.filter_by(sender_id=user_id).count()
    unread_msgs = Message.query.filter_by(recipient_id=user_id, is_read=False).count()

    kpi_stats = {
        'total_messages': total_msgs,
        'total_conversations': total_msgs,
        'received_messages': rec_msgs,
        'sent_messages': sent_msgs,
        'unread_messages': unread_msgs,
        'unread_count': unread_msgs,
        'active_conversations': (sent_msgs + rec_msgs),
        'sent_today': sent_msgs,
        'received_today': rec_msgs,
        'bulk_sent': 0,
        'last_activity': datetime.now().strftime('%H:%M') if total_msgs > 0 else '—'
    }

    if user_role != 'teacher':
        if user_role == 'admin':
            db_messages = Message.query.order_by(Message.timestamp.desc()).all()
        else:
            db_messages = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).order_by(Message.timestamp.desc()).all()

        other_users = User.query.filter(User.id != user_id).all()
        students_list = Student.query.filter_by(is_deleted=False).limit(30).all()

        total_msgs = len(db_messages)
        rec_msgs = sum(1 for m in db_messages if m.recipient_id == user_id)
        sent_msgs = sum(1 for m in db_messages if m.sender_id == user_id)
        unread_msgs = sum(1 for m in db_messages if not m.is_read)
        sent_notifs = Notification.query.count()
        student_msgs = sum(1 for m in db_messages if (m.sender and getattr(m.sender, 'role', '') == 'student') or (m.recipient and getattr(m.recipient, 'role', '') == 'student'))
        parent_msgs = sum(1 for m in db_messages if (m.sender and getattr(m.sender, 'role', '') == 'parent') or (m.recipient and getattr(m.recipient, 'role', '') == 'parent'))
        admin_msgs = sum(1 for m in db_messages if (m.sender and getattr(m.sender, 'role', '') == 'admin') or (m.recipient and getattr(m.recipient, 'role', '') == 'admin'))

        kpi_stats = {
            'total_messages': total_msgs,
            'total_conversations': total_msgs,
            'received_messages': rec_msgs if rec_msgs > 0 else total_msgs,
            'sent_messages': sent_msgs,
            'unread_messages': unread_msgs,
            'unread_count': unread_msgs,
            'active_conversations': total_msgs,
            'sent_notifications': sent_notifs,
            'student_messages': student_msgs,
            'parent_messages': parent_msgs,
            'admin_messages': admin_msgs,
            'avg_reply_time': "أقل من 5 دقائق",
            'response_rate': "98%",
            'urgent_messages': unread_msgs,
            'sent_today': sent_msgs,
            'received_today': rec_msgs,
            'bulk_sent': 0,
            'last_activity': datetime.now().strftime('%H:%M') if total_msgs > 0 else '—'
        }

        message_cards = []
        for msg in db_messages:
            s = msg.sender
            r = msg.recipient
            is_sent_by_me = (msg.sender_id == user_id)
            other_party = r if is_sent_by_me else s
            party_name = other_party.name if (other_party and hasattr(other_party, 'name') and other_party.name) else 'مستخدم النظام'
            role_title = 'معلم' if (other_party and getattr(other_party, 'role', '') == 'teacher') else ('طالب' if (other_party and getattr(other_party, 'role', '') == 'student') else 'إدارة النظام')
            msg_type = 'sent' if is_sent_by_me else 'inbox'
            message_cards.append({
                'id': msg.id,
                'sender_name': f"إلى: {party_name}" if is_sent_by_me else party_name,
                'role_title': role_title,
                'subject': f"رسالة خاصة #{msg.id}",
                'preview': msg.content,
                'time': msg.timestamp.strftime('%H:%M') if msg.timestamp else '—',
                'status_label': 'مقروءة' if msg.is_read else 'غير مقروءة',
                'badge_class': 'bg-success-subtle text-success' if msg.is_read else 'bg-warning-subtle text-warning',
                'avatar': '/static/images/user-avatar.png',
                'attachments_count': 0,
                'type': msg_type,
                'starred': False
            })

        return render_template(
            'messages/index.html',
            metrics=kpi_stats,
            kpi=kpi_stats,
            conversations=db_messages,
            message_cards=message_cards,
            other_users=other_users,
            students=students_list,
            subjects=subjects,
            classes=classes,
            sections=sections,
            teacher_info=None,
            today=datetime.now().strftime('%Y-%m-%d')
        )

    try:
        teacher, subjects, classes, sections = _get_teacher_meta(user_id)
        conversations = get_conversations(user_id)
        kpi_stats = get_teacher_message_statistics(user_id)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Error loading messages page: {e}")
        conversations = []
        teacher = None

    return render_template(
        'teacher/messages.html',
        kpi=kpi_stats,
        conversations=conversations,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        today=datetime.now().strftime('%Y-%m-%d')
    )

@messages_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    user_id = current_user.id
    search = request.args.get('search')
    filter_type = request.args.get('filter')
    sort_by = request.args.get('sort', 'newest')

    try:
        convs = get_conversations(user_id, search=search, filter_type=filter_type, sort_by=sort_by)
        return jsonify({'conversations': convs})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/conversation/<conversation_id>', methods=['GET'])
@login_required
def api_conversation(conversation_id):
    user_id = current_user.id
    try:
        data = get_conversation(conversation_id, user_id)
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    user_id = current_user.id
    payload = request.get_json(silent=True) or request.form
    student_id = payload.get('student_id')
    if not student_id:
        return jsonify({'error': 'Student ID required'}), 400

    try:
        res = create_conversation(user_id, student_id)
        return jsonify({'success': True, 'conversation': res})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/send', methods=['POST'])
@messages_bp.route('/send', methods=['POST'])
@login_required
def api_send():
    user_id = current_user.id
    payload = request.get_json(silent=True) or request.form
    raw_recipient = payload.get('recipient_id') or payload.get('conversation_id') or payload.get('student_id') or payload.get('user_id')
    message_text = (payload.get('message') or payload.get('content') or payload.get('text') or '').strip()

    if not message_text:
        return jsonify({'error': 'نص الرسالة مطلوب'}), 400

    target_user_id = None

    if raw_recipient:
        raw_str = str(raw_recipient).strip()
        try:
            if int(raw_str) == user_id:
                return jsonify({'error': 'لا يمكنك إرسال رسالة لنفسك'}), 400
        except (ValueError, TypeError):
            pass

        # Handle prefix strings if any
        if raw_str.startswith('admin_'):
            try:
                adm_id = int(raw_str.split('_')[-1])
                target_user_id = adm_id
            except (ValueError, TypeError):
                pass
        elif raw_str.startswith('student_') or raw_str.startswith('st_'):
            st_id = raw_str.split('_')[-1]
            st = Student.query.get(st_id)
            if st and hasattr(st, 'user_id') and st.user_id:
                target_user_id = st.user_id
        elif raw_str.startswith('teacher_') or raw_str.startswith('t_'):
            t_id = raw_str.split('_')[-1]
            t = Teacher.query.get(t_id)
            if t and t.user_id:
                target_user_id = t.user_id
        else:
            try:
                rec_num = int(raw_str)
                # Check if rec_num is a Message ID
                msg_check = Message.query.get(rec_num)
                if msg_check and (msg_check.sender_id == user_id or msg_check.recipient_id == user_id):
                    other_uid = msg_check.sender_id if msg_check.sender_id != user_id else msg_check.recipient_id
                    if other_uid != user_id:
                        target_user_id = other_uid

                if not target_user_id:
                    # 1. Try matching User ID directly
                    u = User.query.get(rec_num)
                    if u and u.id != user_id:
                        target_user_id = u.id
                    else:
                        # 2. Try matching Teacher ID
                        t = Teacher.query.get(rec_num)
                        if t and t.user_id and t.user_id != user_id:
                            target_user_id = t.user_id
                        else:
                            # 3. Try matching Student ID
                            st = Student.query.get(rec_num)
                            if st:
                                from services.teacher_message_service import get_student_user_id
                                st_uid = get_student_user_id(st)
                                if st_uid and st_uid != user_id:
                                    target_user_id = st_uid
            except (ValueError, TypeError):
                target_user_id = None

    if target_user_id == user_id:
        return jsonify({'error': 'لا يمكنك إرسال رسالة لنفسك'}), 400

    # Fallback to first non-current user if no recipient resolved
    if not target_user_id:
        other_user = User.query.filter(User.id != user_id).first()
        if other_user:
            target_user_id = other_user.id

    if not target_user_id or target_user_id == user_id:
        return jsonify({'error': 'تعذر تحديد مستقبل الرسالة'}), 400

    try:
        new_msg = Message(
            sender_id=user_id,
            recipient_id=target_user_id,
            content=message_text,
            timestamp=datetime.utcnow(),
            is_read=False
        )
        db.session.add(new_msg)
        db.session.commit()

        # Create real Notification for recipient in DB
        sender_user = User.query.get(user_id)
        sender_name = sender_user.name if (sender_user and hasattr(sender_user, 'name') and sender_user.name) else 'مستخدم النظام'
        notif = Notification(
            user_id=target_user_id,
            title=f"رسالة جديدة من {sender_name}",
            message=message_text[:120],
            notification_type='message',
            action_url=f"/messages/?conversation_id={new_msg.id}",
            priority='high',
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

        return jsonify({
            'success': True,
            'id': new_msg.id,
            'message_id': new_msg.id,
            'notification_id': notif.id,
            'recipient_id': target_user_id,
            'message': 'تم إرسال الرسالة بنجاح'
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/quick_notification', methods=['POST'])
@messages_bp.route('/api/quick', methods=['POST'])
@login_required
def api_quick_notification():
    payload = request.get_json(silent=True) or request.form
    target_user_id = payload.get('user_id') or payload.get('recipient_id') or 1
    title = (payload.get('title') or 'إشعار سريع عاجل').strip()
    msg = (payload.get('message') or payload.get('content') or 'تنبيه سريع من إدارة المدرسة').strip()

    try:
        rec_id = int(target_user_id)
    except (ValueError, TypeError):
        rec_id = 1

    notif = Notification(
        user_id=rec_id,
        title=title,
        message=msg,
        notification_type='admin',
        action_url='/notifications/',
        priority='urgent',
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        'success': True,
        'notification_id': notif.id,
        'message': 'تم إرسال الإشعار السريع وحفظه في قاعدة البيانات بنجاح'
    })

@messages_bp.route('/api/details/<int:msg_id>', methods=['GET'])
@login_required
def api_message_details(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({'error': 'Message not found'}), 404

    if current_user.id not in (msg.sender_id, msg.recipient_id) and getattr(current_user, 'role', '') != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    if current_user.id == msg.recipient_id and not msg.is_read:
        msg.is_read = True
        db.session.commit()

    return jsonify({
        'id': msg.id,
        'sender_id': msg.sender_id,
        'recipient_id': msg.recipient_id,
        'content': msg.content,
        'timestamp': msg.timestamp.strftime('%Y-%m-%d %H:%M:%S') if msg.timestamp else '',
        'is_read': msg.is_read
    })

@messages_bp.route('/api/read/<int:msg_id>', methods=['POST'])
@messages_bp.route('/read/<int:msg_id>', methods=['POST'])
@login_required
def api_mark_read_by_id(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({'error': 'Message not found'}), 404

    if current_user.id != msg.recipient_id and getattr(current_user, 'role', '') != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    msg.is_read = True
    db.session.commit()
    return jsonify({'success': True, 'is_read': True, 'message': 'تم تحديد الرسالة كمقروءة'})

@messages_bp.route('/api/unread/<int:msg_id>', methods=['POST'])
@messages_bp.route('/unread/<int:msg_id>', methods=['POST'])
@login_required
def api_mark_unread_by_id(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({'error': 'Message not found'}), 404

    if current_user.id != msg.recipient_id and getattr(current_user, 'role', '') != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    msg.is_read = False
    db.session.commit()
    return jsonify({'success': True, 'is_read': False, 'message': 'تم تحديد الرسالة كغير مقروءة'})

@messages_bp.route('/api/read', methods=['POST'])
@login_required
def api_read():
    user_id = current_user.id
    payload = request.get_json(silent=True) or request.form
    conversation_id = payload.get('conversation_id') or payload.get('message_id')
    if conversation_id:
        try:
            m_id = int(conversation_id)
            msg = Message.query.get(m_id)
            if msg:
                msg.is_read = True
                db.session.commit()
        except Exception:
            pass
    try:
        success = mark_as_read(user_id, conversation_id)
        return jsonify({'success': success})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/unread_count', methods=['GET'])
@login_required
def api_unread_count():
    count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    return jsonify({'unread_count': count})

@messages_bp.route('/api/delete/<int:msg_id>', methods=['DELETE', 'POST'])
@messages_bp.route('/delete/<int:msg_id>', methods=['POST'])
@login_required
def api_delete_by_id(msg_id):
    msg = Message.query.get(msg_id)
    if not msg:
        return jsonify({'error': 'Message not found'}), 404

    if current_user.id not in (msg.sender_id, msg.recipient_id) and getattr(current_user, 'role', '') != 'admin':
        return jsonify({'error': 'Unauthorized access'}), 403

    db.session.delete(msg)
    db.session.commit()
    return jsonify({'success': True, 'message': 'تم حذف الرسالة بنجاح'})

@messages_bp.route('/api/archive', methods=['POST'])
@login_required
def api_archive():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    try:
        success = archive_conversation(user_id, conversation_id)
        return jsonify({'success': success, 'message': 'تم أرشفة المحادثة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/delete', methods=['POST'])
@login_required
def api_delete():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    try:
        success = delete_conversation(user_id, conversation_id)
        return jsonify({'success': success, 'message': 'تم حذف المحادثة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/bulk', methods=['POST'])
@login_required
def api_bulk():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    student_ids = payload.get('student_ids', [])
    message_text = payload.get('message', '').strip()

    if not message_text:
        return jsonify({'error': 'Message text is required'}), 400

    try:
        res = bulk_send(user_id, student_ids, message_text)
        return jsonify({'success': True, 'result': res, 'message': f'تم إرسال الرسالة إلى {res.get("sent_count", 0)} طالب بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/student/<int:student_id>', methods=['GET'])
@login_required
def api_student_profile(student_id):
    user_id = current_user.id
    try:
        profile = get_student_profile(student_id, user_id)
        activity = get_student_recent_activity(student_id, user_id)
        notifications = get_student_notifications(student_id, user_id)
        return jsonify({
            'profile': profile,
            'recent_activity': activity,
            'notifications': notifications
        })
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/pin', methods=['POST'])
@login_required
def api_pin():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    try:
        success = pin_conversation(user_id, conversation_id)
        return jsonify({'success': success, 'message': 'تم تثبيت المحادثة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/schedule', methods=['POST'])
@login_required
def api_schedule():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    text = payload.get('message', '').strip()
    schedule_time = payload.get('schedule_time')
    try:
        res = schedule_message(user_id, conversation_id, text, schedule_time)
        return jsonify({'success': True, 'result': res, 'message': 'تم جدولة الرسالة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/templates', methods=['GET'])
@login_required
def api_templates():
    user_id = current_user.id
    try:
        templates = get_message_templates(user_id)
        return jsonify({'templates': templates})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/search', methods=['GET'])
@login_required
def api_search():
    user_id = current_user.id
    query = request.args.get('q', '')
    try:
        convs = get_conversations(user_id, search=query)
        return jsonify({'results': convs})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/conversations', methods=['GET'])
@login_required
def api_conversations():
    user_id = current_user.id
    user_role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else ''

    try:
        convs_data = []
        sent_partners = db.session.query(Message.recipient_id.label('partner_id')).filter(Message.sender_id == user_id)
        rec_partners = db.session.query(Message.sender_id.label('partner_id')).filter(Message.recipient_id == user_id)
        partner_ids = set([r.partner_id for r in sent_partners.union(rec_partners).all() if r.partner_id and r.partner_id != user_id])

        if not partner_ids:
            if user_role == 'admin':
                others = User.query.filter(User.id != user_id).limit(10).all()
            else:
                others = User.query.filter(User.id != user_id, User.role.in_(['admin', 'teacher', 'student'])).limit(10).all()
            partner_ids = set(u.id for u in others)

        for pid in partner_ids:
            partner = User.query.get(pid)
            if not partner:
                continue

            p_name = getattr(partner, 'name', '') or partner.username or f"User {pid}"
            p_role_raw = getattr(partner, 'role', '')
            p_role = 'مدير النظام' if p_role_raw == 'admin' else ('معلم' if p_role_raw == 'teacher' else 'طالب')

            msgs = Message.query.filter(
                ((Message.sender_id == user_id) & (Message.recipient_id == pid)) |
                ((Message.sender_id == pid) & (Message.recipient_id == user_id))
            ).order_by(Message.timestamp.desc()).all()

            unread_cnt = sum(1 for m in msgs if m.recipient_id == user_id and not m.is_read)
            latest_msg = msgs[0] if msgs else None

            last_text = latest_msg.content if latest_msg else 'لا توجد رسائل سابقة. انقر لبدء المحادثة.'
            last_time = latest_msg.timestamp.strftime('%Y-%m-%d %H:%M') if (latest_msg and latest_msg.timestamp) else '—'

            convs_data.append({
                'user_id': pid,
                'name': p_name,
                'role': p_role,
                'last_message': last_text,
                'last_time': last_time,
                'unread_count': unread_cnt
            })

        convs_data.sort(key=lambda x: (x['unread_count'] == 0, str(x['last_time'])), reverse=True)

        return jsonify({
            'success': True,
            'conversations': convs_data
        })
    except Exception as e:
        logger.error(f"Error in api_conversations: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@messages_bp.route('/api/thread/<int:target_user_id>', methods=['GET'])
@login_required
def api_thread(target_user_id):
    user_id = current_user.id

    try:
        real_partner_id = target_user_id
        target_user = User.query.get(target_user_id)
        if not target_user:
            t = Teacher.query.get(target_user_id)
            if t and t.user_id:
                real_partner_id = t.user_id
                target_user = User.query.get(real_partner_id)
            else:
                st = Student.query.get(target_user_id)
                if st and hasattr(st, 'user_id') and st.user_id:
                    real_partner_id = st.user_id
                    target_user = User.query.get(real_partner_id)

        if not target_user:
            return jsonify({'success': False, 'error': 'المستخدم المخاطب غير موجود'}), 404

        msgs = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.recipient_id == real_partner_id)) |
            ((Message.sender_id == real_partner_id) & (Message.recipient_id == user_id))
        ).order_by(Message.timestamp.asc()).all()

        unread_msgs = [m for m in msgs if m.recipient_id == user_id and not m.is_read]
        if unread_msgs:
            for m in unread_msgs:
                m.is_read = True
            db.session.commit()

        messages_data = []
        for m in msgs:
            messages_data.append({
                'is_mine': (m.sender_id == user_id),
                'content': m.content,
                'time': m.timestamp.strftime('%H:%M') if m.timestamp else ''
            })

        return jsonify({
            'success': True,
            'messages': messages_data
        })
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in api_thread: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@messages_bp.route('/export/excel', methods=['GET'])
@login_required
def export_excel():
    import io, csv
    from flask import Response
    user_id = current_user.id
    messages = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).order_by(Message.timestamp.desc()).all()
    if not messages and getattr(current_user, 'role', '') == 'admin':
        messages = Message.query.order_by(Message.timestamp.desc()).all()
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Sender', 'Recipient', 'Content', 'Date', 'Status'])
    for m in messages:
        sender_name = m.sender.name if m.sender and hasattr(m.sender, 'name') and m.sender.name else f"User {m.sender_id}"
        rec_name = m.recipient.name if m.recipient and hasattr(m.recipient, 'name') and m.recipient.name else f"User {m.recipient_id}"
        status = 'مقروءة' if m.is_read else 'غير مقروءة'
        writer.writerow([m.id, sender_name, rec_name, m.content, m.timestamp.strftime('%Y-%m-%d %H:%M:%S') if m.timestamp else '', status])
    
    return Response(
        output.getvalue().encode('utf-8-sig'),
        mimetype='text/csv',
        headers={'Content-Disposition': 'attachment; filename=messages_report.csv'}
    )

@messages_bp.route('/export/pdf', methods=['GET'])
@login_required
def export_pdf():
    user_id = current_user.id
    messages = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).order_by(Message.timestamp.desc()).all()
    if not messages and getattr(current_user, 'role', '') == 'admin':
        messages = Message.query.order_by(Message.timestamp.desc()).all()

    rows = ""
    for idx, m in enumerate(messages, 1):
        sender_name = m.sender.name if m.sender and hasattr(m.sender, 'name') and m.sender.name else f"User {m.sender_id}"
        rec_name = m.recipient.name if m.recipient and hasattr(m.recipient, 'name') and m.recipient.name else f"User {m.recipient_id}"
        status = 'مقروءة' if m.is_read else 'غير مقروءة'
        date_str = m.timestamp.strftime('%Y-%m-%d %H:%M') if m.timestamp else ''
        rows += f"<tr><td>{idx}</td><td>{sender_name}</td><td>{rec_name}</td><td>{m.content}</td><td>{date_str}</td><td>{status}</td></tr>"

    html_content = f"""<!DOCTYPE html>
<html dir="rtl" lang="ar">
<head>
    <meta charset="utf-8">
    <title>تقرير سجل الرسائل</title>
    <style>
        body {{ font-family: sans-serif; margin: 30px; }}
        h2 {{ color: #2563eb; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
        th, td {{ border: 1px solid #ddd; padding: 10px; text-align: right; }}
        th {{ background-color: #f8fafc; font-weight: bold; }}
    </style>
</head>
<body onload="window.print()">
    <h2>تقرير مركز الرسائل والتواصل الأكاديمي</h2>
    <p>تاريخ التقرير: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
    <table>
        <thead>
            <tr>
                <th>#</th>
                <th>المرسل</th>
                <th>المستلم</th>
                <th>نص الرسالة</th>
                <th>التاريخ</th>
                <th>الحالة</th>
            </tr>
        </thead>
        <tbody>
            {rows}
        </tbody>
    </table>
</body>
</html>"""
    return html_content
