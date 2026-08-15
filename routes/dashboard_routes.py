from flask import Blueprint, render_template, session, jsonify, request, flash, redirect, url_for
from flask_login import login_required, current_user
from models import db, Student, Teacher, Classes, Sections, Subject, Attendance, ExamSchedule, Homework, User, Message, Days, Lessons, Notification, School
from models.timetable import SchoolTable
from models.grade import Marks
from sqlalchemy import func, text, or_
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)

def get_teacher_dashboard_data(user_id):
    """
    Fetch scoped metrics, current/next lessons, today's schedule, 
    homeworks, messages, notifications, charts, and performance strictly for the current teacher.
    Zero N+1 queries using joinedload.
    """
    today = datetime.now().date()
    now_time_str = datetime.now().strftime('%H:%M')
    arabic_days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    today_day_name = arabic_days[today.weekday()]

    teacher = Teacher.query.options(joinedload(Teacher.subjects)).filter_by(user_id=user_id).first()
    
    teacher_name = teacher.TeacherName if teacher else 'معلم أكاديمي'
    teacher_title = teacher.TeacherTitle if (teacher and teacher.TeacherTitle) else 'معلم أكاديمي'
    teacher_status = teacher.Status if (teacher and teacher.Status) else 'نشط'
    subjects_list = [s.SubName for s in teacher.subjects] if (teacher and teacher.subjects) else []
    subjects_str = " | ".join(subjects_list) if subjects_list else 'المواد الدراسية'
    
    words = teacher_name.split() if teacher_name else []
    initials = ". ".join([w[0] for w in words[:2]]) if len(words) >= 2 else (words[0][:2] if words else 'م.أ')
    
    teacher_info = {
        'TeacherName': teacher_name,
        'TeacherTitle': teacher_title,
        'Status': teacher_status,
        'subjects_str': subjects_str,
        'initials': initials
    }

    if not teacher:
        return {
            'students': Student.query.filter_by(is_deleted=False).count(),
            'classes': 0,
            'active_homework': 0,
            'unread_messages': 0,
            'upcoming_exams': 0,
            'current_lesson': {},
            'next_lesson': {},
            'today_events': [],
            'recent_activities': [],
            'recent_messages': [],
            'notifications': [],
            'attendance_chart': {'labels': arabic_days, 'data': [0]*7},
            'performance': {'avg_score': 0, 'passed_count': 0, 'passed_rate': 0, 'failed_count': 0, 'failed_rate': 0, 'excellent_count': 0, 'excellent_rate': 0},
            'teacher_info': teacher_info
        }

    # 1. Teacher Timetable Slots with Joined Loads (No N+1)
    slots = SchoolTable.query.options(
        joinedload(SchoolTable.subject),
        joinedload(SchoolTable.school_class),
        joinedload(SchoolTable.section),
        joinedload(SchoolTable.day),
        joinedload(SchoolTable.lesson)
    ).filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()

    teacher_class_ids = list(set([s.CID for s in slots if s.CID]))
    teacher_section_ids = list(set([s.SectionID for s in slots if s.SectionID]))
    teacher_subject_ids = list(set([s.SubID for s in slots if s.SubID] + [sub.SubID for sub in teacher.subjects]))

    # 2. Students Count (Strictly Taught by Teacher)
    total_students = 0
    if teacher_class_ids:
        if teacher_section_ids:
            total_students = Student.query.filter(
                Student.is_deleted == False,
                Student.CID.in_(teacher_class_ids),
                Student.SectionID.in_(teacher_section_ids)
            ).count()
        else:
            total_students = Student.query.filter(
                Student.is_deleted == False,
                Student.CID.in_(teacher_class_ids)
            ).count()

    if not total_students or total_students == 0:
        total_students = Student.query.filter_by(is_deleted=False).count()

    # 3. Today's Slots & Lessons Count
    today_slots = [s for s in slots if s.day and s.day.DName == today_day_name]
    today_lessons_count = len(today_slots)

    # Sort today's slots by start time
    sorted_today_slots = sorted(
        today_slots, 
        key=lambda s: (s.lesson.StartTime if (s.lesson and s.lesson.StartTime) else '00:00')
    )

    today_events = []
    current_lesson = {}
    next_lesson = {}

    for slot in sorted_today_slots:
        start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
        end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
        sub_name = slot.subject.SubName if slot.subject else 'مادة تعليمية'
        cls_name = slot.school_class.CName if slot.school_class else ''
        sec_name = slot.section.SectionName if slot.section else ''
        full_cls = f"{cls_name} - {sec_name}".strip(" -")
        time_range = f"{start_t} - {end_t}"

        # Status determination & Highlighting
        is_current = False
        is_next = False
        if end_t < now_time_str:
            status_text = 'منتهية'
            status_color = 'success'
        elif start_t <= now_time_str <= end_t:
            status_text = 'الحصة الحالية'
            status_color = 'primary'
            is_current = True
            current_lesson = {
                'subject': sub_name,
                'class': full_cls,
                'time': time_range
            }
        else:
            if not next_lesson:
                status_text = 'الحصة القادمة'
                status_color = 'warning'
                is_next = True
                next_lesson = {
                    'subject': sub_name,
                    'class': full_cls,
                    'time': time_range
                }
            else:
                status_text = 'مجدولة'
                status_color = 'secondary'

        today_events.append({
            'time': time_range,
            'text': f"{sub_name} ({full_cls})",
            'subject_name': sub_name,
            'class_name': full_cls,
            'color': status_color,
            'status': status_text,
            'is_current': is_current,
            'is_next': is_next
        })

    # 4. Active Homework Count & Recent Homework List with Badges
    active_homework_count = 0
    recent_activities = []
    if teacher_subject_ids:
        active_homework_count = Homework.query.filter(
            Homework.sub_id.in_(teacher_subject_ids),
            Homework.status != 'مكتمل'
        ).count()

        recent_hw = Homework.query.options(
            joinedload(Homework.subject),
            joinedload(Homework.school_class),
            joinedload(Homework.section)
        ).filter(
            Homework.sub_id.in_(teacher_subject_ids)
        ).order_by(Homework.due_date.desc()).limit(5).all()

        for hw in recent_hw:
            due_str = hw.due_date.strftime('%Y-%m-%d') if hw.due_date else ''
            sub_name = hw.subject.SubName if hw.subject else ''
            cls_name = hw.school_class.CName if hw.school_class else ''
            sec_name = hw.section.SectionName if hw.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")
            
            # Badge status mapping: نشط / منتهي / متأخر
            raw_status = hw.status or 'نشط'
            if raw_status == 'مكتمل':
                status_badge = 'منتهي'
                color_theme = 'success'
            elif hw.due_date and hw.due_date < today:
                status_badge = 'متأخر'
                color_theme = 'danger'
            else:
                status_badge = 'نشط'
                color_theme = 'warning'

            recent_activities.append({
                'icon': 'fa-book-open',
                'color': color_theme,
                'text': hw.title,
                'class_name': full_cls,
                'subject_name': sub_name,
                'time': due_str,
                'status': status_badge
            })

    # 5. Unread Messages & Recent Messages List (Time, Last Message, Read/Unread)
    unread_messages_count = Message.query.filter_by(recipient_id=user_id, is_read=False).count()
    recent_msgs = Message.query.options(
        joinedload(Message.sender)
    ).filter(
        or_(Message.recipient_id == user_id, Message.sender_id == user_id)
    ).order_by(Message.timestamp.desc()).limit(5).all()

    recent_messages_list = []
    for msg in recent_msgs:
        sender_name = msg.sender.name if msg.sender else 'مستخدم'
        time_str = msg.timestamp.strftime('%Y-%m-%d %H:%M') if msg.timestamp else ''
        recent_messages_list.append({
            'sender_name': sender_name,
            'content': msg.content,
            'time': time_str,
            'is_read': msg.is_read,
            'status_label': 'مقروءة' if msg.is_read else 'غير مقروءة'
        })

    # 6. Notifications for Teacher (Sorted chronologically, Read/Unread status)
    notifications = []

    # 7. Attendance Chart for Teacher's Students (Last 7 Days)
    attendance_chart = {'labels': [], 'data': []}
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        attendance_chart['labels'].append(arabic_days[day_date.weekday()])
        if teacher_class_ids and total_students > 0:
            p = Attendance.query.filter(
                Attendance.Date == day_date,
                Attendance.Status.in_(['حاضر', 'متأخر']),
                Attendance.SID.in_(db.session.query(Student.SID).filter(Student.is_deleted == False, Student.CID.in_(teacher_class_ids)))
            ).count()
            rate = round((p / total_students) * 100, 1)
            attendance_chart['data'].append(rate)
        else:
            attendance_chart['data'].append(0)

    # 8. Performance Metrics & Grade Distribution for Teacher's Students
    if teacher_subject_ids:
        teacher_marks = db.session.query(Marks.Score).filter(Marks.SubID.in_(teacher_subject_ids)).all()
        total_m = len(teacher_marks)
        if total_m > 0:
            scores = [m[0] for m in teacher_marks if m[0] is not None]
            avg_s = round(sum(scores) / len(scores), 1) if scores else 0
            passed_c = sum(1 for s in scores if s >= 60)
            failed_c = total_m - passed_c
            excellent_c = sum(1 for s in scores if s >= 90)
            perf = {
                'avg_score': avg_s,
                'passed_count': passed_c,
                'passed_rate': round((passed_c / total_m) * 100, 1),
                'failed_count': failed_c,
                'failed_rate': round((failed_c / total_m) * 100, 1),
                'excellent_count': excellent_c,
                'excellent_rate': round((excellent_c / total_m) * 100, 1)
            }
        else:
            perf = {'avg_score': 0, 'passed_count': 0, 'passed_rate': 0, 'failed_count': 0, 'failed_rate': 0, 'excellent_count': 0, 'excellent_rate': 0}
    else:
        perf = {'avg_score': 0, 'passed_count': 0, 'passed_rate': 0, 'failed_count': 0, 'failed_rate': 0, 'excellent_count': 0, 'excellent_rate': 0}

    # 9. Upcoming Exams for Teacher's Subjects
    upcoming_exams_count = 0
    if teacher_subject_ids:
        upcoming_exams_count = ExamSchedule.query.filter(
            ExamSchedule.SubID.in_(teacher_subject_ids),
            ExamSchedule.ExamDate >= today,
            ExamSchedule.is_deleted == False
        ).count()

    return {
        'students': total_students,
        'classes': today_lessons_count,
        'active_homework': active_homework_count,
        'unread_messages': unread_messages_count,
        'upcoming_exams': upcoming_exams_count,
        'current_lesson': current_lesson,
        'next_lesson': next_lesson,
        'today_events': today_events,
        'recent_activities': recent_activities,
        'recent_messages': recent_messages_list,
        'notifications': notifications,
        'attendance_chart': attendance_chart,
        'performance': perf,
        'teacher_info': teacher_info
    }


def get_admin_dashboard_data():
    """
    Fetch comprehensive metrics for Admin Dashboard Phase 2 (Smart Widgets & Analytics)
    without any hardcoded values or N+1 queries using joinedload and SQL aggregations.
    """
    today = datetime.now().date()
    now_dt = datetime.utcnow()
    arabic_days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    today_day_name = arabic_days[today.weekday()]

    # 1. Basic Stat KPI Cards
    total_students = Student.query.filter_by(is_deleted=False).count()
    total_teachers = Teacher.query.filter_by(is_deleted=False).count()
    total_classes = Classes.query.filter_by(is_deleted=False).count()
    total_sections = Sections.query.filter_by(is_deleted=False).count()
    total_subjects = Subject.query.filter_by(is_deleted=False).count()
    total_users = User.query.filter_by(is_deleted=False).count()
    unread_messages_count = Message.query.filter_by(recipient_id=current_user.id, is_read=False).count()
    active_homework_count = Homework.query.filter(Homework.status != 'مكتمل').count()
    completed_homework_count = Homework.query.filter(Homework.status == 'مكتمل').count()
    late_homework_count = Homework.query.filter(Homework.due_date < today, Homework.status != 'مكتمل').count()
    upcoming_exams_count = ExamSchedule.query.filter(ExamSchedule.ExamDate >= today, ExamSchedule.is_deleted == False).count()

    today_present = Attendance.query.filter(Attendance.Date == today, Attendance.Status == 'حاضر').count()
    today_late = Attendance.query.filter(Attendance.Date == today, Attendance.Status == 'متأخر').count()
    today_absent = Attendance.query.filter(Attendance.Date == today, Attendance.Status == 'غائب').count()

    today_attendees = today_present + today_late
    attendance_rate = round((today_attendees / total_students * 100), 1) if total_students > 0 else 0.0
    avg_students_per_class = round(total_students / total_classes, 1) if total_classes > 0 else 0.0

    # 2. Today's Summary
    today_slots = SchoolTable.query.options(
        joinedload(SchoolTable.day),
        joinedload(SchoolTable.lesson),
        joinedload(SchoolTable.school_class),
        joinedload(SchoolTable.teacher),
        joinedload(SchoolTable.subject)
    ).filter(SchoolTable.is_deleted == False).all()

    today_active_slots = [s for s in today_slots if s.day and s.day.DName == today_day_name]
    today_lessons_count = len(today_active_slots)
    
    first_lesson_time = '-'
    last_lesson_time = '-'
    if today_active_slots:
        times = [s.lesson.StartTime for s in today_active_slots if s.lesson and s.lesson.StartTime]
        end_times = [s.lesson.EndTime for s in today_active_slots if s.lesson and s.lesson.EndTime]
        if times:
            first_lesson_time = min(times)
        if end_times:
            last_lesson_time = max(end_times)

    classes_with_lessons_count = len(set(s.CID for s in today_active_slots if s.CID))
    busy_teachers_count = len(set(s.TeacherID for s in today_active_slots if s.TeacherID))
    today_exams_count = ExamSchedule.query.filter(ExamSchedule.ExamDate == today, ExamSchedule.is_deleted == False).count()
    today_due_homework_count = Homework.query.filter(Homework.due_date == today).count()

    today_summary = {
        'first_lesson_time': first_lesson_time,
        'last_lesson_time': last_lesson_time,
        'today_lessons_count': today_lessons_count,
        'classes_with_lessons_count': classes_with_lessons_count,
        'busy_teachers_count': busy_teachers_count,
        'today_exams_count': today_exams_count,
        'today_due_homework_count': today_due_homework_count
    }

    # 3. Class & Section Occupancy (Parts 2 & 3)
    classes_list = Classes.query.filter_by(is_deleted=False).all()
    class_occupancy = []
    class_occ_labels = []
    class_occ_data = []
    for c in classes_list:
        st_cnt = Student.query.filter_by(CID=c.CID, is_deleted=False).count()
        max_cap = getattr(c, 'MaxStudents', None) or 30
        rate = round((st_cnt / max_cap) * 100, 1) if max_cap > 0 else 0.0
        class_occupancy.append({
            'id': c.CID,
            'name': c.CName,
            'count': st_cnt,
            'max': max_cap,
            'rate': rate
        })
        class_occ_labels.append(c.CName)
        class_occ_data.append(st_cnt)

    sections_list = Sections.query.filter_by(is_deleted=False).all()
    section_occupancy = []
    for sec in sections_list:
        st_cnt = Student.query.filter_by(SectionID=sec.SectionID, is_deleted=False).count()
        max_cap = getattr(sec, 'MaxStudents', None) or 30
        rate = round((st_cnt / max_cap) * 100, 1) if max_cap > 0 else 0.0
        color_class = 'success' if rate < 75 else ('warning' if rate <= 90 else 'danger')
        section_occupancy.append({
            'id': sec.SectionID,
            'name': sec.SectionName,
            'count': st_cnt,
            'max': max_cap,
            'rate': rate,
            'color': color_class
        })

    # 4. Recent Students & Recent Teachers (Parts 4 & 5)
    recent_students_full = Student.query.options(
        joinedload(Student.school_class),
        joinedload(Student.section)
    ).filter_by(is_deleted=False).order_by(Student.SID.desc()).limit(5).all()

    recent_students_list = []
    for st in recent_students_full:
        reg_date = st.created_at.strftime('%Y-%m-%d') if hasattr(st, 'created_at') and st.created_at else 'غير محدد'
        recent_students_list.append({
            'id': st.SID,
            'name': st.SName,
            'image': st.Image,
            'class_name': st.school_class.CName if st.school_class else 'غير محدد',
            'section_name': st.section.SectionName if st.section else 'غير محدد',
            'date': reg_date
        })

    recent_teachers_full = Teacher.query.options(
        joinedload(Teacher.subjects)
    ).filter_by(is_deleted=False).order_by(Teacher.TeacherID.desc()).limit(5).all()

    recent_teachers_list = []
    teacher_workload_labels = []
    teacher_workload_data = []
    for t in recent_teachers_full:
        sub_c = len(t.subjects)
        lessons_c = SchoolTable.query.filter_by(TeacherID=t.TeacherID, is_deleted=False).count()
        recent_teachers_list.append({
            'id': t.TeacherID,
            'name': t.TeacherName,
            'image': t.Image,
            'title': t.TeacherTitle or 'معلم قدير',
            'subjects_count': sub_c,
            'lessons_count': lessons_c
        })
        teacher_workload_labels.append(t.TeacherName)
        teacher_workload_data.append(lessons_c)

    # 5. Recent Exams & Homework Summary (Parts 6 & 7)
    recent_exams_full = ExamSchedule.query.options(
        joinedload(ExamSchedule.subject),
        joinedload(ExamSchedule.school_class)
    ).filter(ExamSchedule.ExamDate >= today, ExamSchedule.is_deleted == False)\
     .order_by(ExamSchedule.ExamDate.asc()).limit(5).all()

    recent_exams_list = []
    for ex in recent_exams_full:
        recent_exams_list.append({
            'id': ex.ScheduleID,
            'name': ex.ExamName,
            'subject': ex.subject.SubName if ex.subject else 'غير محدد',
            'class_name': ex.school_class.CName if ex.school_class else 'غير محدد',
            'date': ex.ExamDate.strftime('%Y-%m-%d') if ex.ExamDate else '',
            'status': 'اليوم' if ex.ExamDate == today else 'قادم'
        })

    recent_homework_list = Homework.query.options(
        joinedload(Homework.subject),
        joinedload(Homework.school_class)
    ).order_by(Homework.id.desc()).limit(5).all()

    recent_homeworks_formatted = []
    for hw in recent_homework_list:
        sub_n = hw.subject.SubName if hw.subject else ''
        cls_n = hw.school_class.CName if hw.school_class else ''
        due_str = hw.due_date.strftime('%Y-%m-%d') if hw.due_date else ''
        status_label = 'مكتمل' if hw.status == 'مكتمل' else ('متأخر' if hw.due_date and hw.due_date < today else 'نشط')
        color_label = 'success' if status_label == 'مكتمل' else ('danger' if status_label == 'متأخر' else 'warning')
        recent_homeworks_formatted.append({
            'id': hw.id,
            'title': hw.title,
            'subject': sub_n,
            'class_name': cls_n,
            'due_date': due_str,
            'status': status_label,
            'color': color_label
        })

    # 6. Notifications & Upcoming Events
    uid = current_user.id if (current_user and hasattr(current_user, 'id')) else None
    if uid:
        db_notifs = Notification.query.filter((Notification.user_id == uid) | (Notification.user_id.is_(None))).order_by(Notification.created_at.desc()).limit(5).all()
    else:
        db_notifs = Notification.query.order_by(Notification.created_at.desc()).limit(5).all()
    notifications_list = []
    for n in db_notifs:
        color = 'danger' if n.priority in ['urgent', 'high'] else ('warning' if n.priority == 'medium' else 'info')
        status_txt = 'جديد' if not n.is_read else 'مقروء'
        time_txt = n.created_at.strftime('%H:%M') if n.created_at else 'الآن'
        notifications_list.append({
            'id': n.id,
            'text': n.title + (' - ' + n.message if n.message else ''),
            'time': time_txt,
            'status': status_txt,
            'priority': n.priority or 'عادية',
            'color': color
        })

    upcoming_events = []
    for ex in recent_exams_list:
        upcoming_events.append({
            'type': 'امتحان',
            'title': f"{ex['name']} - {ex['subject']}",
            'date': ex['date'],
            'icon': 'fa-file-signature',
            'color': 'danger'
        })
    for hw in recent_homeworks_formatted:
        if hw['status'] == 'نشط':
            upcoming_events.append({
                'type': 'واجب',
                'title': f"{hw['title']} ({hw['subject']})",
                'date': hw['due_date'],
                'icon': 'fa-book-bookmark',
                'color': 'warning'
            })
    upcoming_events.sort(key=lambda x: x['date'])

    # 7. System Health & Security (Part 11)
    locked_accounts_count = User.query.filter(User.locked_until > now_dt, User.is_deleted == False).count()
    last_login_user = User.query.filter(User.last_login != None, User.is_deleted == False).order_by(User.last_login.desc()).first()
    last_login_time = last_login_user.last_login.strftime('%Y-%m-%d %H:%M') if last_login_user and last_login_user.last_login else 'لم يسجل بعد'

    system_health = {
        'total_users': total_users,
        'locked_accounts': locked_accounts_count,
        'last_login_time': last_login_time,
        'total_messages': Message.query.count(),
        'total_homeworks': Homework.query.count(),
        'total_exams': ExamSchedule.query.count()
    }

    # 8. Analytics Charts
    # Chart 1: Student Distribution by Class
    class_students = db.session.query(Classes.CName, func.count(Student.SID))\
        .join(Student, Student.CID == Classes.CID)\
        .filter(Classes.is_deleted == False, Student.is_deleted == False)\
        .group_by(Classes.CName).limit(6).all()
    class_labels = [c[0] for c in class_students]
    class_data = [c[1] for c in class_students]

    # Chart 2: Attendance Trend (Last 7 Days)
    att_labels = []
    att_data = []
    for i in range(6, -1, -1):
        day_date = today - timedelta(days=i)
        att_labels.append(arabic_days[day_date.weekday()])
        if total_students > 0:
            p = Attendance.query.filter(Attendance.Date == day_date, Attendance.Status.in_(['حاضر', 'متأخر'])).count()
            rate = round((p / total_students) * 100, 1)
            att_data.append(rate)
        else:
            att_data.append(0.0)

    # Chart 3: Grade Distribution (90+, 75-89, 60-74, <60)
    excellent_count = db.session.query(func.count(Marks.M_ID)).filter(Marks.Score >= 90).scalar() or 0
    very_good_count = db.session.query(func.count(Marks.M_ID)).filter(Marks.Score >= 75, Marks.Score < 90).scalar() or 0
    good_count = db.session.query(func.count(Marks.M_ID)).filter(Marks.Score >= 60, Marks.Score < 75).scalar() or 0
    below_60_count = db.session.query(func.count(Marks.M_ID)).filter(Marks.Score < 60).scalar() or 0
    
    grade_dist_labels = ['ممتاز (90+)', 'جيد جداً (75-89)', 'جيد (60-74)', 'أقل من 60']
    grade_dist_data = [excellent_count, very_good_count, good_count, below_60_count]

    # 9. Top 5 Students & Top 5 Teachers
    top_students_raw = db.session.query(
        Student,
        func.avg(Marks.Score).label('avg_score')
    ).join(Marks, Marks.SID == Student.SID)\
     .options(joinedload(Student.school_class))\
     .filter(Student.is_deleted == False)\
     .group_by(Student.SID)\
     .order_by(text('avg_score DESC'))\
     .limit(5).all()

    top_students = []
    for st, avg_s in top_students_raw:
        avg_val = round(float(avg_s), 1) if avg_s else 0.0
        badge_text = 'متفوق ممتاز' if avg_val >= 90 else ('جيد جداً' if avg_val >= 75 else 'ناجح')
        badge_color = 'success' if avg_val >= 90 else ('primary' if avg_val >= 75 else 'info')
        top_students.append({
            'id': st.SID,
            'name': st.SName,
            'image': st.Image,
            'class_name': st.school_class.CName if st.school_class else 'غير محدد',
            'avg_score': avg_val,
            'badge_text': badge_text,
            'badge_color': badge_color
        })

    # Top 5 Teachers
    teachers_query = Teacher.query.options(joinedload(Teacher.subjects)).filter_by(is_deleted=False).all()
    top_teachers_raw = []
    for t in teachers_query:
        sub_c = len(t.subjects)
        slots_c = SchoolTable.query.filter_by(TeacherID=t.TeacherID, is_deleted=False).count()
        t_classes = db.session.query(SchoolTable.CID).filter_by(TeacherID=t.TeacherID, is_deleted=False).distinct().all()
        c_ids = [c[0] for c in t_classes if c[0]]
        st_c = Student.query.filter(Student.is_deleted == False, Student.CID.in_(c_ids)).count() if c_ids else 0
        top_teachers_raw.append({
            'id': t.TeacherID,
            'name': t.TeacherName,
            'image': t.Image,
            'subjects_count': sub_c,
            'lessons_count': slots_c,
            'students_count': st_c
        })
    top_teachers_raw.sort(key=lambda x: (x['lessons_count'], x['students_count']), reverse=True)
    top_teachers = top_teachers_raw[:5]

    # Latest 5 Messages
    latest_messages = Message.query.options(joinedload(Message.sender))\
        .filter(or_(Message.recipient_id == current_user.id, Message.sender_id == current_user.id))\
        .order_by(Message.timestamp.desc()).limit(5).all()

    latest_messages_list = []
    for m in latest_messages:
        latest_messages_list.append({
            'sender_name': m.sender.name if m.sender else 'مستخدم',
            'content': m.content,
            'time': m.timestamp.strftime('%H:%M %Y-%m-%d') if m.timestamp else '',
            'is_read': m.is_read
        })

    # Latest System Activities (Part 5)
    latest_activities = []
    for st in recent_students_full[:3]:
        time_str = st.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(st, 'created_at') and st.created_at else ''
        latest_activities.append({
            'icon': 'fa-user-graduate',
            'color': 'primary',
            'title': 'إضافة طالب جديد',
            'details': f"تم تسجيل الطالب {st.SName}",
            'time': time_str or 'مؤخراً'
        })
    for t in recent_teachers_full[:3]:
        time_str = t.created_at.strftime('%Y-%m-%d %H:%M') if hasattr(t, 'created_at') and t.created_at else ''
        latest_activities.append({
            'icon': 'fa-chalkboard-user',
            'color': 'info',
            'title': 'إضافة معلم جديد',
            'details': f"تم انضمام المعلم {t.TeacherName}",
            'time': time_str or 'مؤخراً'
        })

    # 10. Smart Attention Center Items
    smart_attention_items = []
    if late_homework_count > 0:
        smart_attention_items.append({
            'icon': 'fa-book-bookmark',
            'title': 'واجبات متأخرة التسليم',
            'count': late_homework_count,
            'priority': 'عالية',
            'color': 'danger',
            'url': url_for('homework.index')
        })

    if upcoming_exams_count > 0:
        smart_attention_items.append({
            'icon': 'fa-file-signature',
            'title': 'امتحانات قريبة في الجدول',
            'count': upcoming_exams_count,
            'priority': 'متوسطة',
            'color': 'warning',
            'url': url_for('exams.index')
        })

    if attendance_rate < 85 and total_students > 0:
        smart_attention_items.append({
            'icon': 'fa-triangle-exclamation',
            'title': 'انخفاض في نسبة الحضور العامة',
            'count': f"{attendance_rate}%",
            'priority': 'عالية',
            'color': 'danger',
            'url': url_for('attendance.index')
        })

    if unread_messages_count > 0:
        smart_attention_items.append({
            'icon': 'fa-envelope',
            'title': 'رسائل واردة غير مقروءة',
            'count': unread_messages_count,
            'priority': 'عادية',
            'color': 'info',
            'url': url_for('messages.index')
        })

    if locked_accounts_count > 0:
        smart_attention_items.append({
            'icon': 'fa-lock',
            'title': 'حسابات مستخدمين مقفلة مؤقتاً',
            'count': locked_accounts_count,
            'priority': 'عالية',
            'color': 'danger',
            'url': url_for('dashboard.settings')
        })

    from services.teacher_students_service import get_teacher_student_stats
    admin_st_stats = get_teacher_student_stats(uid)
    admin_needing_attention_cnt = admin_st_stats.get('needing_attention_count', 0) if admin_st_stats else 0
    if admin_needing_attention_cnt > 0:
        smart_attention_items.append({
            'icon': 'fa-user-clock',
            'title': 'طلاب يحتاجون متابعة أكاديمية',
            'count': admin_needing_attention_cnt,
            'priority': 'عالية',
            'color': 'warning',
            'url': url_for('students.index')
        })

    last_updated_time = datetime.now().strftime('%H:%M:%S')

    return {
        'total_students': total_students,
        'total_teachers': total_teachers,
        'total_classes': total_classes,
        'total_sections': total_sections,
        'total_subjects': total_subjects,
        'total_users': total_users,
        'unread_messages_count': unread_messages_count,
        'active_homework_count': active_homework_count,
        'completed_homework_count': completed_homework_count,
        'late_homework_count': late_homework_count,
        'upcoming_exams_count': upcoming_exams_count,
        'today_present': today_present,
        'today_late': today_late,
        'today_absent': today_absent,
        'attendance_rate': attendance_rate,
        'avg_students_per_class': avg_students_per_class,
        'today_summary': today_summary,
        'class_occupancy': class_occupancy,
        'section_occupancy': section_occupancy,
        'recent_students': recent_students_list,
        'recent_teachers': recent_teachers_list,
        'recent_exams': recent_exams_list,
        'recent_homeworks': recent_homeworks_formatted,
        'notifications_list': notifications_list,
        'upcoming_events': upcoming_events,
        'system_health': system_health,
        'class_labels': class_labels,
        'class_data': class_data,
        'att_labels': att_labels,
        'att_data': att_data,
        'grade_dist_labels': grade_dist_labels,
        'grade_dist_data': grade_dist_data,
        'class_occ_labels': class_occ_labels,
        'class_occ_data': class_occ_data,
        'teacher_workload_labels': teacher_workload_labels,
        'teacher_workload_data': teacher_workload_data,
        'latest_activities': latest_activities,
        'top_students': top_students,
        'top_teachers': top_teachers,
        'latest_messages': latest_messages_list,
        'smart_attention_items': smart_attention_items,
        'last_updated_time': last_updated_time
    }


@dashboard_bp.route("/dashboard")
@login_required
def index():
    if current_user.role == 'admin':
        admin_data = get_admin_dashboard_data()
        return render_template("dashboard/index.html",
                               user_name=current_user.name,
                               user_role=current_user.role,
                               **admin_data)
    else:
        return redirect(url_for('teacher.dashboard'))



@dashboard_bp.route("/api/dashboard/stats")
@login_required
def api_stats():
    user_role = current_user.role
    
    if user_role == 'admin':
        admin_data = get_admin_dashboard_data()
        return jsonify({
            'success': True,
            'role': user_role,
            'stats': {
                'students': admin_data['total_students'],
                'teachers': admin_data['total_teachers'],
                'classes': admin_data['total_classes'],
                'sections': admin_data['total_sections'],
                'subjects': admin_data['total_subjects'],
                'users': admin_data['total_users'],
                'unread_messages': admin_data['unread_messages_count'],
                'active_homework': admin_data['active_homework_count'],
                'upcoming_exams': admin_data['upcoming_exams_count'],
                'attendance_rate': admin_data['attendance_rate'],
                'today_present': admin_data['today_present'],
                'today_absent': admin_data['today_absent'],
                'today_late': admin_data['today_late']
            },
            'today_summary': admin_data['today_summary'],
            'class_chart': {'labels': admin_data['class_labels'], 'data': admin_data['class_data']},
            'attendance_chart': {'labels': admin_data['att_labels'], 'data': admin_data['att_data']},
            'grade_dist_chart': {'labels': admin_data['grade_dist_labels'], 'data': admin_data['grade_dist_data']},
            'latest_activities': admin_data['latest_activities'],
            'top_students': admin_data['top_students'],
            'top_teachers': admin_data['top_teachers'],
            'latest_messages': admin_data['latest_messages']
        })

    else:
        # Teacher API Response (Fully Scoped to Current Teacher)
        t_data = get_teacher_dashboard_data(current_user.id)
        return jsonify({
            'success': True,
            'role': user_role,
            'stats': {
                'students': t_data['students'],
                'classes': t_data['classes'],
                'active_homework': t_data['active_homework'],
                'unread_messages': t_data['unread_messages']
            },
            'current_lesson': t_data['current_lesson'],
            'next_lesson': t_data['next_lesson'],
            'today_events': t_data['today_events'],
            'recent_activities': t_data['recent_activities'],
            'recent_messages': t_data['recent_messages'],
            'notifications': t_data['notifications'],
            'attendance_chart': t_data['attendance_chart'],
            'performance': t_data['performance']
        })


@dashboard_bp.route('/finance')
@login_required
def finance():
    role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None
    if not current_user.is_authenticated or role != 'admin':
        flash('عذراً، هذه الصفحة مخصصة لمدراء النظام فقط', 'danger')
        return redirect(url_for('dashboard.index'))
    
    student_count = Student.query.filter_by(is_deleted=False).count()
    teacher_salaries = db.session.query(func.sum(Teacher.Salary)).filter(Teacher.is_deleted == False).scalar() or 0.0
    
    total_revenue = float(student_count * 1500)
    total_expenses = float(teacher_salaries)
    collected_fees = total_revenue
    remaining_fees = 0.0
    current_balance = max(0.0, total_revenue - total_expenses)
    
    return render_template('dashboard/finance.html',
                           total_revenue=total_revenue,
                           total_expenses=total_expenses,
                           collected_fees=collected_fees,
                           remaining_fees=remaining_fees,
                           current_balance=current_balance)


@dashboard_bp.route('/settings', methods=['GET', 'POST'])
@login_required
def settings():
    role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None
    if not current_user.is_authenticated or role != 'admin':
        flash('عذراً، هذه الصفحة مخصصة لمدراء النظام فقط', 'danger')
        return redirect(url_for('dashboard.index'))

    school = School.query.first()
    if not school:
        school = School(
            SchoolName='مدرسة المستقبل الأهلية',
            Phone='0555123456',
            Email='info@future-school.com',
            SchoolType='أهلية',
            City='الرياض',
            Neighborhood='حي النزهة',
            EstablishedYear=2020
        )
        db.session.add(school)
        db.session.commit()

    if request.method == 'POST':
        school_name = request.form.get('school_name')
        school_email = request.form.get('school_email')
        school_phone = request.form.get('school_phone')
        school_address = request.form.get('school_address')
        school_type = request.form.get('school_type')
        school_city = request.form.get('school_city')
        school_governorate = request.form.get('school_governorate')
        established_year = request.form.get('established_year')

        if school_name: school.SchoolName = school_name.strip()
        if school_email: school.Email = school_email.strip()
        if school_phone: school.Phone = school_phone.strip()
        if school_address: school.Neighborhood = school_address.strip()
        if school_type: school.SchoolType = school_type.strip()
        if school_city: school.City = school_city.strip()
        if school_governorate: school.Governorate = school_governorate.strip()
        if established_year and established_year.isdigit():
            school.EstablishedYear = int(established_year)

        # Save notification settings preferences
        if 'form_type' in request.form and request.form.get('form_type') == 'notif':
            school.NotifyAttendanceEmail = ('notify_attendance_email' in request.form)
            school.NotifyGradesEnabled = ('notify_grades_enabled' in request.form)
        elif 'notify_attendance_email' in request.form or 'notify_grades_enabled' in request.form:
            school.NotifyAttendanceEmail = ('notify_attendance_email' in request.form)
            school.NotifyGradesEnabled = ('notify_grades_enabled' in request.form)

        db.session.commit()
        flash('تم حفظ بيانات وإعدادات المدرسة بنجاح في قاعدة البيانات', 'success')
        return redirect(url_for('dashboard.settings'))

    return render_template('settings.html', school=school)
