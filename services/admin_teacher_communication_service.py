import logging
from datetime import datetime
from sqlalchemy.orm import joinedload, selectinload
from models import db, Teacher, Student, Classes, Subject, Sections, User, Message
from services.teacher_students_service import get_teacher_students_query, get_teacher_by_user_id

logger = logging.getLogger(__name__)

_STORED_REQUESTS = {}
_STORED_ADMIN_MESSAGES = {}
_STORED_ACKNOWLEDGED = set()
_STORED_TASKS = {}

def _get_teacher_scope(user_id):
    user = User.query.get(user_id)
    if not user or getattr(user, 'role', None) != 'teacher':
        raise PermissionError("Access forbidden for non-teacher accounts")

    teacher = get_teacher_by_user_id(user_id)
    if not teacher:
        return user, [], [], []

    query, class_ids, section_ids = get_teacher_students_query(teacher)
    students = query.all()
    return teacher, students, class_ids, section_ids

def get_dashboard_statistics(user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    
    announcements = get_teacher_announcements(user_id)
    new_announcements = len([a for a in announcements if not a.get('acknowledged')])
    
    threads = get_teacher_private_messages(user_id)
    private_messages = len(threads)
    
    user_reqs = _STORED_REQUESTS.get(user_id, [])
    open_requests = len([r for r in user_reqs if r.get('status') in ['Draft', 'Submitted', 'Under Review']])
    approved_requests = len([r for r in user_reqs if r.get('status') == 'Approved'])
    rejected_requests = len([r for r in user_reqs if r.get('status') == 'Rejected'])
    
    tasks = get_assigned_tasks(user_id)
    assigned_tasks = len([t for t in tasks if t.get('status') != 'Completed'])

    return {
        'new_announcements': new_announcements,
        'private_messages': private_messages,
        'open_requests': open_requests,
        'approved_requests': approved_requests,
        'rejected_requests': rejected_requests,
        'assigned_tasks': assigned_tasks,
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M')
    }

def get_teacher_announcements(user_id, search=None, priority=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    raw_announcements = [
        {
            'id': 1001,
            'title': '📢 تعميم إداري: اعتماد الجدول النهائي لاختبارات المنتصف',
            'description': 'نحيطكم علماً بأنه تم اعتماد جدول اختبارات منتصف الفصل الدراسي من قبل الإدارة العامة للمدرسة. يرجى التزام معلمي التخصص بالمواعيد المرصودة.',
            'category': 'اختبارات',
            'sender_name': 'الإدارة العامة للمدرسة',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'time_str': '09:00 ص',
            'priority': 'high',
            'priority_label': 'عاجل 🔴',
            'priority_badge': 'danger',
            'attachment_name': 'جدول_الاختبارات_النهائي.pdf',
            'attachment_url': '#',
            'acknowledged': (user_id, 1001) in _STORED_ACKNOWLEDGED,
            'read': True
        },
        {
            'id': 1002,
            'title': '🗓️ دعوة لحضور اجتماع مجلس المعلمين والتطوير الأكاديمي',
            'description': 'تقرر عقد اجتماع مجلس المعلمين الدوري يوم الأربعاء المقبل بقاعة الاجتماعات الرئيسية لمناقشة خطط التطوير ومخرجات التعليم.',
            'category': 'اجتماعات',
            'sender_name': 'إدارة الشؤون التعليمية',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'time_str': '11:30 ص',
            'priority': 'medium',
            'priority_label': 'هام 🟠',
            'priority_badge': 'warning',
            'attachment_name': 'جدول_أعمال_الاجتماع.docx',
            'attachment_url': '#',
            'acknowledged': (user_id, 1002) in _STORED_ACKNOWLEDGED,
            'read': False
        },
        {
            'id': 1003,
            'title': '📋 تحديث ضوابط رصد الدرجات وتسليم التظلمات الأكاديمية',
            'description': 'تم إضافة تحديثات جديدة لضوابط رصد الدرجات بسجل المعلم الإلكتروني، يرجى الاطلاع على المرفق والإسناد.',
            'category': 'ضوابط',
            'sender_name': 'قسم الجودة والأكاديميا',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'time_str': '01:15 م',
            'priority': 'low',
            'priority_label': 'اعتيادي 🟢',
            'priority_badge': 'success',
            'attachment_name': 'دليل_رصد_الدرجات.pdf',
            'attachment_url': '#',
            'acknowledged': (user_id, 1003) in _STORED_ACKNOWLEDGED,
            'read': True
        }
    ]

    filtered = []
    for item in raw_announcements:
        if priority and priority != 'all' and item['priority'] != priority:
            continue
        if search:
            s_lower = search.lower().strip()
            if not (s_lower in item['title'].lower() or s_lower in item['description'].lower()):
                continue
        filtered.append(item)
    return filtered

def get_teacher_private_messages(user_id, search=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    threads = []
    try:
        msgs = Message.query.filter(
            (Message.sender_id == user_id) | (Message.recipient_id == user_id)
        ).order_by(Message.timestamp.desc()).all()

        interlocutors = {}
        for msg in msgs:
            other_id = msg.recipient_id if msg.sender_id == user_id else msg.sender_id
            if other_id not in interlocutors:
                interlocutors[other_id] = []
            interlocutors[other_id].append(msg)

        for other_id, conv_msgs in interlocutors.items():
            other_user = User.query.get(other_id)
            admin_name = getattr(other_user, 'name', 'إدارة المدرسة')
            admin_role = 'إدارة المدرسة' if getattr(other_user, 'role', '') in ['admin', 'supervisor'] else 'مستخدم'
            last_msg = conv_msgs[0]
            unread = sum(1 for m in conv_msgs if m.recipient_id == user_id and not m.is_read)
            threads.append({
                'conversation_id': other_id,
                'admin_name': admin_name,
                'admin_role': admin_role,
                'last_message': last_msg.content,
                'last_time': last_msg.timestamp.strftime('%H:%M ص') if last_msg.timestamp else '',
                'unread_count': unread,
                'status': 'نشطة'
            })
    except Exception as e:
        logger.error(f"Error querying Message model: {e}")

    stored_list = _STORED_ADMIN_MESSAGES.get(user_id, [])
    if stored_list and not threads:
        admin_user = User.query.filter_by(role='admin').first()
        admin_id = admin_user.id if admin_user else 1
        admin_title = getattr(admin_user, 'name', 'إدارة المدرسة')
        threads.append({
            'conversation_id': admin_id,
            'admin_name': admin_title,
            'admin_role': 'إدارة المدرسة',
            'last_message': stored_list[-1]['text'],
            'last_time': stored_list[-1]['time'],
            'unread_count': 0,
            'status': 'نشطة'
        })

    if search:
        s_lower = search.lower().strip()
        threads = [t for t in threads if s_lower in t['admin_name'].lower() or s_lower in t['last_message'].lower()]

    return threads

def get_conversation(conversation_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    messages = []
    admin_name = 'إدارة المدرسة'
    try:
        other_user = User.query.get(conversation_id)
        if other_user:
            admin_name = getattr(other_user, 'name', 'إدارة المدرسة')

        msgs = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.recipient_id == conversation_id)) |
            ((Message.sender_id == conversation_id) & (Message.recipient_id == user_id))
        ).order_by(Message.timestamp.asc()).all()

        for m in msgs:
            is_me = (m.sender_id == user_id)
            messages.append({
                'id': m.id,
                'sender': 'teacher' if is_me else 'admin',
                'sender_name': getattr(teacher, 'TeacherName', 'المعلم') if is_me else admin_name,
                'text': m.content,
                'time': m.timestamp.strftime('%H:%M ص') if m.timestamp else '',
                'status': 'read' if m.is_read else 'delivered'
            })
    except Exception as e:
        logger.error(f"Error querying conversation messages: {e}")

    stored_list = _STORED_ADMIN_MESSAGES.get(user_id, [])
    for sm in stored_list:
        messages.append(sm)

    return {
        'conversation_id': conversation_id,
        'admin_name': admin_name,
        'messages': messages
    }

def send_message(user_id, message_text, recipient_id=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    try:
        if not recipient_id:
            admin_user = User.query.filter_by(role='admin').first()
            recipient_id = admin_user.id if admin_user else 1

        db_msg = Message(
            sender_id=user_id,
            recipient_id=recipient_id,
            content=message_text,
            timestamp=datetime.utcnow(),
            is_read=False
        )
        db.session.add(db_msg)
        db.session.commit()
    except Exception as e:
        logger.error(f"Error saving message to DB: {e}")
        db.session.rollback()

    msg_obj = {
        'id': int(datetime.now().timestamp()),
        'sender': 'teacher',
        'sender_name': getattr(teacher, 'TeacherName', 'المعلم'),
        'text': message_text,
        'time': datetime.now().strftime('%H:%M ص'),
        'status': 'delivered'
    }

    _STORED_ADMIN_MESSAGES.setdefault(user_id, []).append(msg_obj)
    return msg_obj

def reply_message(user_id, conversation_id, message_text):
    return send_message(user_id, message_text, recipient_id=conversation_id)

def create_request(user_id, request_type, title, description, attachments=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    teacher_name = getattr(teacher, 'TeacherName', 'المعلم')

    user_reqs = _STORED_REQUESTS.setdefault(user_id, [])
    req_obj = {
        'id': len(user_reqs) + 2001,
        'request_type': request_type,
        'title': title,
        'description': description,
        'teacher_name': teacher_name,
        'date_str': datetime.now().strftime('%Y-%m-%d'),
        'status': 'Submitted',
        'status_label': 'مقدم للإدارة 🟡',
        'status_badge': 'warning',
        'attachments': attachments or []
    }

    user_reqs.append(req_obj)
    return req_obj

def get_teacher_requests(user_id, status=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    user_reqs = _STORED_REQUESTS.get(user_id, [])
    if status and status != 'all':
        return [r for r in user_reqs if r.get('status') == status]
    return list(user_reqs)

def cancel_request(request_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    user_reqs = _STORED_REQUESTS.get(user_id, [])
    for r in user_reqs:
        if r['id'] == request_id:
            r['status'] = 'Cancelled'
            r['status_label'] = 'ملغي ⚪'
            r['status_badge'] = 'secondary'
    return True

def get_assigned_tasks(user_id, status=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    user_tasks = _STORED_TASKS.get(user_id, [])
    if status and status != 'all':
        user_tasks = [t for t in user_tasks if t.get('status') == status]
    return list(user_tasks)

def update_task_status(task_id, user_id, status):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    user_tasks = _STORED_TASKS.get(user_id, [])
    for t in user_tasks:
        if t['id'] == task_id:
            t['status'] = status
            if status == 'Completed':
                t['status_label'] = 'مكتمل 🟢'
                t['status_badge'] = 'success'
            elif status == 'Pending':
                t['status_label'] = 'بانتظار القبول 🟡'
                t['status_badge'] = 'warning'
    return True

def acknowledge_announcement(announcement_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    _STORED_ACKNOWLEDGED.add((user_id, announcement_id))
    return True

def archive_conversation(conversation_id, user_id):
    return True

def mark_as_read(conversation_id, user_id):
    return True
