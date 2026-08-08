import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import db, Teacher, Classes, Subject, Sections, Notification, User
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
    user_role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None

    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()

    if user_role != 'teacher':
        stats = get_notification_statistics(user_id)
        notification_items = get_notifications(user_id)
        return render_template(
            'notifications.html',
            stats=stats,
            notifications=notification_items,
            subjects=subjects,
            classes=classes,
            sections=sections,
            teacher_info=None,
            today=datetime.now().strftime('%Y-%m-%d')
        )

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
        teacher = None

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

@notifications_bp.route('/api/unread_count', methods=['GET'])
@login_required
def api_unread_count():
    user_id = current_user.id
    count = Notification.query.filter_by(user_id=user_id, is_read=False).count()
    return jsonify({'unread_count': count})

@notifications_bp.route('/api/detail/<int:notification_id>', methods=['GET'])
@notifications_bp.route('/api/details/<int:notification_id>', methods=['GET'])
@login_required
def api_detail(notification_id):
    user_id = current_user.id
    notif = Notification.query.get(notification_id)
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404
    if notif.user_id != user_id:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403

    if not notif.is_read:
        notif.is_read = True
        notif.read_at = datetime.utcnow()
        db.session.commit()

    return jsonify({
        'id': notif.id,
        'title': notif.title,
        'description': notif.message,
        'action_url': notif.action_url,
        'priority': notif.priority,
        'is_read': notif.is_read,
        'created_at': notif.created_at.strftime('%Y-%m-%d %H:%M:%S') if notif.created_at else ''
    })

@notifications_bp.route('/api/read/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_read_by_id(notification_id):
    notif = Notification.query.get(notification_id)
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403

    notif.is_read = True
    notif.read_at = datetime.utcnow()
    db.session.commit()
    return jsonify({'success': True, 'is_read': True, 'message': 'تم تعليم الإشعار كمقروء'})

@notifications_bp.route('/api/unread/<int:notification_id>', methods=['POST'])
@login_required
def api_mark_unread_by_id(notification_id):
    notif = Notification.query.get(notification_id)
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403

    notif.is_read = False
    db.session.commit()
    return jsonify({'success': True, 'is_read': False, 'message': 'تم تعليم الإشعار كغير مقروء'})

@notifications_bp.route('/api/read', methods=['POST'])
@login_required
def api_read():
    user_id = current_user.id
    payload = request.get_json(silent=True) or request.form
    notification_id = payload.get('id') or payload.get('notification_id')
    if notification_id:
        try:
            nid = int(notification_id)
            notif = Notification.query.get(nid)
            if notif and notif.user_id == user_id:
                notif.is_read = True
                notif.read_at = datetime.utcnow()
                db.session.commit()
        except Exception:
            pass
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

@notifications_bp.route('/api/delete/<int:notification_id>', methods=['DELETE', 'POST'])
@login_required
def api_delete_by_id(notification_id):
    notif = Notification.query.get(notification_id)
    if not notif:
        return jsonify({'error': 'Notification not found'}), 404
    if notif.user_id != current_user.id:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403

    db.session.delete(notif)
    db.session.commit()
    return jsonify({'success': True, 'message': 'تم حذف الإشعار بنجاح'})

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

@notifications_bp.route('/api/quick', methods=['POST'])
@login_required
def api_quick_notif():
    payload = request.get_json(silent=True) or request.form
    target_id = payload.get('user_id') or payload.get('recipient_id') or current_user.id
    title = (payload.get('title') or 'إشعار سريع عاجل').strip()
    msg = (payload.get('message') or payload.get('content') or 'تنبيه سريع من إدارة المدرسة').strip()

    try:
        rec_id = int(target_id)
    except (ValueError, TypeError):
        rec_id = current_user.id

    notif = Notification(
        user_id=rec_id,
        title=title,
        message=msg,
        notification_type='admin',
        action_url='/notifications/',
        priority='urgent',
        is_read=False,
        created_at=datetime.utcnow()
    )
    db.session.add(notif)
    db.session.commit()

    return jsonify({
        'success': True,
        'notification_id': notif.id,
        'message': 'تم إرسال الإشعار السريع بنجاح'
    })
