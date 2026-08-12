import logging
from datetime import datetime, timedelta
from sqlalchemy import func, or_
from sqlalchemy.orm import joinedload
from models import db, Student, Teacher, Classes, Sections, Subject, Attendance, ExamSchedule, Homework, User, Message, Days, Lessons
from models.timetable import SchoolTable
from models.grade import Marks, HomeworkMarks
from services.teacher_dashboard_service import get_teacher_by_user_id, get_teacher_subject_and_class_ids

logger = logging.getLogger(__name__)

ARABIC_WEEKDAYS = ['الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس', 'الجمعة', 'السبت', 'الأحد']
ORDERED_WEEKDAYS = ['السبت', 'الأحد', 'الإثنين', 'الثلاثاء', 'الأربعاء', 'الخميس']

def _get_student_counts_map_for_slots(slots):
    """
    Batch fetches student count for slots accounting for both CID and SectionID using GROUP BY to prevent N+1 queries.
    Returns a dict mapping slot.SchoolTableID -> count.
    """
    if not slots:
        return {}

    cids = list(set([s.CID for s in slots if s.CID]))
    if not cids:
        return {s.SchoolTableID: 0 for s in slots}

    try:
        counts = db.session.query(
            Student.CID, Student.SectionID, func.count(Student.SID)
        ).filter(
            Student.CID.in_(cids),
            Student.is_deleted == False
        ).group_by(Student.CID, Student.SectionID).all()

        count_dict = {(cid, sec_id): cnt for cid, sec_id, cnt in counts}

        result_map = {}
        for s in slots:
            if not s.CID:
                result_map[s.SchoolTableID] = 0
                continue

            if s.SectionID is not None:
                exact_count = count_dict.get((s.CID, s.SectionID), 0)
                none_sec_count = count_dict.get((s.CID, None), 0)
                result_map[s.SchoolTableID] = exact_count + none_sec_count
            else:
                total_cid_count = sum(cnt for (cid, sec_id), cnt in count_dict.items() if cid == s.CID)
                result_map[s.SchoolTableID] = total_cid_count

        return result_map
    except Exception as e:
        logger.exception("Error fetching student counts map for slots: %s", str(e))
        return {s.SchoolTableID: 0 for s in slots}

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

        # Batch fetch student counts for slots by CID & SectionID
        student_counts_map = _get_student_counts_map_for_slots(sorted_today)

        for slot in sorted_today:
            start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
            end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
            sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
            cls_name = slot.school_class.CName if slot.school_class else ''
            sec_name = slot.section.SectionName if slot.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")

            # Student count for slot (filtered by CID and SectionID)
            st_count = student_counts_map.get(slot.SchoolTableID, 0)

            item = {
                'TableID': slot.SchoolTableID,
                'SchoolTableID': slot.SchoolTableID,
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

        # Batch fetch student counts for slots by CID & SectionID
        student_counts_map = _get_student_counts_map_for_slots(sorted_today)

        result = []
        for slot in sorted_today:
            start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
            end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
            sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
            cls_name = slot.school_class.CName if slot.school_class else ''
            sec_name = slot.section.SectionName if slot.section else ''
            full_cls = f"{cls_name} - {sec_name}".strip(" -")
            st_count = student_counts_map.get(slot.SchoolTableID, 0)

            if end_t < now_time_str:
                status_code = 'ended'
            elif start_t <= now_time_str <= end_t:
                status_code = 'current'
            else:
                status_code = 'upcoming'

            result.append({
                'TableID': slot.SchoolTableID,
                'SchoolTableID': slot.SchoolTableID,
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

        # Batch fetch student counts for all teacher slots by CID & SectionID
        student_counts_map = _get_student_counts_map_for_slots(slots)

        for slot in slots:
            d_name = slot.day.DName if slot.day else ''
            if d_name in weekly:
                start_t = slot.lesson.StartTime if (slot.lesson and slot.lesson.StartTime) else '08:00'
                end_t = slot.lesson.EndTime if (slot.lesson and slot.lesson.EndTime) else '08:45'
                sub_name = slot.subject.SubName if slot.subject else 'مادة دراسية'
                cls_name = slot.school_class.CName if slot.school_class else ''
                sec_name = slot.section.SectionName if slot.section else ''
                full_cls = f"{cls_name} - {sec_name}".strip(" -")
                st_count = student_counts_map.get(slot.SchoolTableID, 0)

                weekly[d_name].append({
                    'TableID': slot.SchoolTableID,
                    'SchoolTableID': slot.SchoolTableID,
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

        # Real Enrolled students for this class/section (filtered by is_deleted=False and valid CID)
        st_query = Student.query.filter(Student.is_deleted == False)
        if slot.CID:
            st_query = st_query.filter(Student.CID == slot.CID)
            if slot.SectionID:
                st_query = st_query.filter(or_(Student.SectionID == slot.SectionID, Student.SectionID.is_(None)))

        students = st_query.order_by(Student.SID.asc()).all()
        student_sids = [st.SID for st in students]

        # 1. Fetch real attendance for today from Attendance table
        today = datetime.now().date()
        att_by_sid = {}
        if student_sids:
            att_records = Attendance.query.filter(
                Attendance.Date == today,
                Attendance.SID.in_(student_sids),
                Attendance.is_deleted == False
            ).all()
            for att in att_records:
                att_by_sid[att.SID] = att.Status

        # 2. Fetch real latest scores for these students in this subject (slot.SubID)
        score_by_sid = {}
        if student_sids and slot.SubID:
            marks_records = Marks.query.filter(
                Marks.SID.in_(student_sids),
                Marks.SubID == slot.SubID,
                Marks.Score.isnot(None),
                Marks.is_deleted == False
            ).all()
            for m in marks_records:
                if m.Score is not None:
                    score_by_sid[m.SID] = float(m.Score)

            hm_records = HomeworkMarks.query.filter(
                HomeworkMarks.SID.in_(student_sids),
                HomeworkMarks.SubID == slot.SubID,
                HomeworkMarks.Score.isnot(None),
                HomeworkMarks.is_deleted == False
            ).all()
            for hm in hm_records:
                if hm.Score is not None:
                    score_by_sid[hm.SID] = float(hm.Score)

        student_list = []
        for st in students:
            st_cls = st.school_class.CName if st.school_class else cls_name
            st_sec = st.section.SectionName if st.section else sec_name
            att_status = att_by_sid.get(st.SID, 'غير مسجل')
            score_val = score_by_sid.get(st.SID, None)

            score_str = None
            if score_val is not None:
                score_str = f"{int(score_val)}%" if score_val == int(score_val) else f"{score_val}%"

            student_list.append({
                'SID': st.SID,
                'SName': st.SName,
                'student_id': st.SID,
                'class_name': st_cls,
                'section_name': st_sec,
                'full_class': f"{st_cls} - {st_sec}".strip(" -"),
                'attendance_status': att_status,
                'latest_score': score_str,
                'image': st.Image or None
            })

        # Homeworks & Exams
        homeworks = Homework.query.filter_by(sub_id=slot.SubID, class_id=slot.CID).order_by(Homework.due_date.asc()).limit(3).all() if slot.CID else []
        hw_list = [{'title': h.title, 'due_date': h.due_date.strftime('%Y-%m-%d') if h.due_date else ''} for h in homeworks]

        exams = ExamSchedule.query.filter(
            ExamSchedule.SubID == slot.SubID,
            ExamSchedule.is_deleted == False,
            ExamSchedule.ExamDate >= today
        ).order_by(ExamSchedule.ExamDate.asc()).limit(3).all() if slot.SubID else []
        ex_list = [{'title': e.ExamName or f"اختبار {sub_name}", 'exam_date': e.ExamDate.strftime('%Y-%m-%d') if e.ExamDate else ''} for e in exams]

        now_time_str = datetime.now().strftime('%H:%M')
        if end_t < now_time_str:
            status_code = 'ended'
        elif start_t <= now_time_str <= end_t:
            status_code = 'current'
        else:
            status_code = 'upcoming'

        present_cnt = sum(1 for s in student_list if s['attendance_status'] in ['حاضر', 'متأخر'])
        absent_cnt = sum(1 for s in student_list if s['attendance_status'] == 'غائب')
        unregistered_cnt = sum(1 for s in student_list if s['attendance_status'] == 'غير مسجل')

        return {
            'slot_id': slot.SchoolTableID,
            'subject_name': sub_name,
            'class_name': cls_name,
            'section_name': sec_name,
            'full_class': full_cls,
            'start_time': start_t,
            'end_time': end_t,
            'status_code': status_code,
            'total_students': len(student_list),
            'present_count': present_cnt,
            'absent_count': absent_cnt,
            'open_homeworks_count': len(hw_list),
            'upcoming_exams_count': len(ex_list),
            'students': student_list,
            'homeworks': hw_list,
            'exams': ex_list,
            'notes': 'يرجى مراجعة التحضير الأكاديمي وتجهيز الوسائل التعلمية قبل بدء الحصة.'
        }
    except Exception as e:
        logger.exception("Error in get_lesson_drawer_data: %s", str(e))
        return None
