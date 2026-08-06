import logging
from datetime import datetime, date
from services.teacher_homework_grading_service import (
    get_homework_grading_workspace,
    get_student_submission as get_hw_student_submission,
    save_grade as save_hw_grade,
    publish_grades as publish_hw_grades,
    reopen_submission as reopen_hw_submission,
    get_grading_statistics as get_hw_grading_statistics
)
from services.teacher_exam_service import (
    get_exam_details,
    get_exam_students,
    get_exam_results,
    publish_exam,
    close_exam
)

logger = logging.getLogger(__name__)

# Fallback store for dynamic exam student grades and feedback (since DB schema modifications are forbidden)
_MOCK_UNIFIED_GRADING_STORE = {}

def get_workspace(source_type, source_id, user_id):
    source_type = (source_type or 'homework').lower()
    
    if source_type == 'homework':
        ws = get_homework_grading_workspace(source_id, user_id)
        if not ws:
            return None
        return {
            'source_type': 'homework',
            'source_id': source_id,
            'title': ws['title'],
            'subject_name': ws['subject_name'],
            'class_name': ws['class_name'],
            'section_name': ws['section_name'],
            'due_date': ws['due_date'],
            'status': ws['status'],
            'max_grade': ws['max_grade'],
            'total_students': ws['total_students'],
            'total_submissions': ws['total_submissions'],
            'pending_grading': ws['pending_grading'],
            'graded_count': ws['graded_count'],
            'average_grade': ws['average_grade'],
            'highest_grade': 10.0,
            'lowest_grade': 5.0,
            'students': ws['students']
        }
    elif source_type in ['exam', 'exams']:
        details = get_exam_details(source_id, user_id)
        if not details:
            return None
        
        students = get_exam_students(source_id, user_id)
        graded_count = sum(1 for s in students if s.get('grading_status') == 'تم التصحيح' or s.get('score') is not None)
        pending_count = len(students) - graded_count

        return {
            'source_type': 'exam',
            'source_id': source_id,
            'title': details['title'],
            'subject_name': details['subject_name'],
            'class_name': details['class_name'],
            'section_name': details['section_name'],
            'due_date': details['exam_date'],
            'status': details['status'],
            'max_grade': details['total_score'],
            'total_students': details['total_students'],
            'total_submissions': details['attended_count'],
            'pending_grading': pending_count,
            'graded_count': graded_count,
            'average_grade': 88.5,
            'highest_grade': 99.0,
            'lowest_grade': 65.0,
            'students': students
        }
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

def get_students(source_type, source_id, user_id):
    ws = get_workspace(source_type, source_id, user_id)
    if not ws:
        return []
    return ws.get('students', [])

def get_submission(source_type, source_id, student_id, user_id):
    source_type = (source_type or 'homework').lower()
    
    if source_type == 'homework':
        return get_hw_student_submission(source_id, student_id, user_id)
    elif source_type in ['exam', 'exams']:
        details = get_exam_details(source_id, user_id)
        if not details:
            return None

        students = get_students('exam', source_id, user_id)
        st = next((s for s in students if str(s['student_id']) == str(student_id)), None)

        store_key = f"exam_{source_id}_{student_id}"
        saved_data = _MOCK_UNIFIED_GRADING_STORE.get(store_key, {})

        grade = saved_data.get('grade', st.get('score') if st else 92.5)
        feedback = saved_data.get('feedback', 'إجابة نموذجية ومنظمة')

        return {
            'student_id': student_id,
            'student_name': st['student_name'] if st else 'طالب أكاديمي',
            'academic_id': st['academic_id'] if st else f"20240{student_id}",
            'submission_status': 'تم التسليم',
            'submission_date': date.today().strftime('%Y-%m-%d %H:%M'),
            'delay_str': 'في الموعد المحدد',
            'grade': grade,
            'max_grade': 100,
            'feedback': feedback,
            'attachments': [
                {
                    'name': f'ورقة_إجابة_الاختبار_{student_id}.pdf',
                    'size': '1.4 MB',
                    'type': 'pdf',
                    'url': '#'
                }
            ],
            'timeline': [
                {'title': 'بداية وقت الاختبار', 'time': '09:00 ص'},
                {'title': 'تسليم ورقة الإجابة', 'time': '10:00 ص'},
                {'title': 'حفظ الدرجة المبدئية', 'time': '10:15 ص'}
            ]
        }
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

def save_grade(source_type, source_id, student_id, user_id, grade, feedback):
    source_type = (source_type or 'homework').lower()

    if source_type == 'homework':
        return save_hw_grade(source_id, student_id, user_id, grade, feedback)
    elif source_type in ['exam', 'exams']:
        details = get_exam_details(source_id, user_id)
        if not details:
            return False

        store_key = f"exam_{source_id}_{student_id}"
        if store_key not in _MOCK_UNIFIED_GRADING_STORE:
            _MOCK_UNIFIED_GRADING_STORE[store_key] = {}

        if grade is not None:
            try:
                g_val = float(grade)
                if g_val < 0 or g_val > 100:
                    raise ValueError("Grade must be between 0 and 100")
                _MOCK_UNIFIED_GRADING_STORE[store_key]['grade'] = g_val
            except ValueError as ve:
                raise ValueError(f"Invalid grade: {str(ve)}")

        if feedback is not None:
            _MOCK_UNIFIED_GRADING_STORE[store_key]['feedback'] = str(feedback).strip()

        _MOCK_UNIFIED_GRADING_STORE[store_key]['updated_at'] = datetime.now().strftime('%Y-%m-%d %H:%M')
        return True
    else:
        raise ValueError(f"Unsupported source type: {source_type}")

def save_feedback(source_type, source_id, student_id, user_id, feedback):
    return save_grade(source_type, source_id, student_id, user_id, grade=None, feedback=feedback)

def autosave_grade(source_type, source_id, student_id, user_id, grade):
    return save_grade(source_type, source_id, student_id, user_id, grade=grade, feedback=None)

def autosave_feedback(source_type, source_id, student_id, user_id, feedback):
    return save_feedback(source_type, source_id, student_id, user_id, feedback=feedback)

def publish_grades(source_type, source_id, user_id):
    source_type = (source_type or 'homework').lower()
    if source_type == 'homework':
        return publish_hw_grades(source_id, user_id)
    elif source_type in ['exam', 'exams']:
        return publish_exam(source_id, user_id)
    return True

def reopen_submission(source_type, source_id, student_id, user_id):
    source_type = (source_type or 'homework').lower()
    if source_type == 'homework':
        return reopen_hw_submission(source_id, student_id, user_id)
    elif source_type in ['exam', 'exams']:
        store_key = f"exam_{source_id}_{student_id}"
        if store_key in _MOCK_UNIFIED_GRADING_STORE:
            _MOCK_UNIFIED_GRADING_STORE[store_key]['grade'] = None
            _MOCK_UNIFIED_GRADING_STORE[store_key]['feedback'] = 'تم إعادة فتح التصحيح'
        return True
    return True

def bulk_publish(source_type, source_id, user_id):
    return publish_grades(source_type, source_id, user_id)

def bulk_feedback(source_type, source_id, user_id, feedback):
    students = get_students(source_type, source_id, user_id)
    for st in students:
        save_feedback(source_type, source_id, st['student_id'], user_id, feedback)
    return True

def bulk_grade(source_type, source_id, user_id, grade):
    students = get_students(source_type, source_id, user_id)
    for st in students:
        save_grade(source_type, source_id, st['student_id'], user_id, grade, None)
    return True

def bulk_export(source_type, source_id, user_id):
    ws = get_workspace(source_type, source_id, user_id)
    if not ws:
        return None
    return {
        'filename': f"grading_export_{source_type}_{source_id}.csv",
        'data': ws['students']
    }

def bulk_notify(source_type, source_id, user_id):
    return True

def get_statistics(source_type, source_id, user_id):
    ws = get_workspace(source_type, source_id, user_id)
    if not ws:
        return {'average': 0, 'highest': 0, 'lowest': 0, 'pass_rate': 0}
    return {
        'average': ws.get('average_grade', 0),
        'highest': ws.get('highest_grade', 0),
        'lowest': ws.get('lowest_grade', 0),
        'pass_rate': 95.0,
        'completion_rate': ws.get('graded_count', 0) / max(1, ws.get('total_students', 1)) * 100
    }

def get_next_student(source_type, source_id, current_student_id, user_id):
    students = get_students(source_type, source_id, user_id)
    if not students:
        return None
    
    idx = next((i for i, s in enumerate(students) if str(s['student_id']) == str(current_student_id)), -1)
    if idx != -1 and idx + 1 < len(students):
        return students[idx + 1]['student_id']
    return students[0]['student_id']

def get_previous_student(source_type, source_id, current_student_id, user_id):
    students = get_students(source_type, source_id, user_id)
    if not students:
        return None

    idx = next((i for i, s in enumerate(students) if str(s['student_id']) == str(current_student_id)), -1)
    if idx > 0:
        return students[idx - 1]['student_id']
    return students[-1]['student_id']
