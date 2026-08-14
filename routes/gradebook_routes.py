import logging
from datetime import date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Teacher, Classes, Subject, Sections, Homework, ExamSchedule
from services.teacher_gradebook_service import (
    get_gradebook_statistics,
    get_students,
    get_student_gradebook,
    export_gradebook,
    bulk_publish_results,
    bulk_recalculate,
    bulk_notify_students
)

logger = logging.getLogger(__name__)

gradebook_bp = Blueprint('gradebook', __name__, url_prefix='/gradebook')

def _get_teacher_meta(user_id):
    from models import SchoolTable, Subject, Classes, Sections, Teacher, User
    user = User.query.get(user_id) if user_id else None
    user_role = getattr(user, 'role', '').strip("'") if user else ''

    if user_role == 'admin':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        subjects = Subject.query.filter_by(is_deleted=False).all()
        classes = Classes.query.filter_by(is_deleted=False).all()
        sections = Sections.query.filter_by(is_deleted=False).all()
        return teacher, subjects, classes, sections

    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher and user:
        teacher = Teacher.query.filter_by(Email=user.username).first()

    if not teacher:
        if current_user and hasattr(current_user, 'name'):
            class FallbackTeacher:
                def __init__(self, name):
                    self.TeacherName = name
            teacher = FallbackTeacher(current_user.name)
        return teacher, [], [], []

    teacher_id = getattr(teacher, 'TeacherID', None)
    slots = SchoolTable.query.filter_by(TeacherID=teacher_id, is_deleted=False).all() if teacher_id else []
    sub_ids = {s.SubID for s in slots if s.SubID}
    cls_ids = {s.CID for s in slots if s.CID}
    sec_ids = {s.SectionID for s in slots if s.SectionID}

    if hasattr(teacher, 'subjects') and teacher.subjects:
        for s in teacher.subjects:
            if hasattr(s, 'SubID'): sub_ids.add(s.SubID)

    subjects = Subject.query.filter(Subject.SubID.in_(list(sub_ids)), Subject.is_deleted == False).all() if sub_ids else []
    classes = Classes.query.filter(Classes.CID.in_(list(cls_ids)), Classes.is_deleted == False).all() if cls_ids else []
    sections = Sections.query.filter(Sections.SectionID.in_(list(sec_ids)), Sections.is_deleted == False).all() if sec_ids else []

    return teacher, subjects, classes, sections

@gradebook_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    homework_id = request.args.get('homework_id', type=int)
    exam_id = request.args.get('exam_id', type=int)
    active_homework = None
    active_exam = None

    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    subject_id = request.args.get('subject_id', type=int)

    if homework_id:
        active_homework = db.session.get(Homework, homework_id)
        if active_homework:
            if not class_id and active_homework.class_id:
                class_id = active_homework.class_id
            if not section_id and active_homework.section_id:
                section_id = active_homework.section_id
            if not subject_id and active_homework.sub_id:
                subject_id = active_homework.sub_id
    elif exam_id:
        active_exam = db.session.get(ExamSchedule, exam_id)
        if active_exam:
            if not class_id and active_exam.CID:
                class_id = active_exam.CID
            if not section_id and active_exam.SectionID:
                section_id = active_exam.SectionID
            if not subject_id and active_exam.SubID:
                subject_id = active_exam.SubID

    per_page_val = 100 if (homework_id or exam_id) else 10

    try:
        teacher, subjects, classes, sections = _get_teacher_meta(user_id)
        kpi_stats = get_gradebook_statistics(user_id, subject_id=subject_id, class_id=class_id, section_id=section_id)
        students_data = get_students(
            user_id, 
            subject_id=subject_id, 
            class_id=class_id, 
            section_id=section_id, 
            homework_id=homework_id, 
            exam_id=exam_id,
            page=1, 
            per_page=per_page_val
        )
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Error loading gradebook: {e}")
        kpi_stats = {'total_students': 0, 'class_average': 0.0, 'highest_grade': 0.0, 'lowest_grade': 0.0, 'pass_rate': 0.0, 'needs_followup_count': 0}
        students_data = {'items': [], 'total': 0, 'page': 1, 'per_page': per_page_val, 'total_pages': 1}
    view_type = request.args.get('view_type', '').lower()

    if homework_id or view_type == 'homework':
        gradebook_mode = 'homework'
    elif exam_id or view_type == 'exam':
        gradebook_mode = 'exam'
    else:
        gradebook_mode = 'general'

    return render_template(
        'teacher/grades.html',
        gradebook_mode=gradebook_mode,
        view_type=view_type,
        kpi=kpi_stats,
        students=students_data['items'],
        pagination=students_data,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        active_homework=active_homework,
        active_exam=active_exam,
        selected_homework_id=homework_id,
        selected_exam_id=exam_id,
        selected_class_id=class_id,
        selected_section_id=section_id,
        selected_subject_id=subject_id,
        today=date.today().strftime('%Y-%m-%d')
    )

@gradebook_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    user_id = current_user.id
    subject_id = request.args.get('subject_id', type=int)
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    homework_id = request.args.get('homework_id', type=int)
    exam_id = request.args.get('exam_id', type=int)
    term = request.args.get('term')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page_val = 100 if (homework_id or exam_id) else 10

    try:
        data = get_students(
            user_id=user_id,
            subject_id=subject_id,
            class_id=class_id,
            section_id=section_id,
            homework_id=homework_id,
            exam_id=exam_id,
            term=term,
            search=search,
            page=page,
            per_page=per_page_val
        )
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Gradebook api_list error: {e}")
        return jsonify({'error': str(e)}), 500

@gradebook_bp.route('/api/homework/save', methods=['POST'])
@login_required
def api_save_homework_grade():
    user_id = current_user.id
    data = request.get_json() or {}
    homework_id = data.get('homework_id')
    student_id = data.get('student_id')
    score = data.get('score')
    notes = data.get('notes', '')

    if not homework_id or not student_id:
        return jsonify({'success': False, 'error': 'المعاملات المطلوبة مفقودة'}), 400

    from services.teacher_homework_grading_service import save_grade as save_hw_grade
    res = save_hw_grade(homework_id, student_id, user_id, score, notes)
    if res:
        return jsonify({'success': True, 'message': 'تم حفظ الدرجة والملاحظات بنجاح في HomeworkMarks'})
    return jsonify({'success': False, 'error': 'فشل حفظ الدرجة في قاعدة البيانات'}), 500

@gradebook_bp.route('/api/exam/save', methods=['POST'])
@login_required
def api_save_exam_grade():
    user_id = current_user.id
    data = request.get_json() or {}
    exam_id = data.get('exam_id')
    student_id = data.get('student_id')
    score = data.get('score')
    notes = data.get('notes', '')

    if not exam_id or not student_id:
        return jsonify({'success': False, 'error': 'المعاملات المطلوبة مفقودة'}), 400

    from services.teacher_grading_workspace_service import save_grade as save_workspace_grade
    res = save_workspace_grade('exam', exam_id, student_id, user_id, score, notes)
    if res:
        return jsonify({'success': True, 'message': 'تم حفظ درجة الاختبار والملاحظات بنجاح في Marks'})
    return jsonify({'success': False, 'error': 'فشل حفظ الدرجة في قاعدة البيانات'}), 500

@gradebook_bp.route('/api/student/<int:student_id>', methods=['GET'])
@login_required
def api_student_detail(student_id):
    user_id = current_user.id
    try:
        data = get_student_gradebook(student_id, user_id)
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Gradebook api_student_detail error: {e}")
        return jsonify({'error': str(e)}), 500

@gradebook_bp.route('/api/statistics', methods=['GET'])
@login_required
def api_statistics():
    user_id = current_user.id
    subject_id = request.args.get('subject_id', type=int)
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)

    try:
        stats = get_gradebook_statistics(user_id, subject_id, class_id, section_id)
        students_data = get_students(user_id, subject_id, class_id, section_id, page=1, per_page=1000)
        items = students_data.get('items', [])
        
        c_excellent = sum(1 for s in items if isinstance(s.get('final_grade'), (int, float)) and s['final_grade'] >= 90.0)
        c_very_good = sum(1 for s in items if isinstance(s.get('final_grade'), (int, float)) and 80.0 <= s['final_grade'] < 90.0)
        c_good = sum(1 for s in items if isinstance(s.get('final_grade'), (int, float)) and 70.0 <= s['final_grade'] < 80.0)
        c_attention = sum(1 for s in items if isinstance(s.get('final_grade'), (int, float)) and 60.0 <= s['final_grade'] < 70.0)
        c_struggling = sum(1 for s in items if isinstance(s.get('final_grade'), (int, float)) and s['final_grade'] < 60.0)

        stats['distribution'] = [
            {'label': '🟢 ممتاز (90-100%)', 'count': c_excellent},
            {'label': '🟢 جيد جداً (80-89%)', 'count': c_very_good},
            {'label': '🟡 جيد (70-79%)', 'count': c_good},
            {'label': '🟠 يحتاج متابعة (60-69%)', 'count': c_attention},
            {'label': '🔴 متعثر (<60%)', 'count': c_struggling}
        ]
        return jsonify(stats)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Gradebook api_statistics error: {e}")
        return jsonify({'error': str(e)}), 500

@gradebook_bp.route('/api/export', methods=['POST'])
@login_required
def api_export():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    fmt = payload.get('format', 'csv')

    try:
        exp = export_gradebook(user_id, fmt)
        return jsonify({'success': True, 'export': exp})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gradebook_bp.route('/api/recalculate', methods=['POST'])
@login_required
def api_recalculate():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    try:
        success = bulk_recalculate(user_id, payload.get('subject_id'), payload.get('class_id'), payload.get('section_id'))
        return jsonify({'success': success, 'message': 'تم إعادة احتساب جميع المعدلات والترتيب الأكاديمي بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gradebook_bp.route('/api/publish', methods=['POST'])
@login_required
def api_publish():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    try:
        success = bulk_publish_results(user_id, payload.get('subject_id'), payload.get('class_id'), payload.get('section_id'))
        return jsonify({'success': success, 'message': 'تم نشر سجل النتائج للطلاب بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@gradebook_bp.route('/api/notify', methods=['POST'])
@login_required
def api_notify():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    msg = payload.get('message', 'تم تحديث سجل الدرجات والأداء الأكاديمي')
    try:
        success = bulk_notify_students(user_id, payload.get('subject_id'), payload.get('class_id'), payload.get('section_id'), msg)
        return jsonify({'success': success, 'message': 'تم إرسال الإشعارات الأكاديمية بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
