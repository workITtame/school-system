import logging
from datetime import datetime
from sqlalchemy.orm import joinedload, selectinload
from models import db, Teacher, Student, Classes, Subject, Sections, User, Message
from services.teacher_students_service import get_teacher_students_query, get_teacher_by_user_id

logger = logging.getLogger(__name__)

def _get_teacher_scope(user_id):
    teacher = get_teacher_by_user_id(user_id)
    if not teacher:
        user = User.query.get(user_id)
        if user and getattr(user, 'role', '') in ['teacher', 'admin']:
            query = Student.query.filter(Student.is_deleted == False, Student.CID.isnot(None))
            return user, query.all(), [], []
        raise PermissionError("Teacher not found")
    query, class_ids, section_ids = get_teacher_students_query(teacher)
    students = query.all()
    return teacher, students, class_ids, section_ids

def get_teacher_message_statistics(user_id):
    from models.message import Message
    from models.notification import Notification
    today_date = datetime.utcnow().date()
    
    total_messages = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).count()
    unread_count = Message.query.filter_by(recipient_id=user_id, is_read=False).count()
    
    sent_msgs = Message.query.filter(Message.sender_id == user_id, db.func.date(Message.timestamp) == today_date).count()
    rec_msgs = Message.query.filter(Message.recipient_id == user_id, db.func.date(Message.timestamp) == today_date).count()
    
    bulk_sent = Message.query.filter(Message.sender_id == user_id).count()

    latest_msg = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).order_by(Message.timestamp.desc()).first()
    last_act = latest_msg.timestamp.strftime('%H:%M') if latest_msg and latest_msg.timestamp else '—'

    return {
        'total_conversations': total_messages,
        'total_messages': total_messages,
        'unread_count': unread_count,
        'unread_messages': unread_count,
        'sent_messages': sent_msgs,
        'received_messages': rec_msgs,
        'sent_today': sent_msgs,
        'received_today': rec_msgs,
        'bulk_sent': bulk_sent,
        'last_activity': last_act
    }

def get_student_user_id(st):
    if not st:
        return None
    if hasattr(st, 'user_id') and st.user_id:
        return st.user_id
    u = User.query.filter_by(username=f"student_{st.SID}").first()
    if u:
        return u.id
    u = User(
        username=f"student_{st.SID}",
        name=st.SName or f"طالب #{st.SID}",
        role='student'
    )
    u.set_password(f"Student@{st.SID}")
    db.session.add(u)
    db.session.commit()
    return u.id

def get_conversations(user_id, search=None, filter_type=None, sort_by='newest'):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)

    conversations = []

    # 1. FETCH SYSTEM ADMINISTRATOR CONVERSATIONS
    admin_users = User.query.filter(User.role.in_(['admin', 'supervisor'])).all()
    admin_uids = set(a.id for a in admin_users)

    # Also include any user who has exchanged messages with this teacher and is admin or staff
    history_msgs = Message.query.filter((Message.sender_id == user_id) | (Message.recipient_id == user_id)).all()
    for hm in history_msgs:
        other_uid = hm.sender_id if hm.sender_id != user_id else hm.recipient_id
        if other_uid and other_uid not in admin_uids:
            u_check = User.query.get(other_uid)
            if u_check and getattr(u_check, 'role', '') in ['admin', 'supervisor']:
                admin_users.append(u_check)
                admin_uids.add(u_check.id)

    # Default fallback admin if none found
    if not admin_users:
        fallback_admin = User.query.filter_by(role='admin').first()
        if fallback_admin:
            admin_users = [fallback_admin]

    for admin_u in admin_users:
        admin_msgs = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.recipient_id == admin_u.id)) |
            ((Message.sender_id == admin_u.id) & (Message.recipient_id == user_id))
        ).order_by(Message.timestamp.desc()).all()

        unread_cnt = sum(1 for m in admin_msgs if m.recipient_id == user_id and not m.is_read)
        latest_msg = admin_msgs[0] if admin_msgs else None

        if latest_msg:
            last_text = latest_msg.content
            last_time = latest_msg.timestamp.strftime('%H:%M') if latest_msg.timestamp else 'اليوم'
            has_messages = True
            latest_dt = latest_msg.timestamp or datetime.min
            last_sender = 'teacher' if latest_msg.sender_id == user_id else 'admin'
        else:
            last_text = 'قناة التواصل الإداري المباشر مع إدارة المنظومة.'
            last_time = '—'
            has_messages = False
            latest_dt = datetime.min
            last_sender = None

        if search:
            s_lower = search.lower().strip()
            admin_name = (admin_u.name or '').lower()
            if s_lower not in admin_name and 'مدير' not in s_lower and 'ادارة' not in s_lower and 'إدارة' not in s_lower:
                continue

        if filter_type == 'unread' and unread_cnt == 0:
            continue

        conversations.append({
            'conversation_id': f"admin_{admin_u.id}",
            'partner_type': 'admin',
            'user_id': admin_u.id,
            'student_id': f"admin_{admin_u.id}",
            'student_name': admin_u.name or 'مدير النظام التنفيذي',
            'name': admin_u.name or 'مدير النظام التنفيذي',
            'academic_id': 'إدارة النظام',
            'class_name': 'الإدارة العامة',
            'section_name': 'الشؤون الإدارية',
            'role_title': 'مدير النظام التنفيذي',
            'badge_label': 'إدارة المنظومة 🛡️',
            'last_message': last_text,
            'last_message_time': last_time,
            'unread_count': unread_cnt,
            'is_read': (unread_cnt == 0),
            'is_pinned': True,
            'is_archived': False,
            'has_messages': has_messages,
            'last_sender': last_sender,
            '_sort_time': latest_dt,
            'online_status': 'متصل الآن'
        })

    # 2. FETCH STUDENT CONVERSATIONS
    if search:
        s_lower = search.lower().strip()
        students = [st for st in students if s_lower in st.SName.lower() or s_lower in str(st.SID)]

    for st in students:
        st_user_id = get_student_user_id(st)

        # Query real messages between user_id and student
        msgs = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.recipient_id == st_user_id)) |
            ((Message.sender_id == st_user_id) & (Message.recipient_id == user_id))
        ).order_by(Message.timestamp.desc()).all()

        unread_cnt = sum(1 for m in msgs if m.recipient_id == user_id and not m.is_read)
        latest_msg = msgs[0] if msgs else None

        if latest_msg:
            last_text = latest_msg.content
            last_time = latest_msg.timestamp.strftime('%H:%M') if latest_msg.timestamp else 'اليوم'
            has_messages = True
            latest_dt = latest_msg.timestamp or datetime.min
            last_sender = 'teacher' if latest_msg.sender_id == user_id else 'student'
        else:
            last_text = 'لا توجد رسائل سابقة. انقر لبدء المحادثة.'
            last_time = '—'
            has_messages = False
            latest_dt = datetime.min
            last_sender = None

        is_pinned = False
        is_archived = False

        if filter_type == 'unread' and unread_cnt == 0:
            continue
        if filter_type == 'pinned' and not is_pinned:
            continue
        if filter_type == 'archived' and not is_archived:
            continue

        conversations.append({
            'conversation_id': st.SID,
            'partner_type': 'student',
            'student_id': st.SID,
            'student_name': st.SName,
            'name': st.SName,
            'academic_id': str(st.SID),
            'class_name': st.school_class.CName if st.school_class else 'الصف الأول',
            'section_name': st.section.SectionName if st.section else 'شعبة أ',
            'role_title': 'طالب',
            'badge_label': 'طالب 🎓',
            'last_message': last_text,
            'last_message_time': last_time,
            'unread_count': unread_cnt,
            'is_read': (unread_cnt == 0),
            'is_pinned': is_pinned,
            'is_archived': is_archived,
            'has_messages': has_messages,
            'last_sender': last_sender,
            '_sort_time': latest_dt,
            'online_status': 'نشط' if unread_cnt > 0 else 'غير متصل'
        })

    if sort_by == 'unread_first':
        conversations.sort(key=lambda x: (1 if (x.get('partner_type') == 'admin' and x['unread_count'] > 0) else 0, x['unread_count'], x.get('_sort_time', datetime.min)), reverse=True)
    elif sort_by == 'name':
        conversations.sort(key=lambda x: (0 if x.get('partner_type') == 'admin' else 1, x['student_name']))
    else:
        # Default: unread first, admin with messages next, then any messages newest-first
        conversations.sort(key=lambda x: (
            1 if x['unread_count'] > 0 else 0,
            1 if (x.get('partner_type') == 'admin' and x['has_messages']) else 0,
            1 if x['has_messages'] else 0,
            x.get('_sort_time', datetime.min)
        ), reverse=True)
    
    return conversations

_STORED_MESSAGES = {}

def get_conversation(conversation_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    
    conv_str = str(conversation_id).strip()
    target_admin = None
    target_student = None

    # 1. Check if conversation_id explicitly starts with 'admin_'
    if conv_str.startswith('admin_'):
        try:
            admin_uid = int(conv_str.split('_')[-1])
            target_admin = User.query.get(admin_uid)
        except (ValueError, TypeError):
            pass

    # 2. Check if conversation_id is a Message ID (e.g., from notification action_url ?conversation_id=55)
    if not target_admin and conv_str.isdigit():
        int_id = int(conv_str)
        msg = Message.query.get(int_id)
        if msg and (msg.sender_id == user_id or msg.recipient_id == user_id):
            other_uid = msg.sender_id if msg.sender_id != user_id else msg.recipient_id
            other_user = User.query.get(other_uid)
            if other_user and getattr(other_user, 'role', '') in ['admin', 'supervisor']:
                target_admin = other_user
            elif other_user and getattr(other_user, 'role', '') == 'student':
                target_student = Student.query.filter_by(user_id=other_user.id).first()

    # 3. Check if conversation_id is a User ID with admin role
    if not target_admin and not target_student and conv_str.isdigit():
        int_id = int(conv_str)
        u = User.query.get(int_id)
        if u and getattr(u, 'role', '') in ['admin', 'supervisor']:
            target_admin = u

    # 4. Check if conversation_id is a Student ID
    if not target_admin and not target_student and conv_str.isdigit():
        int_id = int(conv_str)
        target_student = Student.query.get(int_id)

    # 5. Default fallback to system admin if string is 'admin'
    if not target_admin and not target_student and conv_str == 'admin':
        target_admin = User.query.filter_by(role='admin').first()

    # ========================================================
    # A. HANDLE ADMIN CONVERSATION
    # ========================================================
    if target_admin:
        db_msgs = Message.query.filter(
            ((Message.sender_id == user_id) & (Message.recipient_id == target_admin.id)) |
            ((Message.sender_id == target_admin.id) & (Message.recipient_id == user_id))
        ).order_by(Message.timestamp.asc()).all()

        # Mark unread incoming messages from admin as read
        unread_msgs = [m for m in db_msgs if m.recipient_id == user_id and not m.is_read]
        if unread_msgs:
            for m in unread_msgs:
                m.is_read = True
            db.session.commit()

        # Mark related notifications as read
        from models.notification import Notification
        try:
            Notification.query.filter(
                Notification.user_id == user_id,
                Notification.is_read == False,
                (Notification.action_url.contains(f"conversation_id={target_admin.id}") |
                 Notification.action_url.contains(f"conversation_id=admin_{target_admin.id}") |
                 Notification.title.contains("مدير النظام") |
                 Notification.title.contains(target_admin.name or ''))
            ).update({'is_read': True}, synchronize_session=False)
            db.session.commit()
        except Exception:
            pass

        teacher_name = getattr(teacher, 'TeacherName', None) or getattr(teacher, 'name', None) or 'المعلم'
        admin_name = target_admin.name or 'مدير النظام التنفيذي'

        messages_list = []
        for m in db_msgs:
            is_from_teacher = (m.sender_id == user_id)
            messages_list.append({
                'id': m.id,
                'sender': 'teacher' if is_from_teacher else 'admin',
                'sender_name': teacher_name if is_from_teacher else admin_name,
                'text': m.content,
                'time': m.timestamp.strftime('%H:%M') if m.timestamp else 'اليوم',
                'status': 'seen' if m.is_read else 'delivered'
            })

        return {
            'partner_type': 'admin',
            'conversation_id': f"admin_{target_admin.id}",
            'admin': {
                'id': target_admin.id,
                'conversation_id': f"admin_{target_admin.id}",
                'name': admin_name,
                'role_title': 'مدير النظام التنفيذي',
                'dept': 'إدارة المنظومة التعليمية',
                'badge': 'إدارة المنظومة 🛡️',
                'online_status': 'متصل الآن'
            },
            'student': {
                'student_id': f"admin_{target_admin.id}",
                'student_name': admin_name,
                'academic_id': 'إدارة النظام',
                'class_name': 'الإدارة العامة',
                'section_name': 'الشؤون الإدارية'
            },
            'messages': messages_list
        }

    # ========================================================
    # B. HANDLE STUDENT CONVERSATION
    # ========================================================
    st = target_student
    if not st or st.is_deleted:
        raise PermissionError("Student out of teacher scope")

    if class_ids and st.CID not in class_ids:
        raise PermissionError("Student outside teacher scope")

    st_user_id = get_student_user_id(st)

    # Query real messages from DB
    db_msgs = Message.query.filter(
        ((Message.sender_id == user_id) & (Message.recipient_id == st_user_id)) |
        ((Message.sender_id == st_user_id) & (Message.recipient_id == user_id))
    ).order_by(Message.timestamp.asc()).all()

    # Auto-mark unread incoming messages as read
    unread_msgs = [m for m in db_msgs if m.recipient_id == user_id and not m.is_read]
    if unread_msgs:
        for m in unread_msgs:
            m.is_read = True
        db.session.commit()

    messages_list = []
    teacher_name = getattr(teacher, 'TeacherName', None) or getattr(teacher, 'name', None) or 'المعلم'

    for m in db_msgs:
        is_from_teacher = (m.sender_id == user_id)
        messages_list.append({
            'id': m.id,
            'sender': 'teacher' if is_from_teacher else 'student',
            'sender_name': teacher_name if is_from_teacher else st.SName,
            'text': m.content,
            'time': m.timestamp.strftime('%H:%M') if m.timestamp else 'اليوم',
            'status': 'seen' if m.is_read else 'delivered'
        })

    # Add memory messages if any
    stored = _STORED_MESSAGES.get(int(st.SID), [])
    if stored:
        messages_list.extend(stored)

    # Calculate real grades for student drawer
    from models.grade import HomeworkMarks, Marks
    from models import Attendance

    hw_marks = HomeworkMarks.query.filter_by(SID=st.SID, is_deleted=False).all()
    hw_scores = [float(hm.Score) for hm in hw_marks if hm.Score is not None]
    hw_avg = round(sum(hw_scores) / len(hw_scores), 1) if hw_scores else 0.0
    if hw_avg > 10.0:
        hw_avg = round(hw_avg / 10.0, 1)

    ex_marks = Marks.query.filter(Marks.SID == st.SID, Marks.assessment_type == 'exam', Marks.is_deleted == False).all()
    ex_scores = [float(em.Score) for em in ex_marks if em.Score is not None]
    exam_avg = round(sum(ex_scores) / len(ex_scores), 1) if ex_scores else 0.0

    att_records = Attendance.query.filter_by(SID=st.SID).all()
    att_pct = round((sum(1 for a in att_records if a.Status in ['حاضر', 'متأخر']) / len(att_records) * 100.0), 1) if att_records else 100.0

    overall_grade = round((exam_avg * 0.7) + ((hw_avg * 10.0) * 0.3), 1) if (exam_avg or hw_avg) else 90.0
    status_txt = 'ممتاز 🟢' if overall_grade >= 90 else ('جيد جداً 🟢' if overall_grade >= 80 else ('جيد 🟡' if overall_grade >= 70 else 'يحتاج متابعة 🟠'))

    student_summary = {
        'student_id': st.SID,
        'student_name': st.SName,
        'academic_id': str(st.SID),
        'class_name': st.school_class.CName if st.school_class else '—',
        'section_name': st.section.SectionName if st.section else '—',
        'attendance_rate': f"{att_pct}%",
        'homework_avg': hw_avg,
        'exam_avg': exam_avg,
        'overall_grade': f"{overall_grade}%",
        'academic_status': status_txt,
        'last_interaction': db_msgs[-1].timestamp.strftime('%Y-%m-%d %H:%M') if db_msgs else 'لا توجد'
    }

    return {
        'partner_type': 'student',
        'student': student_summary,
        'messages': messages_list
    }

def create_conversation(user_id, student_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    st = Student.query.get(student_id)
    if not st or (class_ids and st.CID not in class_ids):
        raise PermissionError("Student outside teacher scope")

    return {
        'conversation_id': st.SID,
        'student_name': st.SName,
        'academic_id': str(st.SID)
    }

def send_message(user_id, conversation_id, message_text):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    conv_str = str(conversation_id).strip()

    # 1. Check if recipient is Admin
    target_admin = None
    if conv_str.startswith('admin_'):
        try:
            admin_uid = int(conv_str.split('_')[-1])
            target_admin = User.query.get(admin_uid)
        except (ValueError, TypeError):
            pass
    elif conv_str.isdigit():
        int_id = int(conv_str)
        # Check if Message.id was passed
        msg = Message.query.get(int_id)
        if msg and (msg.sender_id == user_id or msg.recipient_id == user_id):
            other_uid = msg.sender_id if msg.sender_id != user_id else msg.recipient_id
            other_user = User.query.get(other_uid)
            if other_user and getattr(other_user, 'role', '') in ['admin', 'supervisor']:
                target_admin = other_user
        if not target_admin:
            u = User.query.get(int_id)
            if u and getattr(u, 'role', '') in ['admin', 'supervisor']:
                target_admin = u

    if target_admin:
        teacher_name = getattr(teacher, 'TeacherName', None) or getattr(teacher, 'name', None) or 'المعلم'
        new_msg = Message(
            sender_id=user_id,
            recipient_id=target_admin.id,
            content=message_text,
            timestamp=datetime.utcnow(),
            is_read=False
        )
        db.session.add(new_msg)

        from models.notification import Notification
        notif = Notification(
            user_id=target_admin.id,
            title=f"رد جديد من المعلم ({teacher_name})",
            message=message_text[:150],
            notification_type='message',
            action_url=f"/messages/?conversation_id={user_id}",
            priority='high',
            is_read=False,
            created_at=datetime.utcnow()
        )
        db.session.add(notif)
        db.session.commit()

        return {
            'id': new_msg.id,
            'sender': 'teacher',
            'sender_name': teacher_name,
            'text': message_text,
            'time': datetime.now().strftime('%H:%M'),
            'status': 'delivered'
        }

    # 2. Recipient is Student
    st_id = int(conv_str) if conv_str.isdigit() else None
    st = Student.query.get(st_id) if st_id else None
    if not st or (class_ids and st.CID not in class_ids):
        raise PermissionError("Student outside teacher scope")

    st_user_id = get_student_user_id(st)
    teacher_name = getattr(teacher, 'TeacherName', None) or getattr(teacher, 'name', None) or 'المعلم'

    new_msg = Message(
        sender_id=user_id,
        recipient_id=st_user_id,
        content=message_text,
        timestamp=datetime.utcnow(),
        is_read=False
    )
    db.session.add(new_msg)

    # Create real Notification for recipient student
    from models.notification import Notification
    notif = Notification(
        user_id=st_user_id,
        title=f"رسالة جديدة من المعلم ({teacher_name})",
        message=message_text[:150],
        notification_type='message',
        action_url='/messages/',
        priority='normal',
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.session.add(notif)
    db.session.commit()

    msg_obj = {
        'id': new_msg.id,
        'sender': 'teacher',
        'sender_name': teacher_name,
        'text': message_text,
        'time': datetime.now().strftime('%H:%M'),
        'status': 'delivered'
    }

    return msg_obj

def mark_as_read(user_id, conversation_id):
    st = Student.query.get(conversation_id)
    if st:
        st_user_id = get_student_user_id(st)
        Message.query.filter_by(sender_id=st_user_id, recipient_id=user_id, is_read=False).update({'is_read': True})
        db.session.commit()
    return True

def pin_conversation(user_id, conversation_id):
    return True

def mute_conversation(user_id, conversation_id):
    return True

def archive_conversation(user_id, conversation_id):
    return True

def delete_conversation(user_id, conversation_id):
    return True

def schedule_message(user_id, conversation_id, text, schedule_time):
    return {
        'scheduled_id': int(datetime.now().timestamp()),
        'conversation_id': conversation_id,
        'text': text,
        'schedule_time': schedule_time
    }

def get_student_profile(student_id, user_id):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    st = Student.query.get(student_id)
    if not st or (class_ids and st.CID not in class_ids):
        raise PermissionError("Student outside teacher scope")

    from models.grade import HomeworkMarks, Marks
    from models import Attendance

    hw_marks = HomeworkMarks.query.filter_by(SID=st.SID, is_deleted=False).all()
    hw_scores = [float(hm.Score) for hm in hw_marks if hm.Score is not None]
    hw_avg = round(sum(hw_scores) / len(hw_scores), 1) if hw_scores else 0.0
    if hw_avg > 10.0:
        hw_avg = round(hw_avg / 10.0, 1)

    ex_marks = Marks.query.filter(Marks.SID == st.SID, Marks.assessment_type == 'exam', Marks.is_deleted == False).all()
    ex_scores = [float(em.Score) for em in ex_marks if em.Score is not None]
    exam_avg = round(sum(ex_scores) / len(ex_scores), 1) if ex_scores else 0.0

    att_records = Attendance.query.filter_by(SID=st.SID).all()
    att_pct = round((sum(1 for a in att_records if a.Status in ['حاضر', 'متأخر']) / len(att_records) * 100.0), 1) if att_records else 100.0

    overall_grade = round((exam_avg * 0.7) + ((hw_avg * 10.0) * 0.3), 1) if (exam_avg or hw_avg) else 0.0
    letter_grade = '🟢 ممتاز' if overall_grade >= 90 else ('🟢 جيد جداً' if overall_grade >= 80 else ('🟡 جيد' if overall_grade >= 70 else ('🟠 يحتاج متابعة' if overall_grade >= 60 else '🔴 متعثر')))

    total_assessments = len(hw_scores) + len(ex_scores)
    passed_assessments = sum(1 for s in hw_scores if s >= 6.0) + sum(1 for s in ex_scores if s >= 60.0)
    pass_rate = round((passed_assessments / total_assessments) * 100.0, 1) if total_assessments > 0 else 0.0

    return {
        'student_id': st.SID,
        'student_name': st.SName,
        'academic_id': str(st.SID),
        'class_name': st.school_class.CName if st.school_class else '—',
        'section_name': st.section.SectionName if st.section else '—',
        'subject_name': (teacher.subjects[0].SubName if (hasattr(teacher, 'subjects') and teacher.subjects) else 'المادة الدراسية'),
        'gpa': overall_grade,
        'rank': 1,
        'letter_grade': f"{letter_grade} ({overall_grade}%)" if overall_grade > 0 else "لم تُحدد درجات بعد",
        'pass_rate': pass_rate,
        'homework_completion': f"{hw_avg}/10",
        'exam_average': f"{exam_avg}%",
        'attendance_pct': f"{att_pct}%",
        'final_grade': f"{overall_grade}%",
        'last_activity': 'اليوم'
    }

def get_student_recent_activity(student_id, user_id):
    return [
        {'time': 'اليوم', 'type': 'homework', 'title': 'سجل الواجبات التراكمي للطالب', 'badge': 'نشط 🟢'},
        {'time': 'اليوم', 'type': 'exam', 'title': 'سجل الاختبارات والدوريات', 'badge': 'مرصود 🟢'}
    ]

def get_student_notifications(student_id, user_id):
    from models.notification import Notification
    st = Student.query.get(student_id)
    st_user_id = get_student_user_id(st) if st else 0
    notifs = Notification.query.filter_by(user_id=st_user_id).order_by(Notification.created_at.desc()).limit(5).all()
    
    return [{
        'id': n.id,
        'date': n.created_at.strftime('%Y-%m-%d') if n.created_at else 'اليوم',
        'type': n.notification_type or 'عام',
        'text': n.message
    } for n in notifs]

def get_message_templates(user_id):
    return [
        {'id': 1, 'category': 'واجبات', 'text': 'يرجى تسليم الواجب المطلوب في أقرب وقت.'},
        {'id': 2, 'category': 'اختبارات', 'text': 'يوجد اختبار قصير قريب يرجى الاستعداد والمراجعة.'},
        {'id': 3, 'category': 'درجات', 'text': 'تم تصحيح واجبك وتحديث الدرجة المرصودة بالسجل.'},
        {'id': 4, 'category': 'حضور', 'text': 'يرجى مراجعة سبب الغياب وتأكيده مع إدارة المدرسة.'},
        {'id': 5, 'category': 'تشجيع', 'text': 'أحسنت، ممتاز جداً استمر بهذا المستوى الأكاديمي 👏'},
        {'id': 6, 'category': 'متابعة', 'text': 'تحتاج إلى متابعة إضافية للدروس والتطبيقات ⚠️'}
    ]

def send_homework_reminder(user_id, student_id, homework_title='الواجب الأسبوعي'):
    msg = f"يرجى العلم بأنه يتوجب تسليم ({homework_title}) في موعده المحدد 📚."
    return send_message(user_id, student_id, msg)

def send_exam_reminder(user_id, student_id, exam_title='الاختبار الأكاديمي'):
    msg = f"تذكير أكاديمي: موعد ({exam_title}) قريب يرجى الاستعداد الجيد 📝."
    return send_message(user_id, student_id, msg)

def send_attendance_warning(user_id, student_id):
    msg = "تنبيه الحضور: يرجى الالتزام بمواعيد الحضور والمواظبة اليومية ⚠️."
    return send_message(user_id, student_id, msg)

def bulk_send(user_id, student_ids, message_text):
    teacher, students, class_ids, section_ids = _get_teacher_scope(user_id)
    if not student_ids:
        student_ids = [st.SID for st in students]

    sent_cnt = 0
    from models.notification import Notification
    teacher_name = teacher.TeacherName if teacher else 'المعلم'

    for s_id in student_ids:
        st = Student.query.get(s_id)
        if st:
            st_user_id = get_student_user_id(st)
            new_msg = Message(
                sender_id=user_id,
                recipient_id=st_user_id,
                content=message_text,
                timestamp=datetime.utcnow(),
                is_read=False
            )
            db.session.add(new_msg)
            
            notif = Notification(
                user_id=st_user_id,
                title=f"رسالة جديدة من المعلم ({teacher_name})",
                message=message_text[:150],
                notification_type='message',
                action_url='/messages/',
                priority='normal',
                is_read=False,
                created_at=datetime.utcnow()
            )
            db.session.add(notif)
            sent_cnt += 1

    db.session.commit()
    return {
        'sent_count': sent_cnt,
        'message': message_text
    }

def send_homework_notification(user_id, homework_id, student_ids, text):
    return bulk_send(user_id, student_ids, text)

def send_exam_notification(user_id, exam_id, student_ids, text):
    return bulk_send(user_id, student_ids, text)

def send_grade_notification(user_id, student_id, grade_text):
    return send_message(user_id, student_id, grade_text)

def send_attendance_notification(user_id, student_id, attendance_status):
    msg = f"تنبيه الحضور والغياب: حالة الطالب اليوم هي ({attendance_status})"
    return send_message(user_id, student_id, msg)
