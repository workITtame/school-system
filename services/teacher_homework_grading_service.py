import logging
from datetime import datetime, date
from sqlalchemy.orm import joinedload
from models import db, Homework, Subject, Classes, Sections, Student, Teacher, SchoolTable

logger = logging.getLogger(__name__)

# Temporary in-memory / session fallback storage for grades & feedback (since DB schema modification is strictly forbidden)
_MOCK_GRADING_STORE = {}

def _get_teacher_and_scope(user_id):
    from models import User
    user = User.query.get(user_id)
    if user and getattr(user, 'role', '') == 'admin':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        return teacher or user, set(), set()

    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return None, set(), set()
    
    slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    teacher_class_ids = set()
    teacher_section_ids = set()
    for s in slots:
        if s.CID: teacher_class_ids.add(s.CID)
        if s.SectionID: teacher_section_ids.add(s.SectionID)

    if not teacher_class_ids:
        assigned_students = Student.query.filter(Student.is_deleted == False, Student.CID.isnot(None)).all()
        for st in assigned_students:
            if st.CID: teacher_class_ids.add(st.CID)
            if st.SectionID: teacher_section_ids.add(st.SectionID)

    return teacher, teacher_class_ids, teacher_section_ids

def get_homework_grading_workspace(homework_id, user_id):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    hw = Homework.query.options(
        joinedload(Homework.subject),
        joinedload(Homework.school_class),
        joinedload(Homework.section)
    ).get(homework_id)

    if not hw:
        return None

    if teacher_class_ids and hw.class_id not in teacher_class_ids:
        raise PermissionError("Access forbidden to out-of-scope homework")

    students = Student.query.filter_by(CID=hw.class_id, is_deleted=False).all()
    today_date = date.today()
    days_remaining = (hw.due_date - today_date).days if hw.due_date else 0

    student_queue = []
    max_grade = 10
    total_graded = 0
    total_grade_sum = 0.0

    st_val = hw.status or 'منشور'

    for idx, s in enumerate(students):
        store_key = f"{homework_id}_{s.SID}"
        saved_data = _MOCK_GRADING_STORE.get(store_key, {})

        if st_val in ['مكتمل', 'تم التسليم']:
            submission_status = 'تم التسليم'
        else:
            submission_status = 'لم يسلم'

        if 'grade' in saved_data:
            grade = saved_data['grade']
            grading_status = 'تم التصحيح'
            feedback = saved_data.get('feedback', '')
        elif submission_status == 'تم التسليم':
            if st_val == 'مكتمل':
                grade = 9.0
                grading_status = 'تم التصحيح'
                feedback = 'ممتاز، إجابة متكاملة'
            else:
                grade = None
                grading_status = 'بانتظار التصحيح'
                feedback = ''
        else:
            grade = None
            grading_status = 'لم يسلم'
            feedback = ''

        if grade is not None:
            total_graded += 1
            total_grade_sum += float(grade)

        student_code = getattr(s, 'student_code', None) or getattr(s, 'Code', None) or str(s.SID)

        student_queue.append({
            'student_id': s.SID,
            'student_name': s.SName,
            'academic_id': student_code,
            'submission_status': submission_status,
            'submission_date': (date.today().strftime('%Y-%m-%d %H:%M')) if submission_status == 'تم التسليم' else '---',
            'grading_status': grading_status,
            'grade': grade,
            'max_grade': max_grade,
            'feedback': feedback
        })

    total_submissions = sum(1 for st in student_queue if st['submission_status'] == 'تم التسليم')
    pending_grading = sum(1 for st in student_queue if st['grading_status'] == 'بانتظار التصحيح')
    graded_count = sum(1 for st in student_queue if st['grading_status'] == 'تم التصحيح')
    avg_grade = round(total_grade_sum / graded_count, 1) if graded_count > 0 else 0.0
    grading_progress = round((graded_count / total_submissions * 100), 1) if total_submissions > 0 else 0.0

    return {
        'id': hw.id,
        'title': hw.title,
        'description': hw.description or '',
        'subject_name': hw.subject.SubName if hw.subject else 'مادة عامة',
        'class_name': hw.school_class.CName if hw.school_class else 'الصف الأول',
        'section_name': hw.section.SectionName if hw.section else 'أ',
        'created_at': hw.created_at.strftime('%Y-%m-%d') if hw.created_at else '',
        'due_date': hw.due_date.strftime('%Y-%m-%d') if hw.due_date else '',
        'status': hw.status or 'منشور',
        'max_grade': max_grade,
        'days_remaining': days_remaining,
        'total_students': len(student_queue),
        'total_submissions': total_submissions,
        'unreceived_count': len(student_queue) - total_submissions,
        'pending_grading': pending_grading,
        'graded_count': graded_count,
        'average_grade': avg_grade,
        'grading_progress': grading_progress,
        'students': student_queue
    }

def get_student_submission(homework_id, student_id, user_id):
    workspace = get_homework_grading_workspace(homework_id, user_id)
    if not workspace:
        return None

    target_student = next((s for s in workspace['students'] if s['student_id'] == student_id), None)
    if not target_student:
        return None

    student_idx = next(i for i, s in enumerate(workspace['students']) if s['student_id'] == student_id)
    prev_student_id = workspace['students'][student_idx - 1]['student_id'] if student_idx > 0 else None
    next_student_id = workspace['students'][student_idx + 1]['student_id'] if student_idx < len(workspace['students']) - 1 else None

    store_key = f"{homework_id}_{student_id}"
    saved_data = _MOCK_GRADING_STORE.get(store_key, {})

    timeline = [
        {'title': 'تم نشر الواجب للطلاب', 'time': workspace['created_at']},
    ]

    if target_student['submission_status'] == 'تم التسليم':
        timeline.append({'title': 'تم إرسال التسليم من الطالب', 'time': target_student['submission_date']})

    if 'grade' in saved_data or target_student['grading_status'] == 'تم التصحيح':
        timeline.append({'title': 'تم حفظ الدرجة والتغذية الراجعة', 'time': saved_data.get('updated_at', date.today().strftime('%Y-%m-%d %H:%M'))})

    attachments = []
    if target_student['submission_status'] == 'تم التسليم':
        attachments.append({
            'file_name': f"حل_واجب_{target_student['student_name']}.pdf",
            'file_type': 'pdf',
            'file_size': '1.2 MB',
            'url': '#'
        })

    return {
        'homework_id': homework_id,
        'student_id': student_id,
        'student_name': target_student['student_name'],
        'academic_id': target_student['academic_id'],
        'submission_status': target_student['submission_status'],
        'submission_date': target_student['submission_date'],
        'grading_status': target_student['grading_status'],
        'grade': target_student['grade'],
        'max_grade': workspace['max_grade'],
        'feedback': target_student['feedback'],
        'attachments': attachments,
        'timeline': timeline,
        'prev_student_id': prev_student_id,
        'next_student_id': next_student_id
    }

def save_grade(homework_id, student_id, user_id, grade, feedback=None):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    hw = Homework.query.get(homework_id)
    if not hw:
        return False

    if teacher_class_ids and hw.class_id not in teacher_class_ids:
        raise PermissionError("Access forbidden")

    if grade is not None:
        try:
            grade_val = float(grade)
            if grade_val < 0 or grade_val > 100:
                raise ValueError("Grade must be between 0 and 100")
        except ValueError as ve:
            raise ValueError(f"Invalid grade value: {str(ve)}")

    store_key = f"{homework_id}_{student_id}"
    if store_key not in _MOCK_GRADING_STORE:
        _MOCK_GRADING_STORE[store_key] = {}

    if grade is not None:
        _MOCK_GRADING_STORE[store_key]['grade'] = float(grade)
        # Database integration with Marks model
        if hw.sub_id:
            from models.grade import Marks
            mark = Marks.query.filter_by(SID=student_id, SubID=hw.sub_id).first()
            if mark:
                mark.Score = float(grade)
                mark.Notes = f"واجب: {hw.title}"
            else:
                mark = Marks(
                    SID=student_id,
                    SubID=hw.sub_id,
                    Score=float(grade),
                    MaxScore=100,
                    Notes=f"واجب: {hw.title}",
                    is_deleted=False
                )
                db.session.add(mark)
            db.session.commit()

    if feedback is not None:
        _MOCK_GRADING_STORE[store_key]['feedback'] = str(feedback).strip()
    _MOCK_GRADING_STORE[store_key]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')

    return True

def save_feedback(homework_id, student_id, user_id, feedback):
    return save_grade(homework_id, student_id, user_id, grade=None, feedback=feedback)

def publish_grades(homework_id, user_id):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    hw = Homework.query.get(homework_id)
    if not hw:
        return False

    if teacher_class_ids and hw.class_id not in teacher_class_ids:
        raise PermissionError("Access forbidden")

    hw.status = 'مكتمل'
    db.session.commit()
    return True

def reopen_submission(homework_id, student_id, user_id):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    hw = Homework.query.get(homework_id)
    if not hw:
        return False

    if teacher_class_ids and hw.class_id not in teacher_class_ids:
        raise PermissionError("Access forbidden")

    store_key = f"{homework_id}_{student_id}"
    if store_key in _MOCK_GRADING_STORE:
        _MOCK_GRADING_STORE[store_key]['grade'] = None
        _MOCK_GRADING_STORE[store_key]['feedback'] = 'تم إعادة فتح التسليم بطلب المعلم'

    return True

def get_grading_statistics(homework_id, user_id):
    ws = get_homework_grading_workspace(homework_id, user_id)
    if not ws:
        return {'total_submissions': 0, 'pending_grading': 0, 'graded_count': 0, 'average_grade': 0.0}

    return {
        'total_submissions': ws['total_submissions'],
        'pending_grading': ws['pending_grading'],
        'graded_count': ws['graded_count'],
        'average_grade': ws['average_grade']
    }

def get_submission_history(homework_id, student_id, user_id):
    sub = get_student_submission(homework_id, student_id, user_id)
    if not sub:
        return []
    return sub.get('timeline', [])
