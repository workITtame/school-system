import logging
from datetime import datetime, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from models import db, Student, Teacher, Classes, Sections, Subject, Attendance, ExamSchedule, Homework, User, Message, Days, Lessons
from models.timetable import SchoolTable
from models.grade import Marks

logger = logging.getLogger(__name__)

def get_teacher_by_user_id(user_id):
    """Fetch Teacher profile linked to the logged-in User ID or fallback by Email/username."""
    try:
        teacher = Teacher.query.filter_by(user_id=user_id, is_deleted=False).first()
        if not teacher:
            user = User.query.get(user_id)
            if user:
                email_val = getattr(user, 'email', None) or getattr(user, 'username', None)
                if email_val:
                    teacher = Teacher.query.filter_by(Email=email_val, is_deleted=False).first()
        return teacher
    except Exception as e:
        logger.exception("Error in get_teacher_by_user_id: %s", str(e))
        return None

def get_teacher_subject_and_class_ids(teacher):
    """Retrieve teacher's assigned Subject IDs, Class IDs, and Section IDs safely using joinedload."""
    if not teacher:
        return [], [], []
    
    try:
        teacher_subject_ids = [s.SubID for s in teacher.subjects if hasattr(s, 'SubID')]
        slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
        
        table_subject_ids = [s.SubID for s in slots if s.SubID]
        teacher_class_ids = list(set([s.CID for s in slots if s.CID]))
        teacher_section_ids = list(set([s.SectionID for s in slots if s.SectionID]))
        
        all_subject_ids = list(set(teacher_subject_ids + table_subject_ids))
        return all_subject_ids, teacher_class_ids, teacher_section_ids
    except Exception as e:
        logger.exception("Error in get_teacher_subject_and_class_ids: %s", str(e))
        return [], [], []

def get_today_classes(teacher_id):
    """
    Fetch today's timetable slots for current teacher from schooltable.
    Uses eager loading (joinedload) to prevent N+1 queries.
    """
    if not teacher_id:
        return []
        
    try:
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
    except Exception as e:
        logger.exception("Error in get_today_classes: %s", str(e))
        return []

def get_teacher_students(teacher):
    """
    Fetch all students taught by current teacher across their classes & sections.
    """
    try:
        _, class_ids, section_ids = get_teacher_subject_and_class_ids(teacher)
        query = Student.query.options(
            joinedload(Student.school_class),
            joinedload(Student.section)
        ).filter(Student.is_deleted == False, Student.CID.isnot(None))

        if class_ids:
            query = query.filter(Student.CID.in_(class_ids))
            if section_ids:
                query = query.filter(or_(Student.SectionID.in_(section_ids), Student.SectionID.is_(None)))

        return query.all()
    except Exception as e:
        logger.exception("Error in get_teacher_students: %s", str(e))
        return []

def get_students_needing_attention(teacher):
    """
    Identify students taught by this teacher needing follow-up:
    - Frequent absence (2+ absent days)
    - Low marks (< 60) in teacher's subjects
    Sorted by severity (High -> Medium -> Low).
    """
    try:
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

        # 2. Low grades check (Exam Marks and HomeworkMarks)
        from models.grade import HomeworkMarks
        low_grade_sids = set()
        if subject_ids:
            low_grades = db.session.query(Marks.SID).filter(
                Marks.SID.in_(student_ids),
                Marks.SubID.in_(subject_ids),
                Marks.assessment_type == 'exam',
                Marks.Score < 60
            ).distinct().all()
            low_hw = db.session.query(HomeworkMarks.SID).filter(
                HomeworkMarks.SID.in_(student_ids),
                HomeworkMarks.SubID.in_(subject_ids),
                HomeworkMarks.Score < 60
            ).distinct().all()
            low_grade_sids = {g[0] for g in low_grades} | {h[0] for h in low_hw}

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
                primary_reason_type = 'grade' if st.SID in low_grade_sids else 'attendance'

                attention_list.append({
                    'student_id': st.SID,
                    'student_name': st.SName,
                    'class_name': full_cls,
                    'reasons': reasons,
                    'reason_str': "، ".join(reasons),
                    'severity_rank': severity_rank,
                    'severity_label': severity_label,
                    'primary_reason_type': primary_reason_type
                })

        attention_list = sorted(attention_list, key=lambda x: x['severity_rank'])
        return attention_list[:10]
    except Exception as e:
        logger.exception("Error in get_students_needing_attention: %s", str(e))
        return []

def get_pending_exam_corrections(teacher):
    """
    Fetch ended exams for teacher's subjects that require grade entry in Marks.
    """
    try:
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
            ExamSchedule.ExamDate <= today
        )

        if subject_ids:
            query = query.filter(ExamSchedule.SubID.in_(subject_ids))
        if class_ids:
            query = query.filter(ExamSchedule.CID.in_(class_ids))

        ended_exams = query.order_by(ExamSchedule.ExamDate.desc()).all()
        if not ended_exams:
            return []

        ended_exam_ids = [ex.ScheduleID for ex in ended_exams]
        graded_exam_ids = set(
            g[0] for g in db.session.query(Marks.ExamID).filter(
                Marks.ExamID.in_(ended_exam_ids),
                Marks.assessment_type == 'exam',
                Marks.Score.isnot(None)
            ).distinct().all()
        )

        pending_exams = [ex for ex in ended_exams if ex.ScheduleID not in graded_exam_ids]
        return pending_exams
    except Exception as e:
        logger.exception("Error in get_pending_exam_corrections: %s", str(e))
        return []

def get_pending_homeworks(teacher):
    """
    Fetch homeworks created for teacher's subjects sorted by:
    1. Pending/Uncorrected first (based on actual HomeworkMarks submissions needing correction)
    2. Nearest due date
    """
    try:
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
        if class_ids:
            query = query.filter(Homework.class_id.in_(class_ids))

        homeworks = query.order_by(Homework.due_date.asc()).all()
        if not homeworks:
            return []

        # Query actual HomeworkMarks records for teacher's scoped homeworks
        hw_ids = [hw.id for hw in homeworks]
        from models.grade import HomeworkMarks
        hm_records = HomeworkMarks.query.filter(
            HomeworkMarks.HomeworkID.in_(hw_ids),
            HomeworkMarks.is_deleted == False
        ).all()

        hm_by_hw = {}
        for hm in hm_records:
            hm_by_hw.setdefault(hm.HomeworkID, []).append(hm)

        result = []
        for hw in homeworks:
            sub_name = hw.subject.SubName if hw.subject else ''
            cls_name = hw.school_class.CName if hw.school_class else ''
            sec_name = hw.section.SectionName if hw.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")

            marks_list = hm_by_hw.get(hw.id, [])
            has_submissions = len(marks_list) > 0
            has_unscored = any(hm.Score is None for hm in marks_list)

            # A homework is pending correction ONLY if it has actual student submissions/marks in HomeworkMarks AND is not completed
            is_pending_correction = has_submissions and (hw.status != 'مكتمل' or has_unscored)

            if hw.status == 'مكتمل' and not has_unscored:
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
                'is_pending': is_pending_correction
            })

        result = sorted(result, key=lambda x: (0 if x['is_pending'] else 1, x['due_date'] or today))
        return result
    except Exception as e:
        logger.exception("Error in get_pending_homeworks: %s", str(e))
        return []

def get_upcoming_exams(teacher):
    """
    Fetch upcoming exams for teacher's subjects from ExamSchedule.
    """
    try:
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
    except Exception as e:
        logger.exception("Error in get_upcoming_exams: %s", str(e))
        return []

def get_teacher_notifications(user_id):
    """
    Fetch latest 5 notifications/messages merging Notification model and Message model.
    """
    try:
        from models import Notification

        # System notifications
        sys_notifs = Notification.query.filter(
            or_(Notification.user_id == user_id, Notification.user_id.is_(None))
        ).order_by(Notification.created_at.desc()).limit(5).all()

        # Messages
        messages = Message.query.filter(
            or_(Message.recipient_id == user_id, Message.sender_id == user_id)
        ).order_by(Message.timestamp.desc()).limit(5).all()

        combined = []
        for n in sys_notifs:
            combined.append({
                'title': n.title or 'تنبيه النظام',
                'content': n.message or '',
                'timestamp': n.created_at or datetime.now(),
                'category': 'إشعار',
                'is_read': bool(n.is_read)
            })

        for m in messages:
            sender_name = m.sender.name if (hasattr(m, 'sender') and m.sender) else 'نظام المدرسة'
            combined.append({
                'title': f"رسالة من {sender_name}",
                'content': m.content or '',
                'timestamp': m.timestamp or datetime.now(),
                'category': 'رسالة',
                'is_read': bool(m.is_read)
            })

        combined.sort(key=lambda x: (0 if not x['is_read'] else 1, x['timestamp'] or datetime.now()), reverse=True)
        return combined[:5]
    except Exception as e:
        logger.exception("Error in get_teacher_notifications: %s", str(e))
        return []

def get_dashboard_statistics(teacher):
    """
    Aggregates top summary cards and metadata for current teacher.
    """
    try:
        today_classes = get_today_classes(teacher.TeacherID if teacher else None)
        today_classes_count = len(today_classes)
        remaining_classes_count = sum(1 for c in today_classes if c['status_code'] != 'ended')
        next_class = next((c for c in today_classes if c['status_code'] in ('current', 'upcoming')), None)

        students = get_teacher_students(teacher)
        total_students_count = len(students)

        homeworks = get_pending_homeworks(teacher)
        pending_homeworks_count = sum(1 for hw in homeworks if hw.get('is_pending'))

        exams = get_upcoming_exams(teacher)
        upcoming_exams_count = len(exams)

        pending_exam_corrections = get_pending_exam_corrections(teacher)
        pending_exam_corrections_count = len(pending_exam_corrections)

        attention_students = get_students_needing_attention(teacher)
        attention_students_count = len(attention_students)

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
            'next_class': next_class,
            'total_students_count': total_students_count,
            'pending_homeworks_count': pending_homeworks_count,
            'upcoming_exams_count': upcoming_exams_count,
            'pending_exam_corrections_count': pending_exam_corrections_count,
            'attention_students_count': attention_students_count,
            'teacher_name': teacher_name,
            'teacher_title': teacher_title,
            'subjects_str': subjects_str,
            'current_day_name': current_day_name,
            'current_date_str': current_date_str,
            'last_update_time': last_update_time
        }
    except Exception as e:
        logger.exception("Error in get_dashboard_statistics: %s", str(e))
        now_time = datetime.now()
        return {
            'today_classes_count': 0,
            'remaining_classes_count': 0,
            'next_class': None,
            'total_students_count': 0,
            'pending_homeworks_count': 0,
            'upcoming_exams_count': 0,
            'pending_exam_corrections_count': 0,
            'attention_students_count': 0,
            'teacher_name': 'المعلم الأكاديمي',
            'teacher_title': 'معلم أكاديمي',
            'subjects_str': 'المواد الدراسية',
            'current_day_name': 'اليوم',
            'current_date_str': now_time.strftime('%Y-%m-%d'),
            'last_update_time': now_time.strftime('%H:%M')
        }
