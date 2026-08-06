import logging
from datetime import date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Subject, Classes, Sections, Student, SchoolTable, Teacher
from services.teacher_exam_service import (
    get_teacher_exam_statistics,
    get_teacher_exams,
    get_exam_details,
    create_exam,
    update_exam,
    publish_exam,
    close_exam,
    duplicate_exam,
    soft_delete_exam,
    restore_exam,
    get_exam_students,
    get_exam_results,
    get_exam_statistics
)

logger = logging.getLogger(__name__)

exam_bp = Blueprint('exams', __name__, url_prefix='/exams')
exams_bp = exam_bp

def _get_teacher_subjects_classes_sections(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return [], [], []

    slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    sub_ids = {s.SubID for s in slots if s.SubID}
    cls_ids = {s.CID for s in slots if s.CID}
    sec_ids = {s.SectionID for s in slots if s.SectionID}

    if not cls_ids:
        assigned_students = Student.query.filter(Student.is_deleted == False, Student.CID.isnot(None)).all()
        for st in assigned_students:
            if st.CID: cls_ids.add(st.CID)
            if st.SectionID: sec_ids.add(st.SectionID)

    subjects = Subject.query.filter(Subject.SubID.in_(list(sub_ids))).all() if sub_ids else Subject.query.filter_by(Status='نشط').all()
    classes = Classes.query.filter(Classes.CID.in_(list(cls_ids))).all() if cls_ids else Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter(Sections.SectionID.in_(list(sec_ids))).all() if sec_ids else Sections.query.filter_by(is_deleted=False).all()

    return subjects, classes, sections

@exam_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    subject_id = request.args.get('subject_id')
    class_id = request.args.get('class_id')
    section_id = request.args.get('section_id')
    status = request.args.get('status')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)

    subjects, classes, sections = _get_teacher_subjects_classes_sections(user_id)
    kpi_stats = get_teacher_exam_statistics(user_id)

    try:
        exams_data = get_teacher_exams(
            user_id=user_id,
            subject_id=subject_id,
            class_id=class_id,
            section_id=section_id,
            status=status,
            search=search,
            page=page,
            per_page=10
        )
    except Exception as e:
        logger.error(f"Error fetching teacher exams: {e}")
        exams_data = {'items': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 1}

    teacher = Teacher.query.filter_by(user_id=user_id).first()

    return render_template(
        'teacher/exams.html',
        kpi=kpi_stats,
        exam_list=exams_data['items'],
        pagination=exams_data,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        today=date.today().strftime('%Y-%m-%d')
    )

@exam_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    user_id = current_user.id
    subject_id = request.args.get('subject_id')
    class_id = request.args.get('class_id')
    section_id = request.args.get('section_id')
    status = request.args.get('status')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)

    try:
        data = get_teacher_exams(
            user_id=user_id,
            subject_id=subject_id,
            class_id=class_id,
            section_id=section_id,
            status=status,
            search=search,
            page=page,
            per_page=10
        )
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Unauthorized teacher access'}), 403
    except Exception as e:
        logger.error(f"API List error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/details/<int:exam_id>', methods=['GET'])
@login_required
def api_details(exam_id):
    try:
        data = get_exam_details(exam_id, current_user.id)
        if not data:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Details error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/students/<int:exam_id>', methods=['GET'])
@login_required
def api_students(exam_id):
    try:
        students = get_exam_students(exam_id, current_user.id)
        return jsonify(students)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Students error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/results/<int:exam_id>', methods=['GET'])
@login_required
def api_results(exam_id):
    try:
        results = get_exam_results(exam_id, current_user.id)
        return jsonify(results)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Results error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    payload = request.get_json() or request.form
    try:
        exam_id = create_exam(current_user.id, payload)
        return jsonify({'success': True, 'id': exam_id, 'message': 'تم إنشاء الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Create error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/update/<int:exam_id>', methods=['POST'])
@login_required
def api_update(exam_id):
    payload = request.get_json() or request.form
    try:
        success = update_exam(exam_id, current_user.id, payload)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم تحديث البيانات بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Update error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/publish/<int:exam_id>', methods=['POST'])
@login_required
def api_publish(exam_id):
    try:
        success = publish_exam(exam_id, current_user.id)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم نشر الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Publish error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/close/<int:exam_id>', methods=['POST'])
@login_required
def api_close(exam_id):
    try:
        success = close_exam(exam_id, current_user.id)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم إغلاق الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Close error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/duplicate/<int:exam_id>', methods=['POST'])
@login_required
def api_duplicate(exam_id):
    try:
        dup_id = duplicate_exam(exam_id, current_user.id)
        if not dup_id:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'id': dup_id, 'message': 'تم نسخ الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Duplicate error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/restore/<int:exam_id>', methods=['POST'])
@login_required
def api_restore(exam_id):
    try:
        success = restore_exam(exam_id, current_user.id)
        return jsonify({'success': True, 'message': 'تم استعادة الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/delete/<int:exam_id>', methods=['DELETE', 'POST'])
@login_required
def api_delete(exam_id):
    try:
        success = soft_delete_exam(exam_id, current_user.id)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم حذف الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Delete error: {e}")
        return jsonify({'error': str(e)}), 500
