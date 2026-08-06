from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from flask_login import login_required, current_user
from models import db, SchoolTable, Classes, Sections, Subject, Teacher, Days, Lessons, Terms, Student, Attendance, Homework, ExamSchedule, Marks
from sqlalchemy.orm import joinedload
from datetime import datetime, timedelta

timetable_bp = Blueprint('timetable', __name__, url_prefix='/timetable')

@timetable_bp.route('/')
@login_required
def index():
    if hasattr(current_user, 'role') and current_user.role == 'teacher':
        from services.teacher_timetable_service import (
            get_teacher_timetable_stats,
            get_teacher_today_schedule,
            get_teacher_weekly_schedule
        )

        stats = get_teacher_timetable_stats(current_user.id)
        today_schedule = get_teacher_today_schedule(current_user.id)
        weekly_schedule = get_teacher_weekly_schedule(current_user.id)

        return render_template('teacher/timetable.html',
                               stats=stats,
                               today_schedule=today_schedule,
                               weekly_schedule=weekly_schedule)

    # Admin Timetable View
    today = datetime.now().date()
    now_time_str = datetime.now().strftime('%H:%M')
    arabic_days = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
    today_day_name = arabic_days[today.weekday()]
    
    teacher = Teacher.query.options(joinedload(Teacher.subjects)).filter_by(user_id=current_user.id).first()
    
    if not teacher:
        teacher_name = current_user.name
        teacher_title = 'إدارة النظام'
        teacher_status = 'نشط'
        subjects_str = 'كافة المواد الدراسية'
        words = teacher_name.split()
        initials = ". ".join([w[0] for w in words[:2]]) if len(words) >= 2 else 'م.أ'
        slots = SchoolTable.query.options(
            joinedload(SchoolTable.subject),
            joinedload(SchoolTable.school_class),
            joinedload(SchoolTable.section),
            joinedload(SchoolTable.day),
            joinedload(SchoolTable.lesson)
        ).filter(SchoolTable.is_deleted == False).all()
    else:
        teacher_id = teacher.TeacherID
        teacher_name = teacher.TeacherName
        teacher_title = teacher.TeacherTitle or 'معلم أكاديمي'
        teacher_status = teacher.Status or 'نشط'
        sub_names = [s.SubName for s in teacher.subjects] if teacher.subjects else []
        subjects_str = " | ".join(sub_names) if sub_names else 'المواد الدراسية'
        words = teacher_name.split()
        initials = ". ".join([w[0] for w in words[:2]]) if len(words) >= 2 else 'م.أ'
        
        slots = SchoolTable.query.options(
            joinedload(SchoolTable.subject),
            joinedload(SchoolTable.school_class),
            joinedload(SchoolTable.section),
            joinedload(SchoolTable.day),
            joinedload(SchoolTable.lesson)
        ).filter_by(TeacherID=teacher_id, is_deleted=False).all()

    teacher_info = {
        'TeacherName': teacher_name,
        'TeacherTitle': teacher_title,
        'Status': teacher_status,
        'subjects_str': subjects_str,
        'initials': initials,
        'school_name': 'مدرسة المستقبل الأهلية',
        'term_name': 'الفصل الدراسي الثاني - 2025/2026'
    }

    teacher_class_ids = list(set([s.CID for s in slots if s.CID]))
    teacher_section_ids = list(set([s.SectionID for s in slots if s.SectionID]))
    
    total_students = Student.query.filter(Student.is_deleted == False).count()

    today_slots = [s for s in slots if s.day and s.day.DName == today_day_name]
    today_slots_sorted = sorted(
        today_slots, 
        key=lambda s: (s.lesson.StartTime if (s.lesson and s.lesson.StartTime) else '00:00')
    )
    
    today_lessons_count = len(today_slots_sorted)
    today_classes_count = len(set([s.CID for s in today_slots_sorted if s.CID]))
    
    current_lesson = {}
    next_lesson = {}
    current_slot_num = None
    current_slot_time = None
    next_slot_num = None
    next_slot_time = None
    daily_timeline = []
    finished_count = 0
    
    for idx, slot in enumerate(today_slots_sorted, start=1):
        start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
        end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
        sub_name = slot.subject.SubName if slot.subject else 'مادة تعليمية'
        cls_name = slot.school_class.CName if slot.school_class else ''
        sec_name = slot.section.SectionName if slot.section else ''
        full_cls = f"{cls_name} - {sec_name}".strip(" -")
        room_name = getattr(slot, 'RoomNo', None) or f"قاعة {200 + idx}"
        time_range = f"{start_t} - {end_t}"
        
        st_count = 30
        is_current = False
        is_next = False
        
        if end_t < now_time_str:
            status_text = 'انتهت'
            status_badge_class = 'secondary'
            finished_count += 1
        elif start_t <= now_time_str <= end_t:
            status_text = 'الحصة الحالية'
            status_badge_class = 'success'
            is_current = True
            current_slot_num = idx
            current_slot_time = time_range
            current_lesson = {
                'slot_num': idx,
                'subject': sub_name,
                'class': full_cls,
                'time': time_range,
                'room': room_name,
                'students_count': st_count,
                'attendance_rate': 90
            }
        else:
            if not next_lesson:
                status_text = 'الحصة القادمة'
                status_badge_class = 'warning'
                is_next = True
                next_slot_num = idx
                next_slot_time = time_range
                next_lesson = {
                    'slot_num': idx,
                    'subject': sub_name,
                    'class': full_cls,
                    'time': time_range,
                    'room': room_name,
                    'students_count': st_count
                }
            else:
                status_text = 'لاحقة'
                status_badge_class = 'info'
                
        daily_timeline.append({
            'num': idx,
            'subject_name': sub_name,
            'class_name': full_cls,
            'time': time_range,
            'room': room_name,
            'students_count': st_count,
            'status': status_text,
            'status_class': status_badge_class,
            'is_current': is_current,
            'is_next': is_next
        })

    if not current_lesson and today_slots_sorted:
        first_s = today_slots_sorted[0]
        start_t = first_s.lesson.StartTime if (first_s.lesson and first_s.lesson.StartTime) else '08:55'
        end_t = first_s.lesson.EndTime if (first_s.lesson and first_s.lesson.EndTime) else '09:40'
        sub_name = first_s.subject.SubName if first_s.subject else 'مادة تعليمية'
        cls_name = first_s.school_class.CName if first_s.school_class else ''
        sec_name = first_s.section.SectionName if first_s.section else ''
        current_lesson = {
            'slot_num': 1,
            'subject': sub_name,
            'class': f"{cls_name} - {sec_name}".strip(" -"),
            'time': f"{start_t} - {end_t}",
            'room': getattr(first_s, 'RoomNo', None) or 'قاعة 201',
            'students_count': total_students or 32,
            'attendance_rate': 90
        }
        current_slot_num = 1
        current_slot_time = f"{start_t} - {end_t}"

    occupancy_rate = min(100, round((today_lessons_count / 6.0) * 100)) if today_lessons_count > 0 else 0

    week_days = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']
    weekly_matrix = {}
    for day in week_days:
        weekly_matrix[day] = []
        day_slots = [s for s in slots if s.day and s.day.DName == day]
        day_slots_sorted = sorted(day_slots, key=lambda s: (s.lesson.StartTime if (s.lesson and s.lesson.StartTime) else '00:00'))
        for s in day_slots_sorted:
            sub_name = s.subject.SubName if s.subject else ''
            cls_name = s.school_class.CName if s.school_class else ''
            sec_name = s.section.SectionName if s.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")
            start_t = s.lesson.StartTime if (s.lesson and s.lesson.StartTime) else '08:00'
            room_name = getattr(s, 'RoomNo', None) or 'قاعة 201'
            weekly_matrix[day].append({
                'subject': sub_name,
                'class': full_cls,
                'time': start_t,
                'room': room_name
            })

    today_present = Attendance.query.filter(Attendance.Date == today, Attendance.Status.in_(['حاضر', 'متأخر'])).count()
    today_absent = Attendance.query.filter(Attendance.Date == today, Attendance.Status == 'غائب').count()
    total_att = today_present + today_absent
    att_rate = round((today_present / total_att * 100), 1) if total_att > 0 else 90.0
    
    kpi_data = {
        'today_lessons_count': today_lessons_count,
        'current_slot_num': current_slot_num or ('2' if today_slots_sorted else '—'),
        'current_slot_time': current_slot_time or ('08:55 - 09:40' if today_slots_sorted else '—'),
        'next_slot_num': next_slot_num or ('3' if len(today_slots_sorted) > 1 else '—'),
        'next_slot_time': next_slot_time or ('09:50 - 10:35' if len(today_slots_sorted) > 1 else '—'),
        'total_students': total_students,
        'occupancy_rate': occupancy_rate or 83,
        'taught_classes_count': today_classes_count or (len(teacher_class_ids) or 3)
    }
    
    today_summary = {
        'completed_str': f"{finished_count} من {today_lessons_count}",
        'attendance_rate': att_rate,
        'absent_count': today_absent or 3,
        'present_count': today_present or (total_students - 3 if total_students > 3 else 29)
    }

    return render_template('timetable/index.html',
                           teacher_info=teacher_info,
                           kpi=kpi_data,
                           current_lesson=current_lesson,
                           next_lesson=next_lesson,
                           daily_timeline=daily_timeline,
                           weekly_matrix=weekly_matrix,
                           week_days=week_days,
                           today_summary=today_summary,
                           today_date=today.strftime('%Y-%m-%d'),
                           today_day_name=today_day_name)

@timetable_bp.route('/api/drawer/<int:slot_id>')
@login_required
def lesson_drawer_api(slot_id):
    from services.teacher_timetable_service import get_lesson_drawer_data
    data = get_lesson_drawer_data(slot_id, current_user.id)
    if not data:
        return jsonify({'error': 'Lesson not found or access forbidden'}), 403
    return jsonify(data)
