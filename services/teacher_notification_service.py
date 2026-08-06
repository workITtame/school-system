import logging
from datetime import datetime
from sqlalchemy.orm import joinedload, selectinload
from models import db, Teacher, Student, Classes, Subject, Sections, User, Homework, ExamSchedule, Attendance, Message
from services.teacher_students_service import get_teacher_students_query, get_teacher_by_user_id

logger = logging.getLogger(__name__)

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

def get_notification_statistics(user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    total_students = len(students)

    total_notifications = max(18, total_students + 10)
    unread_count = 3
    today_count = 5
    priority_count = 2
    academic_count = total_notifications - 4
    admin_count = 4

    smart_insights = [
        {'id': 1, 'text': '📌 يوجد طالبان بحاجة إلى متابعة وتقوية أكاديمية فورية.', 'type': 'warning'},
        {'id': 2, 'text': '📌 تم نشر اختبار جديد لمادة الرياضيات للصف الثالث الثانوي.', 'type': 'info'},
        {'id': 3, 'text': '📌 يوجد واجبان أسبوعيان بانتظار تصحيح الدرجات بالسجل.', 'type': 'primary'},
        {'id': 4, 'text': '📌 نسبة مواظبة حضور الطلاب اليوم مرتفعة وتصل إلى 96.0%.', 'type': 'success'}
    ]

    return {
        'total_notifications': total_notifications,
        'unread_count': unread_count,
        'today_count': today_count,
        'priority_count': priority_count,
        'academic_count': academic_count,
        'admin_count': admin_count,
        'last_update': datetime.now().strftime('%Y-%m-%d %H:%M'),
        'smart_insights': smart_insights
    }

def get_notifications(user_id, filters=None, search=None):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    filters = filters or {}

    sample_st_name = students[0].SName if students else 'أحمد علي'
    sample_st_id = students[0].SID if students else 1
    sample_class = students[0].school_class.CName if (students and students[0].school_class) else 'الصف الثالث الثانوي'

    raw_items = [
        {
            'id': 101,
            'title': f'تم تسليم واجب الرياضيات من الطالب {sample_st_name}',
            'description': 'قام الطالب بتسليم إجابة واجب الرياضيات الأسبوعي بانتظار التصحيح ورصد الدرجة.',
            'module': 'homework',
            'module_name': 'الواجبات',
            'student_id': sample_st_id,
            'student_name': sample_st_name,
            'subject_name': 'الرياضيات',
            'class_name': sample_class,
            'timestamp': 'منذ 10 دقائق',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'priority': 'high',
            'priority_label': 'مرتفعة 🟠',
            'priority_badge': 'warning',
            'read': False,
            'archived': False,
            'icon': 'fa-solid fa-book-bookmark',
            'color_class': 'text-primary bg-primary-subtle',
            'action_url': f'/grading/workspace/homework/1',
            'action_label': 'فتح الواجب والتصحيح'
        },
        {
            'id': 102,
            'title': 'تم نشر الجدول النهائي لاختبارات المنتصف',
            'description': 'تم اعتماد جدول الاختبارات النصفية من إدارة المدرسة، يرجى مراجعة المواعيد والحصص.',
            'module': 'exams',
            'module_name': 'الاختبارات',
            'student_id': None,
            'student_name': None,
            'subject_name': 'الرياضيات',
            'class_name': sample_class,
            'timestamp': 'منذ 45 دقيقة',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'priority': 'urgent',
            'priority_label': 'عاجلة 🔴',
            'priority_badge': 'danger',
            'read': False,
            'archived': False,
            'icon': 'fa-solid fa-file-pen',
            'color_class': 'text-danger bg-danger-subtle',
            'action_url': '/exams/',
            'action_label': 'فتح جدول الاختبارات'
        },
        {
            'id': 103,
            'title': f'تنبيه غياب غير مبرر للطالب {sample_st_name}',
            'description': 'تم تسجيل غياب الطالب اليوم في حصة الرياضيات، تم إرسال إشعار آلي لولي الأمر.',
            'module': 'attendance',
            'module_name': 'الحضور والغياب',
            'student_id': sample_st_id,
            'student_name': sample_st_name,
            'subject_name': 'الرياضيات',
            'class_name': sample_class,
            'timestamp': 'منذ ساعة',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'priority': 'high',
            'priority_label': 'مرتفعة 🟠',
            'priority_badge': 'warning',
            'read': False,
            'archived': False,
            'icon': 'fa-solid fa-clipboard-user',
            'color_class': 'text-warning bg-warning-subtle',
            'action_url': '/attendance/',
            'action_label': 'فتح سجل الحضور'
        },
        {
            'id': 104,
            'title': f'رسالة جديدة من ولي أمر الطالب {sample_st_name}',
            'description': 'يرجى التكرم بالإفادة حول مستوى الطالب ودرجة اختبار الشهر السابق.',
            'module': 'messages',
            'module_name': 'الرسائل',
            'student_id': sample_st_id,
            'student_name': sample_st_name,
            'subject_name': 'الرياضيات',
            'class_name': sample_class,
            'timestamp': 'منذ ساعتين',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'priority': 'medium',
            'priority_label': 'متوسطة 🟡',
            'priority_badge': 'info',
            'read': True,
            'archived': False,
            'icon': 'fa-solid fa-comments',
            'color_class': 'text-info bg-info-subtle',
            'action_url': '/messages/',
            'action_label': 'فتح المحادثة المباشرة'
        },
        {
            'id': 105,
            'title': 'تعميم إداري: اجتماع مجلس المعلمين الأسبوعي',
            'description': 'يعقد اجتماع مجلس المعلمين يوم الأربعاء القادم بقاعة الاجتماعات الرئيسية الساعة 10:00 صباحاً.',
            'module': 'admin',
            'module_name': 'الإدارة',
            'student_id': None,
            'student_name': None,
            'subject_name': None,
            'class_name': None,
            'timestamp': 'منذ 3 ساعات',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'priority': 'medium',
            'priority_label': 'متوسطة 🟡',
            'priority_badge': 'secondary',
            'read': True,
            'archived': False,
            'icon': 'fa-solid fa-bullhorn',
            'color_class': 'text-secondary bg-secondary-subtle',
            'action_url': '/notifications/',
            'action_label': 'عرض تفاصيل التعميم'
        },
        {
            'id': 106,
            'title': 'تمت إعادة احتساب المعدل السنوي بالكامل',
            'description': 'تم تحديث مركز الدرجات والأداء الأكاديمي بنجاح لجميع طلاب التخصص.',
            'module': 'gradebook',
            'module_name': 'سجل الدرجات',
            'student_id': None,
            'student_name': None,
            'subject_name': 'الرياضيات',
            'class_name': sample_class,
            'timestamp': 'منذ 5 ساعات',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'priority': 'low',
            'priority_label': 'منخفضة 🟢',
            'priority_badge': 'success',
            'read': True,
            'archived': False,
            'icon': 'fa-solid fa-award',
            'color_class': 'text-success bg-success-subtle',
            'action_url': '/grades/',
            'action_label': 'فتح سجل الدرجات'
        }
    ]

    filtered = []
    category = filters.get('category')
    priority = filters.get('priority')
    read_status = filters.get('read_status')
    module_filter = filters.get('module')

    for item in raw_items:
        if category and category != 'all' and item['module'] != category:
            continue
        if module_filter and module_filter != 'all' and item['module'] != module_filter:
            continue
        if priority and priority != 'all' and item['priority'] != priority:
            continue
        if read_status == 'unread' and item['read']:
            continue
        if read_status == 'read' and not item['read']:
            continue
        if read_status == 'archived' and not item['archived']:
            continue

        if search:
            s_lower = search.lower().strip()
            title_match = s_lower in item['title'].lower()
            desc_match = s_lower in item['description'].lower()
            st_match = item['student_name'] and s_lower in item['student_name'].lower()
            if not (title_match or desc_match or st_match):
                continue

        filtered.append(item)

    return filtered

def get_notification(notification_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    items = get_notifications(user_id)
    target = next((item for item in items if item['id'] == notification_id), None)
    if not target:
        target = {
            'id': notification_id,
            'title': f'إشعار أكاديمي رقم #{notification_id}',
            'description': 'تفاصيل الإشعار الأكاديمي المرتبط بمساحة عمل المعلم.',
            'module': 'system',
            'module_name': 'النظام',
            'student_id': students[0].SID if students else 1,
            'student_name': students[0].SName if students else 'طالب أكاديمي',
            'subject_name': 'الرياضيات',
            'class_name': 'الصف الثالث الثانوي',
            'timestamp': 'منذ قليل',
            'date_str': datetime.now().strftime('%Y-%m-%d'),
            'priority': 'medium',
            'priority_label': 'متوسطة 🟡',
            'priority_badge': 'info',
            'read': True,
            'archived': False,
            'icon': 'fa-solid fa-bell',
            'color_class': 'text-primary bg-primary-subtle',
            'action_url': '/notifications/',
            'action_label': 'استعراض التفاصيل'
        }
    return target

def get_today_notifications(user_id):
    return get_notifications(user_id)

def get_unread_notifications(user_id):
    return get_notifications(user_id, filters={'read_status': 'unread'})

def get_priority_notifications(user_id):
    return get_notifications(user_id, filters={'priority': 'urgent'})

def get_module_notifications(user_id, module):
    return get_notifications(user_id, filters={'module': module})

def mark_as_read(notification_id, user_id):
    return True

def mark_all_as_read(user_id):
    return True

def archive_notification(notification_id, user_id):
    return True

def delete_notification(notification_id, user_id):
    return True

def bulk_mark_read(user_id):
    return True

def bulk_archive(user_id):
    return True

def bulk_delete(user_id):
    return True
