import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Teacher, Classes, Subject, Sections
from services.admin_teacher_communication_service import (
    get_dashboard_statistics,
    get_teacher_announcements,
    get_teacher_private_messages,
    get_conversation,
    send_message,
    reply_message,
    create_request,
    get_teacher_requests,
    cancel_request,
    get_assigned_tasks,
    update_task_status,
    acknowledge_announcement,
    archive_conversation,
    mark_as_read
)

logger = logging.getLogger(__name__)

admin_teacher_bp = Blueprint('admin_teacher', __name__, url_prefix='/admin-communication')

def _get_teacher_meta(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    return teacher, subjects, classes, sections

@admin_teacher_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    try:
        teacher, subjects, classes, sections = _get_teacher_meta(user_id)
        stats = get_dashboard_statistics(user_id)
        announcements = get_teacher_announcements(user_id)
        messages = get_teacher_private_messages(user_id)
        requests_list = get_teacher_requests(user_id)
        tasks = get_assigned_tasks(user_id)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Error loading admin communication workspace: {e}")
        stats = {'new_announcements': 0, 'private_messages': 0, 'open_requests': 0, 'approved_requests': 0, 'rejected_requests': 0, 'assigned_tasks': 0, 'last_update': ''}
        announcements, messages, requests_list, tasks = [], [], [], []
        teacher, subjects, classes, sections = None, [], [], []

    return render_template(
        'teacher/admin_communication.html',
        stats=stats,
        announcements=announcements,
        messages=messages,
        requests=requests_list,
        tasks=tasks,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        today=datetime.now().strftime('%Y-%m-%d')
    )

@admin_teacher_bp.route('/api/announcements', methods=['GET'])
@login_required
def api_announcements():
    user_id = current_user.id
    search = request.args.get('search')
    priority = request.args.get('priority')
    try:
        data = get_teacher_announcements(user_id, search=search, priority=priority)
        return jsonify({'announcements': data})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/messages', methods=['GET'])
@login_required
def api_messages():
    user_id = current_user.id
    search = request.args.get('search')
    try:
        threads = get_teacher_private_messages(user_id, search=search)
        return jsonify({'messages': threads})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/conversation/<int:conversation_id>', methods=['GET'])
@login_required
def api_conversation(conversation_id):
    user_id = current_user.id
    try:
        conv = get_conversation(conversation_id, user_id)
        return jsonify(conv)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/requests', methods=['GET'])
@login_required
def api_requests():
    user_id = current_user.id
    status = request.args.get('status')
    try:
        reqs = get_teacher_requests(user_id, status=status)
        return jsonify({'requests': reqs})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/tasks', methods=['GET'])
@login_required
def api_tasks():
    user_id = current_user.id
    status = request.args.get('status')
    try:
        tasks = get_assigned_tasks(user_id, status=status)
        return jsonify({'tasks': tasks})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/send', methods=['POST'])
@login_required
def api_send():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    message_text = payload.get('message', '').strip()
    if not message_text:
        return jsonify({'error': 'Message text required'}), 400

    try:
        msg = send_message(user_id, message_text)
        return jsonify({'success': True, 'message': msg, 'info': 'تم إرسال الرسالة للإدارة بنجاح 🚀'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/reply', methods=['POST'])
@login_required
def api_reply():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    message_text = payload.get('message', '').strip()

    if not message_text:
        return jsonify({'error': 'Message text required'}), 400

    try:
        msg = reply_message(user_id, conversation_id, message_text)
        return jsonify({'success': True, 'message': msg, 'info': 'تم إرسال الرد بنجاح 🚀'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/request', methods=['POST'])
@login_required
def api_create_request():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    request_type = payload.get('request_type', 'طلب عام')
    title = payload.get('title', '').strip()
    description = payload.get('description', '').strip()

    if not title or not description:
        return jsonify({'error': 'Title and description are required'}), 400

    try:
        req_obj = create_request(user_id, request_type, title, description)
        return jsonify({'success': True, 'request': req_obj, 'message': 'تم تقديم الطلب للإدارة بنجاح 📝'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/acknowledge', methods=['POST'])
@login_required
def api_acknowledge():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    announcement_id = payload.get('id')
    try:
        success = acknowledge_announcement(announcement_id, user_id)
        return jsonify({'success': success, 'message': 'تم تأكيد الاطلاع على التعميم الإداري بنجاح 🟢'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/cancel-request', methods=['POST'])
@login_required
def api_cancel_request():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    request_id = payload.get('id')
    try:
        success = cancel_request(request_id, user_id)
        return jsonify({'success': success, 'message': 'تم إلغاء الطلب بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/task-status', methods=['POST'])
@login_required
def api_task_status():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    task_id = payload.get('id')
    status = payload.get('status', 'Completed')
    try:
        success = update_task_status(task_id, user_id, status)
        return jsonify({'success': success, 'message': 'تم تحديث حالة المهمة بنجاح 🟢'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/archive', methods=['POST'])
@login_required
def api_archive():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('id')
    try:
        success = archive_conversation(conversation_id, user_id)
        return jsonify({'success': success, 'message': 'تم أرشفة المحادثة الإدارية بنجاح 📁'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@admin_teacher_bp.route('/api/read', methods=['POST'])
@login_required
def api_read():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('id')
    try:
        success = mark_as_read(conversation_id, user_id)
        return jsonify({'success': success})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
