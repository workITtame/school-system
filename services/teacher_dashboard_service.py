from datetime import datetime, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from models import db, Student, Teacher, Classes, Sections, Subject, Attendance, ExamSchedule, Homework, User, Message, Days, Lessons
from models.timetable import SchoolTable
from models.grade import Marks

def get_teacher_by_user_id(user_id):
    """Fetch Teacher profile linked to the logged-in User ID or fallback by Email."""
    teacher = Teacher.query.filter_by(user_id=user_id, is_deleted=False).first()
    if not teacher:
        user = User.query.get(user_id)
        if user and hasattr(user, 'email') and user.email:
            teacher = Teacher.query.filter_by(Email=user.email, is_deleted=False).first()
    return teacher

def get_teacher_subject_and_class_ids(teacher):
    """Retrieve teacher's assigned Subject IDs, Class IDs, and Section IDs safely."""
    if not teacher:
        return [], [], []
    
    teacher_subject_ids = [s.SubID for s in teacher.subjects if hasattr(s, 'SubID')]
    slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    
    table_subject_ids = [s.SubID for s in slots if s.SubID]
    teacher_class_ids = list(set([s.CID for s in slots if s.CID]))
    teacher_section_ids = list(set([s.SectionID for s in slots if s.SectionID]))
    
    all_subject_ids = list(set(teacher_subject_ids + table_subject_ids))
    return all_subject_ids, teacher_class_ids, teacher_section_ids

def get_today_classes(teacher_id):
    """
    Fetch today's timetable slots for current teacher from schooltable.
    Returns raw data dicts sorted by start time.
    """
    if not teacher_id:
        return []
        
    today = datetime.now().date()
    now_time_str = datetime.now().strftime('%H:%M')
    arabic_days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    today_day_name = arabic_days[today.weekday()]

    slots = SchoolTable.query.options(
        joinedload(SchoolTable.subject),
        joinedload(SchoolTable.school_class),
        joinedload(SchoolTable.section),
        joinedload(SchoolTable.day),
        joinedload(SchoolTable.lesson)
    ).filter(
        SchoolTable.TeacherID == teacher_id,
        SchoolTable.is_deleted == False
    ).all()

    today_slots = [s for s in slots if s.day and s.day.DName == today_day_name]

    sorted_today_slots = sorted(
        today_slots,
        key=lambda s: (s.lesson.StartTime if (s.lesson and s.lesson.StartTime) else '00:00')
    )

    result = []
    for slot in sorted_today_slots:
        start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
        end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
        sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
        cls_name = slot.school_class.CName if slot.school_class else ''
        sec_name = slot.section.SectionName if slot.section else ''

        if end_t < now_time_str:
            status_code = 'ended'
        elif start_t <= now_time_str <= end_t:
            status_code = 'current'
        else:
            status_code = 'upcoming'

        result.append({
            'subject_name': sub_name,
            'class_name': cls_name,
            'section_name': sec_name,
            'start_time': start_t,
            'end_time': end_t,
            'status_code': status_code
        })

    return result

def get_teacher_students(teacher):
    """
    Fetch all students taught by current teacher across their classes & sections.
    """
    _, class_ids, section_ids = get_teacher_subject_and_class_ids(teacher)
    if not class_ids:
        return []

    query = Student.query.options(
        joinedload(Student.school_class),
        joinedload(Student.section)
    ).filter(
        Student.is_deleted == False,
        Student.CID.in_(class_ids)
    )

    if section_ids:
        query = query.filter(
            or_(Student.SectionID.in_(section_ids), Student.SectionID.is_(None))
        )

    return query.all()

def get_students_needing_attention(teacher):
    """
    Identify students taught by this teacher needing follow-up:
    - Frequent absence (2+ absent days)
    - Low marks (< 60) in teacher's subjects
    Sorted by severity (High -> Medium -> Low).
    """
    students = get_teacher_students(teacher)
    if not students:
        return []

    student_ids = [st.SID for st in students]
    subject_ids, _, _ = get_teacher_subject_and_class_ids(teacher)

    attention_list = []
    
    # 1. Absences check
    absent_counts = db.session.query(
        Attendance.SID, func.count(Attendance.AttendanceID)
    ).filter(
        Attendance.SID.in_(student_ids),
        Attendance.Status == 'غائب'
    ).group_by(Attendance.SID).all()

    absent_map = {sid: count for sid, count in absent_counts}

    # 2. Low grades check
    low_grade_sids = set()
    if subject_ids:
        low_grades = db.session.query(Marks.SID).filter(
            Marks.SID.in_(student_ids),
            Marks.SubID.in_(subject_ids),
            Marks.Score < 60
        ).distinct().all()
        low_grade_sids = {g[0] for g in low_grades}

    for st in students:
        reasons = []
        abs_cnt = absent_map.get(st.SID, 0)
        
        if abs_cnt >= 2:
            reasons.append(f"غياب متكرر ({abs_cnt} أيام)")
        if st.SID in low_grade_sids:
            reasons.append("درجات منخفضة (< 60)")

        if reasons:
            cls_name = st.school_class.CName if st.school_class else ''
            sec_name = st.section.SectionName if st.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")
            
            severity_rank = 1 if (abs_cnt >= 4 or st.SID in low_grade_sids) else 2
            severity_label = 'عالي' if severity_rank == 1 else 'متوسط'

            attention_list.append({
                'student_name': st.SName,
                'class_name': full_cls,
                'reasons': reasons,
                'reason_str': "، ".join(reasons),
                'severity_rank': severity_rank,
                'severity_label': severity_label
            })

    # Sort High -> Medium
    attention_list = sorted(attention_list, key=lambda x: x['severity_rank'])
    return attention_list[:10]

def get_pending_homeworks(teacher):
    """
    Fetch homeworks created for teacher's subjects sorted by:
    1. Pending/Uncorrected first
    2. Nearest due date
    """
    subject_ids, class_ids, _ = get_teacher_subject_and_class_ids(teacher)
    if not subject_ids and not class_ids:
        return []

    today = datetime.now().date()
    
    query = Homework.query.options(
        joinedload(Homework.subject),
        joinedload(Homework.school_class),
        joinedload(Homework.section)
    )

    if subject_ids:
        query = query.filter(Homework.sub_id.in_(subject_ids))
    elif class_ids:
        query = query.filter(Homework.class_id.in_(class_ids))

    homeworks = query.order_by(Homework.due_date.asc()).all()

    result = []
    for hw in homeworks:
        sub_name = hw.subject.SubName if hw.subject else ''
        cls_name = hw.school_class.CName if hw.school_class else ''
        sec_name = hw.section.SectionName if hw.section else ''
        full_cls = f"{cls_name} - {sec_name}".strip(" -")

        if hw.status == 'مكتمل':
            status_code = 'completed'
        elif hw.due_date and hw.due_date < today:
            status_code = 'overdue'
        else:
            status_code = 'pending'

        result.append({
            'title': hw.title,
            'subject_name': sub_name,
            'class_name': full_cls,
            'due_date': hw.due_date,
            'status_code': status_code,
            'is_pending': hw.status != 'مكتمل'
        })

    # Sort: pending/overdue first, completed last
    result = sorted(result, key=lambda x: (0 if x['is_pending'] else 1, x['due_date'] or today))
    return result

def get_upcoming_exams(teacher):
    """
    Fetch upcoming exams for teacher's subjects from ExamSchedule.
    """
    subject_ids, class_ids, _ = get_teacher_subject_and_class_ids(teacher)
    if not subject_ids and not class_ids:
        return []

    today = datetime.now().date()

    query = ExamSchedule.query.options(
        joinedload(ExamSchedule.subject),
        joinedload(ExamSchedule.school_class),
        joinedload(ExamSchedule.section)
    ).filter(
        ExamSchedule.is_deleted == False,
        ExamSchedule.ExamDate >= today
    )

    if subject_ids:
        query = query.filter(ExamSchedule.SubID.in_(subject_ids))
    elif class_ids:
        query = query.filter(ExamSchedule.CID.in_(class_ids))

    exams = query.order_by(ExamSchedule.ExamDate.asc()).all()

    result = []
    for ex in exams:
        sub_name = ex.subject.SubName if ex.subject else ''
        cls_name = ex.school_class.CName if ex.school_class else ''
        sec_name = ex.section.SectionName if ex.section else ''
        full_cls = f"{cls_name} - {sec_name}".strip(" -")

        result.append({
            'title': ex.ExamName or f"اختبار {sub_name}",
            'subject_name': sub_name,
            'class_name': full_cls,
            'exam_date': ex.ExamDate,
            'exam_time': ex.ExamTime or '08:00',
            'location': ex.Location or 'قاعة الاختبارات'
        })

    return result

def get_teacher_notifications(user_id):
    """
    Fetch latest 5 notifications/messages strictly for current teacher sorted by unread first.
    """
    messages = Message.query.filter(
        or_(Message.recipient_id == user_id, Message.sender_id == user_id)
    ).order_by(Message.is_read.asc(), Message.timestamp.desc()).limit(5).all()

    result = []
    for m in messages:
        sender_name = m.sender.name if (hasattr(m, 'sender') and m.sender) else 'نظام المدرسة'
        result.append({
            'title': f"رسالة من {sender_name}",
            'content': m.content,
            'timestamp': m.timestamp,
            'category': 'رسالة',
            'is_read': m.is_read
        })

    if not result:
        result = [
            {'title': 'إشعار إداري', 'content': 'مرحباً بك في لوحة تحكم المعلم التنفيذية المخصصة لجدولك والطلاب.', 'timestamp': datetime.now(), 'category': 'إداري', 'is_read': True},
            {'title': 'تنبيه الواجبات', 'content': 'يرجى متابعة تصحيح الواجبات المسلمة من قبل الطلاب.', 'timestamp': datetime.now() - timedelta(hours=2), 'category': 'واجب', 'is_read': False}
        ]

    return result[:5]

def get_dashboard_statistics(teacher):
    """
    Aggregates top summary cards and metadata for current teacher.
    """
    today_classes = get_today_classes(teacher.TeacherID if teacher else None)
    today_classes_count = len(today_classes)
    remaining_classes_count = sum(1 for c in today_classes if c['status_code'] != 'ended')

    students = get_teacher_students(teacher)
    total_students_count = len(students)

    homeworks = get_pending_homeworks(teacher)
    pending_homeworks_count = sum(1 for hw in homeworks if hw.get('is_pending'))

    exams = get_upcoming_exams(teacher)
    upcoming_exams_count = len(exams)

    teacher_name = teacher.TeacherName if teacher else 'المعلم الأكاديمي'
    teacher_title = teacher.TeacherTitle if (teacher and teacher.TeacherTitle) else 'معلم أكاديمي'
    subjects_list = [s.SubName for s in teacher.subjects] if (teacher and teacher.subjects) else []
    subjects_str = " | ".join(subjects_list) if subjects_list else 'المواد الدراسية'

    now_time = datetime.now()
    arabic_days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    current_day_name = arabic_days[now_time.weekday()]
    current_date_str = now_time.strftime('%Y-%m-%d')
    last_update_time = now_time.strftime('%H:%M')

    return {
        'today_classes_count': today_classes_count,
        'remaining_classes_count': remaining_classes_count,
        'total_students_count': total_students_count,
        'pending_homeworks_count': pending_homeworks_count,
        'upcoming_exams_count': upcoming_exams_count,
        'teacher_name': teacher_name,
        'teacher_title': teacher_title,
        'subjects_str': subjects_str,
        'current_day_name': current_day_name,
        'current_date_str': current_date_str,
        'last_update_time': last_update_time
    }
