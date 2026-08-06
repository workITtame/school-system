import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Teacher, Classes, Subject, Sections
from services.teacher_notification_service import (
    get_notification_statistics,
    get_notifications,
    get_notification,
    mark_as_read,
    mark_all_as_read,
    archive_notification,
    delete_notification,
    bulk_mark_read,
    bulk_archive,
    bulk_delete
)

logger = logging.getLogger(__name__)

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

def _get_teacher_meta(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    return teacher, subjects, classes, sections

@notifications_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    try:
        teacher, subjects, classes, sections = _get_teacher_meta(user_id)
        stats = get_notification_statistics(user_id)
        notification_items = get_notifications(user_id)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Error loading notifications workspace: {e}")
        stats = {'total_notifications': 0, 'unread_count': 0, 'today_count': 0, 'priority_count': 0, 'academic_count': 0, 'admin_count': 0, 'last_update': '', 'smart_insights': []}
        notification_items = []
        teacher, subjects, classes, sections = None, [], [], []

    return render_template(
        'teacher/notifications.html',
        stats=stats,
        notifications=notification_items,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        today=datetime.now().strftime('%Y-%m-%d')
    )

@notifications_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    user_id = current_user.id
    search = request.args.get('search')
    category = request.args.get('category')
    priority = request.args.get('priority')
    read_status = request.args.get('read_status')
    module_filter = request.args.get('module')

    filters = {
        'category': category,
        'priority': priority,
        'read_status': read_status,
        'module': module_filter
    }

    try:
        items = get_notifications(user_id, filters=filters, search=search)
        return jsonify({'items': items})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/statistics', methods=['GET'])
@login_required
def api_statistics():
    user_id = current_user.id
    try:
        stats = get_notification_statistics(user_id)
        return jsonify(stats)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/detail/<int:notification_id>', methods=['GET'])
@login_required
def api_detail(notification_id):
    user_id = current_user.id
    try:
        item = get_notification(notification_id, user_id)
        return jsonify(item)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/read', methods=['POST'])
@login_required
def api_read():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    notification_id = payload.get('id')
    try:
        success = mark_as_read(notification_id, user_id)
        return jsonify({'success': success, 'message': 'تم تعليم الإشعار كمقروء'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/read-all', methods=['POST'])
@login_required
def api_read_all():
    user_id = current_user.id
    try:
        success = mark_all_as_read(user_id)
        return jsonify({'success': success, 'message': 'تم تحديد جميع الإشعارات كمقروءة بنجاح 🟢'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/archive', methods=['POST'])
@login_required
def api_archive():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    notification_id = payload.get('id')
    try:
        success = archive_notification(notification_id, user_id)
        return jsonify({'success': success, 'message': 'تم أرشفة الإشعار بنجاح 📁'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/delete', methods=['POST'])
@login_required
def api_delete():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    notification_id = payload.get('id')
    try:
        success = delete_notification(notification_id, user_id)
        return jsonify({'success': success, 'message': 'تم حذف الإشعار بنجاح 🗑'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/bulk', methods=['POST'])
@login_required
def api_bulk():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    action = payload.get('action')
    try:
        if action == 'read':
            bulk_mark_read(user_id)
            msg = 'تم تعليم الإشعارات المحددة كمقروءة'
        elif action == 'archive':
            bulk_archive(user_id)
            msg = 'تم أرشفة الإشعارات المحددة'
        elif action == 'delete':
            bulk_delete(user_id)
            msg = 'تم حذف الإشعارات المحددة'
        else:
            msg = 'تم تنفيذ الإجراء الجماعي بنجاح'
        return jsonify({'success': True, 'message': msg})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@notifications_bp.route('/api/mark_all_read', methods=['POST'])
@login_required
def legacy_mark_all_read():
    user_id = current_user.id
    try:
        mark_all_as_read(user_id)
        return jsonify({'success': True, 'message': 'تم تحديد جميع الإشعارات كمقروءة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
