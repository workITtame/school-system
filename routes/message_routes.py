import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Teacher, Classes, Subject, Sections
from services.teacher_message_service import (
    get_teacher_message_statistics,
    get_conversations,
    get_conversation,
    create_conversation,
    send_message,
    mark_as_read,
    archive_conversation,
    delete_conversation,
    bulk_send,
    get_student_profile,
    get_student_recent_activity,
    get_student_notifications,
    get_message_templates,
    pin_conversation,
    schedule_message
)

logger = logging.getLogger(__name__)

messages_bp = Blueprint('messages', __name__, url_prefix='/messages')

def _get_teacher_meta(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    return teacher, subjects, classes, sections

@messages_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    try:
        teacher, subjects, classes, sections = _get_teacher_meta(user_id)
        kpi_stats = get_teacher_message_statistics(user_id)
        conversations = get_conversations(user_id)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Error loading messages page: {e}")
        kpi_stats = {'total_conversations': 0, 'unread_count': 0, 'sent_today': 0, 'received_today': 0, 'bulk_sent': 0, 'last_activity': ''}
        conversations = []
        teacher, subjects, classes, sections = None, [], [], []

    return render_template(
        'teacher/messages.html',
        kpi=kpi_stats,
        conversations=conversations,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        today=datetime.now().strftime('%Y-%m-%d')
    )

@messages_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    user_id = current_user.id
    search = request.args.get('search')
    filter_type = request.args.get('filter')
    sort_by = request.args.get('sort', 'newest')

    try:
        convs = get_conversations(user_id, search=search, filter_type=filter_type, sort_by=sort_by)
        return jsonify({'conversations': convs})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/conversation/<int:conversation_id>', methods=['GET'])
@login_required
def api_conversation(conversation_id):
    user_id = current_user.id
    try:
        data = get_conversation(conversation_id, user_id)
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    student_id = payload.get('student_id')
    if not student_id:
        return jsonify({'error': 'Student ID required'}), 400

    try:
        res = create_conversation(user_id, student_id)
        return jsonify({'success': True, 'conversation': res})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/send', methods=['POST'])
@login_required
def api_send():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    message_text = payload.get('message', '').strip()

    if not conversation_id or not message_text:
        return jsonify({'error': 'Conversation ID and message required'}), 400

    try:
        msg = send_message(user_id, conversation_id, message_text)
        return jsonify({'success': True, 'message': msg})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/archive', methods=['POST'])
@login_required
def api_archive():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    try:
        success = archive_conversation(user_id, conversation_id)
        return jsonify({'success': success, 'message': 'تم أرشفة المحادثة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/delete', methods=['POST'])
@login_required
def api_delete():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    try:
        success = delete_conversation(user_id, conversation_id)
        return jsonify({'success': success, 'message': 'تم حذف المحادثة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/read', methods=['POST'])
@login_required
def api_read():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    try:
        success = mark_as_read(user_id, conversation_id)
        return jsonify({'success': success})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/bulk', methods=['POST'])
@login_required
def api_bulk():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    student_ids = payload.get('student_ids', [])
    message_text = payload.get('message', '').strip()

    if not message_text:
        return jsonify({'error': 'Message text is required'}), 400

    try:
        res = bulk_send(user_id, student_ids, message_text)
        return jsonify({'success': True, 'result': res, 'message': f'تم إرسال الرسالة إلى {res.get("sent_count", 0)} طالب بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/student/<int:student_id>', methods=['GET'])
@login_required
def api_student_profile(student_id):
    user_id = current_user.id
    try:
        profile = get_student_profile(student_id, user_id)
        activity = get_student_recent_activity(student_id, user_id)
        notifications = get_student_notifications(student_id, user_id)
        return jsonify({
            'profile': profile,
            'recent_activity': activity,
            'notifications': notifications
        })
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/pin', methods=['POST'])
@login_required
def api_pin():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    try:
        success = pin_conversation(user_id, conversation_id)
        return jsonify({'success': success, 'message': 'تم تثبيت المحادثة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/schedule', methods=['POST'])
@login_required
def api_schedule():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    conversation_id = payload.get('conversation_id')
    text = payload.get('message', '').strip()
    schedule_time = payload.get('schedule_time')
    try:
        res = schedule_message(user_id, conversation_id, text, schedule_time)
        return jsonify({'success': True, 'result': res, 'message': 'تم جدولة الرسالة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/templates', methods=['GET'])
@login_required
def api_templates():
    user_id = current_user.id
    try:
        templates = get_message_templates(user_id)
        return jsonify({'templates': templates})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@messages_bp.route('/api/search', methods=['GET'])
@login_required
def api_search():
    user_id = current_user.id
    query = request.args.get('q', '')
    try:
        convs = get_conversations(user_id, search=query)
        return jsonify({'results': convs})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
