import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from services.teacher_grading_workspace_service import (
    get_workspace,
    get_students,
    get_submission,
    save_grade,
    save_feedback,
    autosave_grade,
    autosave_feedback,
    publish_grades,
    reopen_submission,
    bulk_publish,
    bulk_feedback,
    bulk_grade,
    bulk_export,
    bulk_notify,
    get_statistics
)

logger = logging.getLogger(__name__)

grading_bp = Blueprint('grading', __name__, url_prefix='/grading')

@grading_bp.route('/workspace/<source_type>/<int:source_id>', methods=['GET'])
@login_required
def workspace(source_type, source_id):
    try:
        ws_data = get_workspace(source_type, source_id, current_user.id)
        if not ws_data:
            return jsonify({'error': 'Resource not found'}), 404
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest' or request.args.get('format') == 'json':
            return jsonify(ws_data)

        return jsonify(ws_data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Grading workspace error: {e}")
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/students', methods=['GET'])
@login_required
def api_students():
    source_type = request.args.get('source_type')
    source_id = request.args.get('source_id', type=int)
    
    if not source_type or not source_id:
        return jsonify({'error': 'source_type and source_id required'}), 400

    try:
        students = get_students(source_type, source_id, current_user.id)
        return jsonify(students)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Grading api_students error: {e}")
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/submission', methods=['GET'])
@login_required
def api_submission():
    source_type = request.args.get('source_type')
    source_id = request.args.get('source_id', type=int)
    student_id = request.args.get('student_id', type=int)

    if not source_type or not source_id or not student_id:
        return jsonify({'error': 'source_type, source_id, and student_id required'}), 400

    try:
        sub = get_submission(source_type, source_id, student_id, current_user.id)
        if not sub:
            return jsonify({'error': 'Submission not found'}), 404
        return jsonify(sub)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Grading api_submission error: {e}")
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/save', methods=['POST'])
@login_required
def api_save():
    payload = request.get_json() or {}
    source_type = payload.get('source_type')
    source_id = payload.get('source_id')
    student_id = payload.get('student_id')
    grade = payload.get('grade')
    feedback = payload.get('feedback')

    if not source_type or not source_id or not student_id:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        success = save_grade(source_type, int(source_id), int(student_id), current_user.id, grade, feedback)
        return jsonify({'success': success, 'message': 'تم حفظ الدرجة والملاحظات بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except Exception as e:
        logger.error(f"Grading api_save error: {e}")
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/autosave', methods=['POST'])
@login_required
def api_autosave():
    payload = request.get_json() or {}
    source_type = payload.get('source_type')
    source_id = payload.get('source_id')
    student_id = payload.get('student_id')
    grade = payload.get('grade')
    feedback = payload.get('feedback')

    if not source_type or not source_id or not student_id:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        success = save_grade(source_type, int(source_id), int(student_id), current_user.id, grade, feedback)
        return jsonify({'success': success, 'autosaved': True, 'timestamp': datetime.now().strftime('%H:%M:%S')})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/publish', methods=['POST'])
@login_required
def api_publish():
    payload = request.get_json() or {}
    source_type = payload.get('source_type')
    source_id = payload.get('source_id')

    if not source_type or not source_id:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        success = publish_grades(source_type, int(source_id), current_user.id)
        return jsonify({'success': success, 'message': 'تم نشر جميع الدرجات بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/reopen', methods=['POST'])
@login_required
def api_reopen():
    payload = request.get_json() or {}
    source_type = payload.get('source_type')
    source_id = payload.get('source_id')
    student_id = payload.get('student_id')

    if not source_type or not source_id or not student_id:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        success = reopen_submission(source_type, int(source_id), int(student_id), current_user.id)
        return jsonify({'success': success, 'message': 'تم إعادة فتح التسليم بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/bulk', methods=['POST'])
@login_required
def api_bulk():
    payload = request.get_json() or {}
    source_type = payload.get('source_type')
    source_id = payload.get('source_id')
    action = payload.get('action')

    if not source_type or not source_id or not action:
        return jsonify({'error': 'Missing parameters'}), 400

    try:
        if action == 'publish':
            success = bulk_publish(source_type, int(source_id), current_user.id)
        elif action == 'feedback':
            success = bulk_feedback(source_type, int(source_id), current_user.id, payload.get('feedback', 'عمل ممتاز'))
        elif action == 'grade':
            success = bulk_grade(source_type, int(source_id), current_user.id, payload.get('grade', 10))
        else:
            success = True
        return jsonify({'success': success, 'message': f'تم تنفيذ الإجراء الجماعي [{action}] بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/export', methods=['POST'])
@login_required
def api_export():
    payload = request.get_json() or {}
    source_type = payload.get('source_type')
    source_id = payload.get('source_id')

    try:
        export_data = bulk_export(source_type, int(source_id), current_user.id)
        return jsonify({'success': True, 'export': export_data})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/notify', methods=['POST'])
@login_required
def api_notify():
    payload = request.get_json() or {}
    source_type = payload.get('source_type')
    source_id = payload.get('source_id')

    try:
        success = bulk_notify(source_type, int(source_id), current_user.id)
        return jsonify({'success': success, 'message': 'تم إرسال الإشعارات الجماعية للطلاب بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@grading_bp.route('/api/statistics', methods=['GET'])
@login_required
def api_statistics():
    source_type = request.args.get('source_type')
    source_id = request.args.get('source_id', type=int)

    try:
        stats = get_statistics(source_type, source_id, current_user.id)
        return jsonify(stats)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
