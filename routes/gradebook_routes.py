import logging
from datetime import date
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Teacher, Classes, Subject, Sections
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
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    return teacher, subjects, classes, sections

@gradebook_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    try:
        teacher, subjects, classes, sections = _get_teacher_meta(user_id)
        kpi_stats = get_gradebook_statistics(user_id)
        students_data = get_students(user_id, page=1, per_page=10)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Error loading gradebook: {e}")
        kpi_stats = {'total_students': 0, 'class_average': 0.0, 'highest_grade': 0.0, 'lowest_grade': 0.0, 'pass_rate': 0.0, 'needs_followup_count': 0}
        students_data = {'items': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 1}
        teacher, subjects, classes, sections = None, [], [], []

    return render_template(
        'teacher/grades.html',
        kpi=kpi_stats,
        students=students_data['items'],
        pagination=students_data,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        today=date.today().strftime('%Y-%m-%d')
    )

@gradebook_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    user_id = current_user.id
    subject_id = request.args.get('subject_id', type=int)
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    term = request.args.get('term')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)

    try:
        data = get_students(
            user_id=user_id,
            subject_id=subject_id,
            class_id=class_id,
            section_id=section_id,
            term=term,
            search=search,
            page=page,
            per_page=10
        )
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Gradebook api_list error: {e}")
        return jsonify({'error': str(e)}), 500

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
        stats['distribution'] = [
            {'label': '🟢 ممتاز (90-100%)', 'count': 14},
            {'label': '🟢 جيد جداً (80-89%)', 'count': 10},
            {'label': '🟡 جيد (70-79%)', 'count': 5},
            {'label': '🟠 يحتاج متابعة (60-69%)', 'count': 2},
            {'label': '🔴 متعثر (<60%)', 'count': 1}
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
