import logging
from datetime import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload
from models import db, Student, Teacher, Classes, Sections, Subject, Attendance
from models.timetable import SchoolTable
from services.teacher_dashboard_service import get_teacher_by_user_id

logger = logging.getLogger(__name__)

VALID_ATTENDANCE_STATUSES = ['حاضر', 'غائب', 'متأخر', 'بعذر', 'غير مسجل']

def get_lesson_attendance(slot_id, user_id, date_str=None):
    """
    Fetch raw attendance records and statistics for a specific lesson slot.
    Verifies teacher scope (returns None if unauthorized for 403 Forbidden).
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

        # Target Date
        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = datetime.now().date()
        else:
            target_date = datetime.now().date()

        # Enrolled Students
        st_query = Student.query.filter(Student.is_deleted == False)
        if slot.CID:
            st_query = st_query.filter(Student.CID == slot.CID)
            if slot.SectionID:
                st_query = st_query.filter(or_(Student.SectionID == slot.SectionID, Student.SectionID.is_(None)))

        students = st_query.all()
        student_ids = [s.SID for s in students]

        att_map = {}
        if student_ids:
            records = Attendance.query.filter(
                Attendance.SID.in_(student_ids),
                Attendance.Date == target_date
            ).order_by(
                Attendance.updated_at.desc(), Attendance.created_at.desc(), Attendance.AttendanceID.desc()
            ).all()
            for r in records:
                if r.SID not in att_map:
                    att_map[r.SID] = r

        student_list = []
        present_cnt = 0
        absent_cnt = 0
        late_cnt = 0
        excused_cnt = 0
        unregistered_cnt = 0

        for idx, st in enumerate(students, start=1):
            st_cls = st.school_class.CName if st.school_class else cls_name
            st_sec = st.section.SectionName if st.section else sec_name
            rec = att_map.get(st.SID)
            
            if rec and rec.Status in VALID_ATTENDANCE_STATUSES:
                status = rec.Status
            else:
                status = 'غير مسجل'

            if status == 'حاضر':
                present_cnt += 1
            elif status == 'غائب':
                absent_cnt += 1
            elif status == 'متأخر':
                late_cnt += 1
            elif status == 'بعذر':
                excused_cnt += 1
            else:
                unregistered_cnt += 1

            rec_time = '—'
            rec_dt = getattr(rec, 'updated_at', None) or getattr(rec, 'created_at', None) if rec else None
            if rec and rec_dt:
                h = rec_dt.strftime('%I').lstrip('0')
                if not h: h = '12'
                m = rec_dt.strftime('%M')
                s = rec_dt.strftime('%S')
                am_pm = 'ص' if rec_dt.strftime('%p') == 'AM' else 'م'
                rec_time = f"{h}:{m}:{s} {am_pm}"

            student_list.append({
                'SID': st.SID,
                'SName': st.SName,
                'academic_id': f"#{st.SID}",
                'class_name': st_cls,
                'section_name': st_sec,
                'full_class': f"{st_cls} - {st_sec}".strip(" -"),
                'attendance_status': status,
                'time_recorded': rec_time,
                'image': st.Image or None
            })

        stats = {
            'total_students': len(student_list),
            'present_count': present_cnt,
            'absent_count': absent_cnt,
            'late_count': late_cnt,
            'excused_count': excused_cnt,
            'unregistered_count': unregistered_cnt
        }

        return {
            'slot_id': slot.SchoolTableID,
            'subject_name': sub_name,
            'class_name': cls_name,
            'section_name': sec_name,
            'full_class': full_cls,
            'start_time': start_t,
            'end_time': end_t,
            'date_str': target_date.strftime('%Y-%m-%d'),
            'stats': stats,
            'students': student_list
        }
    except Exception as e:
        logger.exception("Error in get_lesson_attendance: %s", str(e))
        return None

def save_lesson_attendance(slot_id, user_id, attendance_list, date_str=None):
    """
    Saves bulk attendance records atomically within a DB transaction.
    Verifies teacher scope.
    """
    try:
        teacher = get_teacher_by_user_id(user_id)
        if not teacher:
            return None

        slot = SchoolTable.query.get(slot_id) if slot_id else None

        if date_str:
            try:
                target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
            except ValueError:
                target_date = datetime.now().date()
        else:
            target_date = datetime.now().date()

        saved_count = 0
        now_dt = datetime.now()
        # Atomic Transaction
        with db.session.begin_nested():
            for item in attendance_list:
                sid = item.get('student_id') or item.get('SID')
                status = item.get('status') or item.get('attendance_status')
                
                if not sid or status not in VALID_ATTENDANCE_STATUSES:
                    continue

                if status == 'غير مسجل':
                    # Remove existing attendance record if present
                    Attendance.query.filter_by(SID=sid, Date=target_date).delete()
                    continue

                existing_records = Attendance.query.filter_by(SID=sid, Date=target_date).order_by(
                    Attendance.updated_at.desc(), Attendance.created_at.desc(), Attendance.AttendanceID.desc()
                ).all()

                if existing_records:
                    primary = existing_records[0]
                    primary.Status = status
                    primary.updated_at = now_dt
                    for dup in existing_records[1:]:
                        db.session.delete(dup)
                else:
                    new_att = Attendance(
                        SID=sid,
                        Date=target_date,
                        Status=status,
                        created_at=now_dt,
                        updated_at=now_dt
                    )
                    db.session.add(new_att)
                saved_count += 1

        db.session.commit()

        # Fetch updated statistics
        updated_data = get_lesson_attendance(slot_id, user_id, date_str)
        return {
            'success': True,
            'saved_count': saved_count,
            'stats': updated_data['stats'] if updated_data else {}
        }
    except Exception as e:
        db.session.rollback()
        logger.exception("Error in save_lesson_attendance: %s", str(e))
        return None
