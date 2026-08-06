import logging
from datetime import datetime
from sqlalchemy.orm import joinedload, selectinload
from models import db, Teacher, Student, Classes, Subject, Sections, User
from services.teacher_students_service import get_teacher_students_query, get_teacher_by_user_id

logger = logging.getLogger(__name__)

_STORED_REQUESTS = []
_STORED_ADMIN_MESSAGES = {}
_STORED_ACKNOWLEDGED = set()

def _get_teacher_scope(user_id):
    user = User.query.get(user_id)
    if not user or getattr(user, 'role', None) != 'teacher':
        raise PermissionError("Access forbidden for non-teacher accounts")

    teacher = Teacher.query.filter_by(user_id=user_id, is_deleted=False).first()
    if not teacher and hasattr(user, 'email') and user.email:
        teacher = Teacher.query.filter_by(Email=user.email, is_deleted=False).first()

    if not teacher:
        raise PermissionError("Teacher record not found")

    query, class_ids, section_ids = get_teacher_students_query(teacher)
    students = query.all()
    return teacher, students, class_ids, section_ids

def get_dashboard_statistics(user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    
    new_announcements = 3
    private_messages = 2
    open_requests = len([r for r in _STORED_REQUESTS if r.get('status') in ['Draft', 'Submitted', 'Under Review']]) + 1
    approved_requests = len([r for r in _STORED_REQUESTS if r.get('status') == 'Approved']) + 2
    rejected_requests = len([r for r in _STORED_REQUESTS if r.get('status') == 'Rejected'])
    assigned_tasks = 4

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
            'acknowledged': 1001 in _STORED_ACKNOWLEDGED,
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
            'acknowledged': 1002 in _STORED_ACKNOWLEDGED,
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
            'acknowledged': 1003 in _STORED_ACKNOWLEDGED,
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

    stored_list = _STORED_ADMIN_MESSAGES.get(user_id, [])
    
    threads = [
        {
            'conversation_id': 501,
            'admin_name': 'إدارة الموارد البشرية والتعيينات',
            'admin_role': 'الإدارة المركزية',
            'last_message': stored_list[-1]['text'] if stored_list else 'تمت الموافقة المبدئية على طلب تعديل النصاب الأسبوعي.',
            'last_time': stored_list[-1]['time'] if stored_list else '10:15 ص',
            'unread_count': 0,
            'status': 'نشطة'
        },
        {
            'conversation_id': 502,
            'admin_name': 'مكتب الناظر والمدير الأكاديمي',
            'admin_role': 'إدارة المدرسة',
            'last_message': 'يرجى تزويدنا بتقرير متابعة الطلاب المتعثرين قبل نهاية الأسبوع.',
            'last_time': 'أمس 02:00 م',
            'unread_count': 1,
            'status': 'بانتظار الرد'
        }
    ]

    if search:
        s_lower = search.lower().strip()
        threads = [t for t in threads if s_lower in t['admin_name'].lower() or s_lower in t['last_message'].lower()]

    return threads

def get_conversation(conversation_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    default_messages = [
        {
            'id': 1,
            'sender': 'admin',
            'sender_name': 'إدارة الموارد البشرية والتعيينات',
            'text': f'مرحباً بك أستاذ {teacher.TeacherName}، نود إحاطتكم بتحديث نصاب الحصص الأسبوعي.',
            'time': '09:00 ص',
            'status': 'read'
        },
        {
            'id': 2,
            'sender': 'teacher',
            'sender_name': teacher.TeacherName,
            'text': 'أهلاً بحضرتك، شاكر جداً للتحديث وسأقوم بالمتابعة والالتزام فوراً.',
            'time': '09:15 ص',
            'status': 'delivered'
        }
    ]

    stored_list = _STORED_ADMIN_MESSAGES.get(user_id, [])
    full_stream = default_messages + stored_list

    return {
        'conversation_id': conversation_id,
        'admin_name': 'إدارة الموارد البشرية والتعيينات',
        'messages': full_stream
    }

def send_message(user_id, message_text, recipient_id=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    msg_obj = {
        'id': int(datetime.now().timestamp()),
        'sender': 'teacher',
        'sender_name': teacher.TeacherName,
        'text': message_text,
        'time': datetime.now().strftime('%H:%M ص'),
        'status': 'delivered'
    }

    _STORED_ADMIN_MESSAGES.setdefault(user_id, []).append(msg_obj)
    return msg_obj

def reply_message(user_id, conversation_id, message_text):
    return send_message(user_id, message_text)

def create_request(user_id, request_type, title, description, attachments=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    req_obj = {
        'id': len(_STORED_REQUESTS) + 2001,
        'request_type': request_type,
        'title': title,
        'description': description,
        'teacher_name': teacher.TeacherName,
        'date_str': datetime.now().strftime('%Y-%m-%d'),
        'status': 'Submitted',
        'status_label': 'مقدم للإدارة 🟡',
        'status_badge': 'warning',
        'attachments': attachments or []
    }

    _STORED_REQUESTS.append(req_obj)
    return req_obj

def get_teacher_requests(user_id, status=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    defaults = [
        {
            'id': 1991,
            'request_type': 'إجازة اعتيادية',
            'title': 'طلب إجازة اعتيادية لمدة يومين',
            'description': 'يرجى الموافقة على طلب إجازة قصيرة لظروف عائلية وتكليف المعلم البديل.',
            'teacher_name': teacher.TeacherName,
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Approved',
            'status_label': 'معتمد 🟢',
            'status_badge': 'success',
            'attachments': []
        },
        {
            'id': 1992,
            'request_type': 'تعديل الجدول',
            'title': 'طلب تبديل حصة الرياضيات الرابعة',
            'description': 'طلب تبديل الحصة الرابعة يوم الثلاثاء مع المعلم التخصصي.',
            'teacher_name': teacher.TeacherName,
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'status': 'Under Review',
            'status_label': 'قيد المراجعة 🟡',
            'status_badge': 'warning',
            'attachments': []
        }
    ]

    all_reqs = defaults + _STORED_REQUESTS
    if status and status != 'all':
        all_reqs = [r for r in all_reqs if r['status'] == status]
    return all_reqs

def cancel_request(request_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    for r in _STORED_REQUESTS:
        if r['id'] == request_id:
            r['status'] = 'Cancelled'
            r['status_label'] = 'ملغي ⚪'
            r['status_badge'] = 'secondary'
    return True

def get_assigned_tasks(user_id, status=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    tasks = [
        {
            'id': 3001,
            'title': '📋 الإشراف على مراقبة اختبار المنتصف بالقاعة #4',
            'description': 'تكليف إداري بالإشراف والتواجد بقاعة الاختبارات الرئيسية الحصة الثانية.',
            'due_date': '2026-08-10',
            'priority': 'عاجل',
            'status': 'Pending',
            'status_label': 'بانتظار القبول 🟡',
            'status_badge': 'warning'
        },
        {
            'id': 3002,
            'title': '📊 تسليم التقرير الأكاديمي الشهري للطلاب المتعثرين',
            'description': 'يرجى إرفاق تقرير المتابعة الخاص بمركز الدرجات لمكتب مدير المدرسة.',
            'due_date': '2026-08-12',
            'priority': 'هام',
            'status': 'Completed',
            'status_label': 'مكتمل 🟢',
            'status_badge': 'success'
        }
    ]

    if status and status != 'all':
        tasks = [t for t in tasks if t['status'] == status]
    return tasks

def update_task_status(task_id, user_id, status):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    return True

def acknowledge_announcement(announcement_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    _STORED_ACKNOWLEDGED.add(announcement_id)
    return True

def archive_conversation(conversation_id, user_id):
    return True

def mark_as_read(conversation_id, user_id):
    return True
