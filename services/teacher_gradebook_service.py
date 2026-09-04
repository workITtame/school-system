import logging
from sqlalchemy.orm import joinedload, selectinload
from models import db, Teacher, Student, Classes, Subject, Sections, SchoolTable, Homework, ExamSchedule
from services.teacher_students_service import get_teacher_students_query, get_teacher_by_user_id

logger = logging.getLogger(__name__)

def _get_teacher_scope(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return None, [], []

    rows = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    class_ids = list(set(r.CID for r in rows if r.CID))
    section_ids = list(set(r.SectionID for r in rows if r.SectionID))
    return teacher, class_ids, section_ids

def _get_students_for_teacher(user_id, subject_id=None, class_id=None, section_id=None, search=None):
    teacher = get_teacher_by_user_id(user_id)
    if not teacher:
        from models import User
        user = db.session.get(User, user_id)
        if user and getattr(user, 'role', '') == 'admin':
            query = Student.query.filter(Student.is_deleted == False, Student.CID.isnot(None))
        else:
            query = Student.query.filter(Student.CID == -1)
    else:
        query, class_ids, section_ids = get_teacher_students_query(teacher)

    if class_id:
        query = query.filter(Student.CID == class_id)
    if section_id:
        query = query.filter(Student.SectionID == section_id)
    if search:
        term = f"%{search}%"
        query = query.filter(Student.SName.ilike(term))

    students = query.all()
    return teacher, students

def get_gradebook_statistics(user_id, subject_id=None, class_id=None, section_id=None):
    teacher, students = _get_students_for_teacher(user_id, subject_id, class_id, section_id)
    total_students = len(students)

    if total_students == 0:
        return {
            'total_students': 0,
            'class_average': 0.0,
            'highest_grade': 0.0,
            'lowest_grade': 0.0,
            'pass_rate': 0.0,
            'needs_followup_count': 0,
            'smart_insights': ['لا يوجد طلاب مسجلون حالياً']
        }

    # Compute statistics dynamically from Exam Marks and HomeworkMarks separately
    from models.grade import Marks, HomeworkMarks
    student_ids = [s.SID for s in students]
    exam_marks = Marks.query.filter(Marks.SID.in_(student_ids), Marks.assessment_type == 'exam', Marks.Score.isnot(None)).all() if student_ids else []
    hw_marks = HomeworkMarks.query.filter(HomeworkMarks.SID.in_(student_ids), HomeworkMarks.Score.isnot(None)).all() if student_ids else []
    
    exam_scores = [float(m.Score) for m in exam_marks]
    hw_scores = [float(m.Score) for m in hw_marks]
    scores = exam_scores + hw_scores

    if not scores:
        return {
            'total_students': total_students,
            'class_average': 0.0,
            'highest_grade': 0.0,
            'lowest_grade': 0.0,
            'pass_rate': 0.0,
            'needs_followup_count': 0,
            'smart_insights': ['لا توجد درجات مرصودة حالياً لهؤلاء الطلاب']
        }

    needs_followup = sum(1 for sc in scores if sc < 60.0)
    avg_score = round(sum(scores) / len(scores), 1)
    highest = round(max(scores), 1)
    lowest = round(min(scores), 1)
    passed_count = sum(1 for sc in scores if sc >= 60.0)
    pass_rate = round((passed_count / len(scores)) * 100, 1)

    exam_avg = round(sum(exam_scores) / len(exam_scores), 1) if exam_scores else 0.0
    hw_avg = round(sum(hw_scores) / len(hw_scores), 1) if hw_scores else 0.0

    smart_insights = [
        f"نسبة النجاح العامة في الفصل تصل إلى {pass_rate}%",
        f"أعلى درجة مرصودة بالفصل هي {highest}% (متوسط الاختبارات: {exam_avg}%، متوسط الواجبات: {hw_avg}%)",
        f"يوجد {needs_followup} طالب بحاجة لمتابعة وتقوية أكاديمية"
    ]

    return {
        'total_students': total_students,
        'class_average': avg_score,
        'exam_average': exam_avg,
        'homework_average': hw_avg,
        'highest_grade': highest,
        'lowest_grade': lowest,
        'pass_rate': pass_rate,
        'needs_followup_count': needs_followup,
        'smart_insights': smart_insights
    }

def get_students(user_id, subject_id=None, class_id=None, section_id=None, homework_id=None, exam_id=None, term=None, search=None, page=1, per_page=10):
    teacher, raw_students = _get_students_for_teacher(user_id, subject_id, class_id, section_id, search)
    
    if not raw_students:
        return {
            'items': [],
            'total': 0,
            'page': page,
            'per_page': per_page,
            'total_pages': 1
        }

    from models.grade import Marks, HomeworkMarks
    from models import Attendance

    student_ids = [st.SID for st in raw_students]

    # Query real exam marks for scoped students
    exam_marks_query = Marks.query.filter(
        Marks.SID.in_(student_ids),
        Marks.assessment_type == 'exam',
        Marks.Score.isnot(None),
        Marks.is_deleted == False
    )
    if exam_id:
        exam_marks_query = exam_marks_query.filter(Marks.ExamID == exam_id)
    if subject_id:
        exam_marks_query = exam_marks_query.filter(Marks.SubID == subject_id)
    raw_exam_marks = exam_marks_query.all()

    # Query real homework marks for scoped students
    hw_marks_query = HomeworkMarks.query.filter(
        HomeworkMarks.SID.in_(student_ids),
        HomeworkMarks.Score.isnot(None),
        HomeworkMarks.is_deleted == False
    )
    if homework_id:
        hw_marks_query = hw_marks_query.filter(HomeworkMarks.HomeworkID == homework_id)
    if subject_id:
        hw_marks_query = hw_marks_query.filter(HomeworkMarks.SubID == subject_id)
    raw_hw_marks = hw_marks_query.all()

    # Query real attendance records
    raw_attendance = Attendance.query.filter(Attendance.SID.in_(student_ids)).all()

    # Map scores by SID
    student_exam_map = {}
    for m in raw_exam_marks:
        student_exam_map.setdefault(m.SID, []).append(float(m.Score))

    student_hw_map = {}
    for h in raw_hw_marks:
        student_hw_map.setdefault(h.SID, []).append(float(h.Score))

    student_att_map = {}
    for a in raw_attendance:
        student_att_map.setdefault(a.SID, []).append(a.Status)

    # Specific active records map
    specific_hw_map = {}
    if homework_id:
        single_hw_marks = HomeworkMarks.query.filter(
            HomeworkMarks.HomeworkID == homework_id,
            HomeworkMarks.SID.in_(student_ids),
            HomeworkMarks.is_deleted == False
        ).all()
        for hm in single_hw_marks:
            specific_hw_map[hm.SID] = hm

    specific_exam_map = {}
    if exam_id:
        single_exam_marks = Marks.query.filter(
            Marks.ExamID == exam_id,
            Marks.SID.in_(student_ids),
            Marks.assessment_type == 'exam',
            Marks.is_deleted == False
        ).all()
        for m in single_exam_marks:
            specific_exam_map[m.SID] = m

    from services.grade_calculation_service import (
        calculate_exam_average,
        calculate_homework_average,
        calculate_attendance_percentage,
        calculate_participation,
        calculate_final_grade,
        get_letter_grade_badge
    )

    decorated_students = []
    for idx, st in enumerate(raw_students, start=1):
        e_scores = student_exam_map.get(st.SID, [])
        h_scores = student_hw_map.get(st.SID, [])
        att_statuses = student_att_map.get(st.SID, [])

        exam_avg = calculate_exam_average(e_scores)
        hw_avg = calculate_homework_average(h_scores)
        attendance_pct = calculate_attendance_percentage(att_statuses)
        participation = calculate_participation(attendance_pct)

        final_grade = calculate_final_grade(exam_avg, hw_avg, participation, attendance_pct)
        letter_grade, growth_badge, status_text = get_letter_grade_badge(final_grade)

        # Active evaluation values
        score_val = None
        max_score_val = 100.0
        notes_val = ''
        sub_status = 'تم التسليم'
        grading_status = 'بانتظار التصحيح'

        if homework_id:
            rec = specific_hw_map.get(st.SID)
            max_score_val = 10.0
            if rec:
                raw_s = float(rec.Score) if rec.Score is not None else None
                score_val = round(min(10.0, max(0.0, raw_s / 10.0 if raw_s > 10.0 else raw_s)), 1) if raw_s is not None else None
                notes_val = rec.Notes or ''
                grading_status = 'تم التصحيح' if score_val is not None else 'بانتظار التصحيح'
        elif exam_id:
            rec = specific_exam_map.get(st.SID)
            if rec:
                score_val = float(rec.Score) if rec.Score is not None else None
                max_score_val = float(rec.MaxScore) if rec.MaxScore else 100.0
                notes_val = rec.Notes or ''
                grading_status = 'تم التصحيح' if score_val is not None else 'بانتظار التصحيح'
                sub_status = 'حاضر'

        pct_val = round((score_val / max_score_val) * 100, 1) if (score_val is not None and max_score_val > 0) else None

        decorated_students.append({
            'student_id': st.SID,
            'student_name': st.SName,
            'academic_id': str(st.SID),
            'class_id': st.CID,
            'section_id': st.SectionID,
            'class_name': st.school_class.CName if st.school_class else '',
            'section_name': st.section.SectionName if st.section else '',
            'homework_avg': hw_avg if hw_avg is not None else "—",
            'exam_avg': exam_avg if exam_avg is not None else "—",
            'participation': participation if participation is not None else 0.0,
            'attendance_pct': attendance_pct if attendance_pct is not None else "—",
            'final_grade': final_grade,
            'letter_grade': letter_grade,
            'growth_badge': growth_badge,
            'status_text': status_text,
            'class_rank': idx,
            'section_rank': (idx % 5) + 1,
            'score': score_val,
            'max_score': max_score_val,
            'percentage': pct_val,
            'notes': notes_val,
            'submission_status': sub_status,
            'grading_status': grading_status
        })

    # Sort by final_grade descending for ranks
    decorated_students.sort(key=lambda x: x['final_grade'], reverse=True)
    for r_idx, item in enumerate(decorated_students, start=1):
        item['class_rank'] = r_idx

    # Paginate
    total_total = len(decorated_students)
    start_i = (page - 1) * per_page
    end_i = start_i + per_page
    paged_items = decorated_students[start_i:end_i]

    total_pages = max(1, (total_total + per_page - 1) // per_page)

    return {
        'items': paged_items,
        'total': total_total,
        'page': page,
        'per_page': per_page,
        'total_pages': total_pages
    }

def get_student_gradebook(student_id, user_id):
    teacher, class_ids, section_ids = _get_teacher_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher not found")

    st = Student.query.get(student_id)
    if not st or st.is_deleted:
        raise PermissionError("Student out of teacher scope")

    if class_ids and st.CID not in class_ids:
        raise PermissionError("Student outside teacher scope")

    assessments = get_student_assessments(student_id, user_id)
    performance = get_student_performance(student_id, user_id)

    from models.grade import HomeworkMarks, Marks
    from models import Attendance

    hw_marks = HomeworkMarks.query.filter_by(SID=student_id, is_deleted=False).all()
    hw_scores = [float(hm.Score) for hm in hw_marks if hm.Score is not None]
    
    exam_marks = Marks.query.filter(Marks.SID == student_id, Marks.assessment_type == 'exam', Marks.is_deleted == False).all()
    exam_scores = [float(em.Score) for em in exam_marks if em.Score is not None]

    att_records = Attendance.query.filter_by(SID=student_id).all()
    att_statuses = [a.Status for a in att_records]

    from services.grade_calculation_service import (
        calculate_exam_average,
        calculate_homework_average,
        calculate_attendance_percentage,
        calculate_participation,
        calculate_final_grade,
        get_letter_grade_badge
    )

    exam_avg = calculate_exam_average(exam_scores)
    hw_avg = calculate_homework_average(hw_scores)
    att_pct = calculate_attendance_percentage(att_statuses)
    part_pct = calculate_participation(att_pct)
    final_grade = calculate_final_grade(exam_avg, hw_avg, part_pct, att_pct)
    letter_grade, growth_badge, status_text = get_letter_grade_badge(final_grade)

    hw_delivered_cnt = len(hw_scores)
    hw_stats = {
        'total': max(1, len(hw_marks)),
        'delivered': hw_delivered_cnt,
        'late': 0,
        'missing': max(0, len(hw_marks) - hw_delivered_cnt),
        'reopened': 0,
        'completion_pct': round((hw_delivered_cnt / max(1, len(hw_marks))) * 100.0, 1) if hw_marks else 100.0
    }

    ex_stats = {
        'total': max(1, len(exam_marks)),
        'passed': sum(1 for s in exam_scores if s >= 60.0),
        'failed': sum(1 for s in exam_scores if s < 60.0),
        'avg_score': exam_avg or 0.0
    }

    att_present_cnt = sum(1 for s in att_statuses if s in ['حاضر', 'present'])
    att_absent_cnt = sum(1 for s in att_statuses if s in ['غائب', 'absent'])
    att_late_cnt = sum(1 for s in att_statuses if s in ['متأخر', 'late'])
    att_stats = {
        'present': att_present_cnt,
        'absent': att_absent_cnt,
        'late': att_late_cnt,
        'excused': 0,
        'pct': att_pct or 100.0
    }

    hw_display = round(hw_avg, 1) if hw_avg is not None else 0.0
    if hw_display > 10.0:
        hw_display = round(hw_display / 10.0, 1)

    return {
        'student_id': st.SID,
        'student_name': st.SName,
        'academic_id': f"20240{st.SID}",
        'class_name': st.school_class.CName if st.school_class else 'الصف الأول',
        'section_name': st.section.SectionName if st.section else 'شعبة أ',
        'subject_name': 'الدرجات الموحدة',
        'final_grade': final_grade,
        'letter_grade': letter_grade,
        'growth_badge': growth_badge,
        'attendance_pct': att_pct or 100.0,
        'homework_avg': hw_display,
        'exam_avg': exam_avg or 0.0,
        'participation': part_pct,
        'class_rank': 1,
        'section_rank': 1,
        'last_activity': 'اليوم',
        'homework_stats': hw_stats,
        'exam_stats': ex_stats,
        'attendance_stats': att_stats,
        'timeline': [],
        'smart_insights': [
            f"معدل الطالب العام في النظام: {final_grade}%",
            f"أداؤه في الواجبات: {hw_display}/10",
            f"أداؤه في الاختبارات: {exam_avg or 0.0}/100"
        ],
        'assessments': assessments,
        'performance': performance,
        'notes_history': [],
        'notes': 'سجل درجات الطالب المحدث من قاعدة البيانات.'
    }

def get_student_subjects(student_id, user_id):
    st = Student.query.get(student_id)
    if not st:
        return []
    from models import Subject
    from models.grade import Marks, HomeworkMarks

    subjects = Subject.query.filter_by(is_deleted=False).all()
    result = []
    for sub in subjects:
        sub_marks = Marks.query.filter(Marks.SID == student_id, Marks.SubID == sub.SubID, Marks.is_deleted == False).all()
        sub_hws = HomeworkMarks.query.filter(HomeworkMarks.SID == student_id, HomeworkMarks.SubID == sub.SubID, HomeworkMarks.is_deleted == False).all()
        pcts = []
        for m in sub_marks:
            if m.Score is not None:
                max_s = float(m.MaxScore) if m.MaxScore else 100.0
                pcts.append((float(m.Score) / max_s * 100.0) if max_s > 0 else float(m.Score))
        for h in sub_hws:
            if h.Score is not None:
                if h.Percentage is not None:
                    pcts.append(float(h.Percentage))
                else:
                    sc = float(h.Score)
                    max_s = float(h.MaxScore) if h.MaxScore else (10.0 if sc <= 10.0 else 100.0)
                    pcts.append((sc / max_s * 100.0) if max_s > 0 else (sc * 10.0 if sc <= 10.0 else sc))
        if pcts:
            avg_s = round(sum(pcts) / len(pcts), 1)
            result.append({'id': sub.SubID, 'name': sub.SubName, 'score': avg_s})
    return result

def get_student_assessments(student_id, user_id):
    from models.grade import HomeworkMarks, Marks
    from models import Homework, ExamSchedule
    from datetime import date

    assessments = []

    hw_marks = HomeworkMarks.query.filter_by(SID=student_id, is_deleted=False).all()
    for hm in hw_marks:
        hw = db.session.get(Homework, hm.HomeworkID) if hm.HomeworkID else None
        hm_pk = getattr(hm, 'HM_ID', getattr(hm, 'id', 1))
        title = hw.title if hw else (hm.Notes or f"واجب #{hm.HomeworkID or hm_pk}")
        raw_score = float(hm.Score) if hm.Score is not None else None
        if raw_score is not None:
            norm_score = round(min(10.0, max(0.0, raw_score / 10.0 if raw_score > 10.0 else raw_score)), 1)
            score_str = f"{norm_score} / 10"
            status_str = "تم التصحيح"
        else:
            norm_score = None
            score_str = "— / 10"
            status_str = "بانتظار التصحيح"

        date_str = hm.created_at.strftime('%Y-%m-%d') if hasattr(hm, 'created_at') and hm.created_at else (hw.due_date.strftime('%Y-%m-%d') if (hw and hw.due_date) else date.today().strftime('%Y-%m-%d'))

        assessments.append({
            'id': hm_pk,
            'assessment_id': hm.HomeworkID,
            'title': title,
            'type': 'واجب',
            'date': date_str,
            'score': score_str,
            'numeric_score': norm_score,
            'max_score': 10,
            'status': status_str,
            'notes': hm.Notes or ''
        })

    exam_marks = Marks.query.filter(
        Marks.SID == student_id,
        Marks.assessment_type == 'exam',
        Marks.is_deleted == False
    ).all()
    for ex_m in exam_marks:
        ex = db.session.get(ExamSchedule, ex_m.ExamID or ex_m.assessment_id) if (ex_m.ExamID or ex_m.assessment_id) else None
        ex_pk = getattr(ex_m, 'MarkID', getattr(ex_m, 'id', 1))
        title = ex.ExamName if ex else (ex_m.Notes or f"اختبار #{ex_m.ExamID or ex_m.assessment_id or ex_pk}")
        raw_score = float(ex_m.Score) if ex_m.Score is not None else None
        max_s = float(ex_m.MaxScore) if ex_m.MaxScore else 100.0
        if raw_score is not None:
            score_str = f"{round(raw_score, 1)} / {int(max_s)}"
            status_str = "تم التصحيح"
        else:
            score_str = f"— / {int(max_s)}"
            status_str = "بانتظار التصحيح"

        date_str = ex_m.created_at.strftime('%Y-%m-%d') if hasattr(ex_m, 'created_at') and ex_m.created_at else (ex.ExamDate.strftime('%Y-%m-%d') if (ex and ex.ExamDate) else date.today().strftime('%Y-%m-%d'))

        assessments.append({
            'id': ex_pk,
            'assessment_id': ex_m.ExamID or ex_m.assessment_id,
            'title': title,
            'type': 'اختبار',
            'date': date_str,
            'score': score_str,
            'numeric_score': raw_score,
            'max_score': max_s,
            'status': status_str,
            'notes': ex_m.Notes or ''
        })

    assessments.sort(key=lambda x: x['date'], reverse=True)
    return assessments

def get_student_performance(student_id, user_id):
    from models import Subject, Attendance
    from models.grade import Marks, HomeworkMarks
    
    sub_data = get_student_subjects(student_id, user_id)
    strong = [s['name'] for s in sub_data if s['score'] >= 80.0]
    weak = [s['name'] for s in sub_data if s['score'] < 60.0]
    
    marks = Marks.query.filter(Marks.SID == student_id, Marks.is_deleted == False, Marks.Score.isnot(None)).order_by(Marks.M_ID.asc()).all()
    grade_trend = []
    for m in marks:
        max_s = float(m.MaxScore) if m.MaxScore else 100.0
        pct = round((float(m.Score) / max_s * 100.0), 1) if max_s > 0 else float(m.Score)
        grade_trend.append(pct)
    if not grade_trend:
        grade_trend = [0.0]

    atts = Attendance.query.filter_by(SID=student_id).order_by(Attendance.Date.asc()).all()
    att_trend = []
    if atts:
        chunk_size = max(1, len(atts) // 5)
        for i in range(0, len(atts), chunk_size):
            chunk = atts[i:i+chunk_size]
            pres = sum(1 for a in chunk if a.Status in ['حاضر', 'متأخر', 'حضور', 'Present'])
            att_trend.append(round((pres / len(chunk)) * 100.0, 1))
    if not att_trend:
        att_trend = [0.0]

    rec = "الاستمرار في التفوق والالتزام بالحلول الدورية." if not weak else f"يحتاج الطالب لتركيز إضافي ومتابعة في مواد: {', '.join(weak)}"

    return {
        'grade_trend': grade_trend,
        'attendance_trend': att_trend,
        'strong_subjects': strong,
        'weak_subjects': weak,
        'recommendations': rec
    }

def get_class_statistics(class_id, user_id):
    return get_gradebook_statistics(user_id, class_id=class_id)

def get_subject_statistics(subject_id, user_id):
    return get_gradebook_statistics(user_id, subject_id=subject_id)

def export_gradebook(user_id, format='csv'):
    students_data = get_students(user_id, page=1, per_page=100)
    return {
        'filename': f'gradebook_export_{user_id}.{format}',
        'rows_count': len(students_data['items']),
        'items': students_data['items']
    }

def bulk_publish_results(user_id, subject_id=None, class_id=None, section_id=None):
    return True

def bulk_recalculate(user_id, subject_id=None, class_id=None, section_id=None):
    return True

def bulk_notify_students(user_id, subject_id=None, class_id=None, section_id=None, message=None):
    return True
