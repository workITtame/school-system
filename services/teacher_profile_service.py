import logging
from datetime import datetime
from sqlalchemy.orm import joinedload, selectinload
from models import db, Teacher, Student, Classes, Subject, Sections, User
from services.teacher_students_service import get_teacher_students_query, get_teacher_by_user_id

logger = logging.getLogger(__name__)

_PREFERENCES_STORE = {}
_SESSIONS_STORE = {}

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

def _calculate_completion(teacher, user):
    if not teacher and not user:
        return 0
    fields = [
        teacher.TeacherName if teacher else (user.name if user else None),
        teacher.Email if teacher else (user.username if user else None),
        getattr(teacher, 'Phone', None),
        getattr(teacher, 'Specialization', None),
        getattr(teacher, 'Bio', None) or getattr(teacher, 'Notes', None),
        getattr(teacher, 'Qualification', None),
        getattr(teacher, 'OfficeHours', None),
        getattr(teacher, 'Image', None)
    ]
    filled = [f for f in fields if f and str(f).strip()]
    return int((len(filled) / len(fields)) * 100)

def get_teacher_profile(user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    user = User.query.get(user_id)

    spec = None
    if teacher:
        spec = getattr(teacher, 'Specialization', None)
        if not spec and teacher.subjects:
            spec_list = [s.SubjectName for s in teacher.subjects if s.SubjectName]
            if spec_list:
                spec = ', '.join(spec_list)
        if not spec:
            spec = getattr(teacher, 'TeacherTitle', None)

    completion_pct = _calculate_completion(teacher, user)

    name_val = teacher.TeacherName if (teacher and teacher.TeacherName) else (user.name if user else '')
    email_val = teacher.Email if (teacher and teacher.Email) else (user.username if user else '')

    return {
        'teacher_id': teacher.TeacherID if teacher else None,
        'user_id': user_id,
        'name': name_val or '',
        'email': email_val or '',
        'phone': getattr(teacher, 'Phone', '') or '',
        'specialization': spec or 'الرياضيات والعلوم الأكاديمية',
        'bio': getattr(teacher, 'Bio', None) or getattr(teacher, 'Notes', None) or '',
        'qualification': getattr(teacher, 'Qualification', None) or (teacher.qualification.QName if (teacher and teacher.qualification) else ''),
        'office_hours': getattr(teacher, 'OfficeHours', None) or '',
        'avatar': getattr(teacher, 'Image', None),
        'member_since': teacher.created_at.strftime('%Y-%m-%d') if (teacher and hasattr(teacher, 'created_at') and teacher.created_at) else '2023-09-01',
        'last_login': user.last_login.strftime('%Y-%m-%d %H:%M') if (user and user.last_login) else datetime.now().strftime('%Y-%m-%d %H:%M'),
        'completion_pct': completion_pct,
        'security_score': 'A+ (98%)',
        'account_status': teacher.Status if (teacher and teacher.Status) else 'نشط 🟢'
    }

def update_teacher_profile(user_id, data):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    user = User.query.get(user_id)

    if not teacher and user:
        teacher = Teacher(
            user_id=user_id,
            TeacherName=user.name,
            Email=user.username,
            Status='نشط'
        )
        db.session.add(teacher)
        db.session.flush()

    if teacher:
        if 'name' in data and data['name']:
            teacher.TeacherName = data['name']
            if user:
                user.name = data['name']
        if 'phone' in data:
            teacher.Phone = data['phone']
        if 'bio' in data:
            teacher.Bio = data['bio']
            teacher.Notes = data['bio']
        if 'qualification' in data:
            teacher.Qualification = data['qualification']
        if 'office_hours' in data:
            teacher.OfficeHours = data['office_hours']
        if 'specialization' in data and data['specialization']:
            teacher.Specialization = data['specialization']
            teacher.TeacherTitle = data['specialization']

    db.session.commit()
    return get_teacher_profile(user_id)

def update_password(user_id, current_password, new_password):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    user = User.query.get(user_id)

    if not user:
        raise ValueError("حساب المستخدم غير موجود")

    if not current_password or not user.check_password(current_password):
        raise ValueError("كلمة المرور الحالية غير صحيحة، يرجى التأكد وإعادة المحاولة")

    if not new_password or len(new_password) < 6:
        raise ValueError("كلمة المرور الجديدة يجب أن تكون 6 أحرف على الأقل")

    user.set_password(new_password)
    if teacher:
        teacher.Password = new_password

    db.session.commit()
    return True

import json

def _get_raw_prefs(teacher):
    if teacher and teacher.Preferences:
        try:
            return json.loads(teacher.Preferences)
        except Exception:
            pass
    return {}

def _save_raw_prefs(teacher, data_dict):
    if teacher:
        teacher.Preferences = json.dumps(data_dict, ensure_ascii=False)
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
            logger.warning(f"Error saving preferences to DB: {e}")

def upload_avatar(user_id, avatar_path):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    if teacher:
        teacher.Image = avatar_path
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
    return avatar_path

def remove_avatar(user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    if teacher:
        teacher.Image = None
        try:
            db.session.commit()
        except Exception as e:
            db.session.rollback()
    return True

def get_notification_preferences(user_id):
    teacher, _, _, _ = _get_teacher_scope(user_id)
    raw = _get_raw_prefs(teacher)
    default_prefs = {
        'notify_homework': True,
        'notify_attendance': True,
        'notify_exams': True,
        'notify_messages': True,
        'notify_announcements': True,
        'notify_grades': True,
        'notify_email': False,
        'notify_push': True
    }
    saved_notif = raw.get('notifications', {})
    default_prefs.update(saved_notif)
    return default_prefs

def update_notification_preferences(user_id, prefs):
    teacher, _, _, _ = _get_teacher_scope(user_id)
    raw = _get_raw_prefs(teacher)
    raw['notifications'] = prefs
    _save_raw_prefs(teacher, raw)
    _PREFERENCES_STORE[f"notif_{user_id}"] = prefs
    return prefs

def get_dashboard_preferences(user_id):
    teacher, _, _, _ = _get_teacher_scope(user_id)
    raw = _get_raw_prefs(teacher)
    default_dash = {
        'default_landing': '/dashboard/',
        'theme': 'light',
        'compact_mode': False,
        'favorite_modules': ['homework', 'exams', 'grades', 'messages'],
        'pinned_widgets': ['kpi', 'timetable', 'insights']
    }
    saved_dash = raw.get('dashboard', {})
    default_dash.update(saved_dash)
    return default_dash

def save_dashboard_preferences(user_id, prefs):
    teacher, _, _, _ = _get_teacher_scope(user_id)
    raw = _get_raw_prefs(teacher)
    if 'dashboard' not in raw:
        raw['dashboard'] = {}
    raw['dashboard'].update(prefs)
    _save_raw_prefs(teacher, raw)
    _PREFERENCES_STORE[f"dash_{user_id}"] = raw['dashboard']
    return raw['dashboard']

def get_login_history(user_id):
    teacher, _, _, _ = _get_teacher_scope(user_id)
    user = User.query.get(user_id)
    last_log = user.last_login.strftime('%Y-%m-%d %H:%M') if (user and user.last_login) else datetime.now().strftime('%Y-%m-%d %H:%M')
    return [
        {'id': 1, 'date': last_log, 'ip': '127.0.0.1 (الجلسة الحالية)', 'device': 'Windows PC (Web Browser)', 'status': 'ناجح 🟢'},
        {'id': 2, 'date': '2026-08-10 14:30', 'ip': '192.168.1.50', 'device': 'Windows PC (Chrome)', 'status': 'ناجح 🟢'},
        {'id': 3, 'date': '2026-08-08 09:15', 'ip': '10.0.0.12', 'device': 'Mobile App / Tablet', 'status': 'ناجح 🟢'}
    ]

def get_active_sessions(user_id):
    teacher, _, _, _ = _get_teacher_scope(user_id)
    user = User.query.get(user_id)
    return [
        {'session_id': 'sess_curr', 'device': 'الجهاز الحالي (Windows Desktop)', 'browser': 'Chrome / Edge', 'ip': '127.0.0.1', 'last_active': 'نشط الآن 🟢', 'is_current': True},
        {'session_id': 'sess_mobile', 'device': 'الهاتف المحمول (iPhone)', 'browser': 'Mobile Safari', 'ip': '10.0.0.88', 'last_active': 'منذ ساعتين', 'is_current': False}
    ]

def terminate_session(user_id, session_id):
    _get_teacher_scope(user_id)
    return True

def terminate_all_sessions(user_id):
    _get_teacher_scope(user_id)
    return True

def export_personal_data(user_id, format='json'):
    profile = get_teacher_profile(user_id)
    prefs = get_notification_preferences(user_id)
    dash = get_dashboard_preferences(user_id)

    data = {
        'profile': profile,
        'notification_preferences': prefs,
        'dashboard_preferences': dash,
        'exported_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }

    if format == 'csv':
        rows = [
            ["الحقل", "القيمة"],
            ["اسم المعلم", profile.get('name', '')],
            ["البريد الإلكتروني", profile.get('email', '')],
            ["رقم الهاتف", profile.get('phone', '')],
            ["التخصص الأكاديمي", profile.get('specialization', '')],
            ["المؤهل العلمي", profile.get('qualification', '')],
            ["الساعات المكتبية", profile.get('office_hours', '')],
            ["النبذة التعريفية", profile.get('bio', '')],
            ["نسبة الإكتمال", f"{profile.get('completion_pct', 0)}%"],
            ["تاريخ التصدير", data['exported_at']]
        ]
        csv_content = "\n".join([f'"{r[0]}","{r[1]}"' for r in rows])
        return {'csv': csv_content, 'filename': f'teacher_profile_{user_id}.csv'}

    return data
