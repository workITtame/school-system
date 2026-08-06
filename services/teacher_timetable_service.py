import logging
from datetime import datetime, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from models import db, Student, Teacher, Classes, Sections, Subject, Attendance, ExamSchedule, Homework, User, Message, Days, Lessons
from models.timetable import SchoolTable
from models.grade import Marks
from services.teacher_dashboard_service import get_teacher_by_user_id, get_teacher_subject_and_class_ids

logger = logging.getLogger(__name__)

ARABIC_WEEKDAYS = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
ORDERED_WEEKDAYS = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']

def get_teacher_timetable_stats(user_id):
    """
    Aggregates stats for the Teacher Timetable Hero & KPI cards.
    Returns raw data dict only.
    """
    try:
        teacher = get_teacher_by_user_id(user_id)
        if not teacher:
            now_time = datetime.now()
            return {
                'today_classes_count': 0,
                'current_lesson': None,
                'upcoming_lesson': None,
                'remaining_classes_count': 0,
                'total_weekly_classes_count': 0,
                'current_day_name': 'اليوم',
                'current_date_str': now_time.strftime('%Y-%m-%d'),
                'last_update_time': now_time.strftime('%H:%M')
            }

        today = datetime.now().date()
        now_time = datetime.now()
        now_time_str = now_time.strftime('%H:%M')
        today_day_name = ARABIC_WEEKDAYS[now_time.weekday()]

        slots = SchoolTable.query.options(
            joinedload(SchoolTable.subject),
            joinedload(SchoolTable.school_class),
            joinedload(SchoolTable.section),
            joinedload(SchoolTable.day),
            joinedload(SchoolTable.lesson)
        ).filter(
            SchoolTable.TeacherID == teacher.TeacherID,
            SchoolTable.is_deleted == False
        ).all()

        total_weekly_classes_count = len(slots)

        today_slots = [s for s in slots if s.day and s.day.DName == today_day_name]
        sorted_today = sorted(
            today_slots,
            key=lambda s: (s.lesson.StartTime if (s.lesson and s.lesson.StartTime) else '00:00')
        )

        today_classes_count = len(sorted_today)
        current_lesson = None
        upcoming_lesson = None
        remaining_classes_count = 0
        has_found_next = False

        for slot in sorted_today:
            start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
            end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
            sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
            cls_name = slot.school_class.CName if slot.school_class else ''
            sec_name = slot.section.SectionName if slot.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")

            # Student count for class
            st_count = Student.query.filter_by(CID=slot.CID, is_deleted=False).count() if slot.CID else 25

            item = {
                'TableID': slot.TableID,
                'period_num': slot.lesson.LessonID if slot.lesson else 1,
                'subject_name': sub_name,
                'class_name': cls_name,
                'section_name': sec_name,
                'full_class': full_cls,
                'start_time': start_t,
                'end_time': end_t,
                'students_count': st_count
            }

            if end_t < now_time_str:
                item['status_code'] = 'ended'
            elif start_t <= now_time_str <= end_t:
                item['status_code'] = 'current'
                current_lesson = item
                remaining_classes_count += 1
            else:
                item['status_code'] = 'upcoming'
                remaining_classes_count += 1
                if not has_found_next:
                    upcoming_lesson = item
                    has_found_next = True

        return {
            'today_classes_count': today_classes_count,
            'current_lesson': current_lesson,
            'upcoming_lesson': upcoming_lesson,
            'remaining_classes_count': remaining_classes_count,
            'total_weekly_classes_count': total_weekly_classes_count,
            'current_day_name': today_day_name,
            'current_date_str': now_time.strftime('%Y-%m-%d'),
            'last_update_time': now_time.strftime('%H:%M')
        }
    except Exception as e:
        logger.exception("Error in get_teacher_timetable_stats: %s", str(e))
        now_time = datetime.now()
        return {
            'today_classes_count': 0,
            'current_lesson': None,
            'upcoming_lesson': None,
            'remaining_classes_count': 0,
            'total_weekly_classes_count': 0,
            'current_day_name': 'اليوم',
            'current_date_str': now_time.strftime('%Y-%m-%d'),
            'last_update_time': now_time.strftime('%H:%M')
        }

def get_teacher_today_schedule(user_id):
    """
    Fetch today's schedule for current teacher using joinedload.
    Returns list of slot dicts sorted by start time.
    """
    try:
        teacher = get_teacher_by_user_id(user_id)
        if not teacher:
            return []

        now_time = datetime.now()
        now_time_str = now_time.strftime('%H:%M')
        today_day_name = ARABIC_WEEKDAYS[now_time.weekday()]

        slots = SchoolTable.query.options(
            joinedload(SchoolTable.subject),
            joinedload(SchoolTable.school_class),
            joinedload(SchoolTable.section),
            joinedload(SchoolTable.day),
            joinedload(SchoolTable.lesson)
        ).filter(
            SchoolTable.TeacherID == teacher.TeacherID,
            SchoolTable.is_deleted == False
        ).all()

        today_slots = [s for s in slots if s.day and s.day.DName == today_day_name]
        sorted_today = sorted(
            today_slots,
            key=lambda s: (s.lesson.StartTime if (s.lesson and s.lesson.StartTime) else '00:00')
        )

        result = []
        for slot in sorted_today:
            start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
            end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
            sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
            cls_name = slot.school_class.CName if slot.school_class else ''
            sec_name = slot.section.SectionName if slot.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")
            st_count = Student.query.filter_by(CID=slot.CID, is_deleted=False).count() if slot.CID else 25

            if end_t < now_time_str:
                status_code = 'ended'
            elif start_t <= now_time_str <= end_t:
                status_code = 'current'
            else:
                status_code = 'upcoming'

            result.append({
                'TableID': slot.TableID,
                'period_num': slot.lesson.LessonID if slot.lesson else 1,
                'subject_name': sub_name,
                'class_name': cls_name,
                'section_name': sec_name,
                'full_class': full_cls,
                'start_time': start_t,
                'end_time': end_t,
                'status_code': status_code,
                'students_count': st_count
            })

        return result
    except Exception as e:
        logger.exception("Error in get_teacher_today_schedule: %s", str(e))
        return []

def get_teacher_weekly_schedule(user_id):
    """
    Fetch weekly schedule for teacher grouped by day name ('السبت' to 'الخميس').
    Returns dict mapping day names to sorted lists of slot dicts.
    """
    try:
        teacher = get_teacher_by_user_id(user_id)
        weekly = {day: [] for day in ORDERED_WEEKDAYS}
        if not teacher:
            return weekly

        now_time_str = datetime.now().strftime('%H:%M')

        slots = SchoolTable.query.options(
            joinedload(SchoolTable.subject),
            joinedload(SchoolTable.school_class),
            joinedload(SchoolTable.section),
            joinedload(SchoolTable.day),
            joinedload(SchoolTable.lesson)
        ).filter(
            SchoolTable.TeacherID == teacher.TeacherID,
            SchoolTable.is_deleted == False
        ).all()

        for slot in slots:
            d_name = slot.day.DName if slot.day else ''
            if d_name in weekly:
                start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
                end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
                sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
                cls_name = slot.school_class.CName if slot.school_class else ''
                sec_name = slot.section.SectionName if slot.section else ''
                full_cls = f"{cls_name} - {sec_name}".strip(" -")
                st_count = Student.query.filter_by(CID=slot.CID, is_deleted=False).count() if slot.CID else 25

                weekly[d_name].append({
                    'TableID': slot.TableID,
                    'period_num': slot.lesson.LessonID if slot.lesson else 1,
                    'subject_name': sub_name,
                    'class_name': cls_name,
                    'section_name': sec_name,
                    'full_class': full_cls,
                    'start_time': start_t,
                    'end_time': end_t,
                    'status_code': 'upcoming',
                    'students_count': st_count
                })

        # Sort slots per day by start_time
        for day in weekly:
            weekly[day] = sorted(weekly[day], key=lambda x: x['start_time'])

        return weekly
    except Exception as e:
        logger.exception("Error in get_teacher_weekly_schedule: %s", str(e))
        return {day: [] for day in ORDERED_WEEKDAYS}

def get_lesson_drawer_data(slot_id, user_id):
    """
    Fetch comprehensive lesson workspace details for Lesson Offcanvas Side Drawer.
    Verifies that slot belongs strictly to current teacher (returns None if unauthorized for 403).
    """
    try:
        teacher = get_teacher_by_user_id(user_id)
        if not teacher:
            return None

        slot = SchoolTable.query.options(
            joinedload(SchoolTable.subject),
            joinedload(SchoolTable.school_class),
            joinedload(SchoolTable.section),
            joinedload(SchoolTable.day),
            joinedload(SchoolTable.lesson)
        ).get(slot_id)

        if not slot or slot.is_deleted or slot.TeacherID != teacher.TeacherID:
            return None

        sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
        cls_name = slot.school_class.CName if slot.school_class else ''
        sec_name = slot.section.SectionName if slot.section else ''
        full_cls = f"{cls_name} - {sec_name}".strip(" -")
        start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
        end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'

        # Enrolled students for this class/section
        students = Student.query.filter_by(CID=slot.CID, is_deleted=False).all() if slot.CID else []
        student_list = [{'SID': st.SID, 'SName': st.SName} for st in students]

        # Homeworks for this subject & class
        today = datetime.now().date()
        homeworks = Homework.query.filter_by(sub_id=slot.SubID, class_id=slot.CID).order_by(Homework.due_date.asc()).limit(3).all()
        hw_list = [{'title': h.title, 'due_date': h.due_date.strftime('%Y-%m-%d') if h.due_date else ''} for h in homeworks]

        # Upcoming exams
        exams = ExamSchedule.query.filter(
            ExamSchedule.SubID == slot.SubID,
            ExamSchedule.CID == slot.CID,
            ExamSchedule.is_deleted == False,
            ExamSchedule.ExamDate >= today
        ).order_by(ExamSchedule.ExamDate.asc()).limit(3).all()
        ex_list = [{'title': e.ExamName or f"اختبار {sub_name}", 'exam_date': e.ExamDate.strftime('%Y-%m-%d') if e.ExamDate else ''} for e in exams]

        return {
            'slot_id': slot.TableID,
            'subject_name': sub_name,
            'class_name': cls_name,
            'section_name': sec_name,
            'full_class': full_cls,
            'start_time': start_t,
            'end_time': end_t,
            'total_students': len(student_list) or 25,
            'present_count': len(student_list) or 25,
            'absent_count': 0,
            'students': student_list[:10],
            'homeworks': hw_list,
            'exams': ex_list,
            'notes': 'يرجى مراجعة التحضير وتجهيز الوسائل التعليمية قبل البدء.'
        }
    except Exception as e:
        logger.exception("Error in get_lesson_drawer_data: %s", str(e))
        return None
