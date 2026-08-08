import logging
from datetime import datetime
from flask import Blueprint, render_template, request, jsonify
from flask_login import login_required, current_user
from models import Teacher, Classes, Subject, Sections
from services.teacher_profile_service import (
    get_teacher_profile,
    update_teacher_profile,
    update_password,
    upload_avatar,
    remove_avatar,
    get_notification_preferences,
    update_notification_preferences,
    get_dashboard_preferences,
    save_dashboard_preferences,
    get_login_history,
    get_active_sessions,
    terminate_session,
    terminate_all_sessions,
    export_personal_data
)

logger = logging.getLogger(__name__)

profile_bp = Blueprint('profile', __name__, url_prefix='/profile')

def _get_teacher_meta(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    return teacher, subjects, classes, sections

@profile_bp.route('/', methods=['GET'])
@login_required
def index():
    user_id = current_user.id
    user_role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None

    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()

    if user_role != 'teacher':
        profile = {
            'name': getattr(current_user, 'name', 'مدير النظام'),
            'email': getattr(current_user, 'username', 'admin'),
            'role': 'مدير النظام',
            'phone': '770000000',
            'address': 'الإدارة العامة'
        }
        return render_template(
            'profile.html',
            profile=profile,
            notif_prefs={},
            dash_prefs={},
            sessions=[],
            login_history=[],
            subjects=subjects,
            classes=classes,
            sections=sections,
            teacher_info=None,
            today=datetime.now().strftime('%Y-%m-%d')
        )

    try:
        teacher, subjects, classes, sections = _get_teacher_meta(user_id)
        profile = get_teacher_profile(user_id)
        notif_prefs = get_notification_preferences(user_id)
        dash_prefs = get_dashboard_preferences(user_id)
        sessions = get_active_sessions(user_id)
        history = get_login_history(user_id)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"Error loading profile center: {e}")
        profile = {}
        notif_prefs, dash_prefs, sessions, history = {}, {}, [], []
        teacher = None

    return render_template(
        'teacher/profile.html',
        profile=profile,
        notif_prefs=notif_prefs,
        dash_prefs=dash_prefs,
        sessions=sessions,
        login_history=history,
        subjects=subjects,
        classes=classes,
        sections=sections,
        teacher_info=teacher,
        today=datetime.now().strftime('%Y-%m-%d')
    )

@profile_bp.route('/api/profile', methods=['GET'])
@login_required
def api_profile():
    user_id = current_user.id
    try:
        profile = get_teacher_profile(user_id)
        return jsonify(profile)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/preferences', methods=['GET'])
@login_required
def api_preferences():
    user_id = current_user.id
    try:
        notif = get_notification_preferences(user_id)
        dash = get_dashboard_preferences(user_id)
        return jsonify({'notification_preferences': notif, 'dashboard_preferences': dash})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/security', methods=['GET'])
@login_required
def api_security():
    user_id = current_user.id
    try:
        profile = get_teacher_profile(user_id)
        return jsonify({
            'security_score': profile.get('security_score', 'A+'),
            'two_factor_enabled': False,
            'last_password_change': '2026-07-01'
        })
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/sessions', methods=['GET'])
@login_required
def api_sessions():
    user_id = current_user.id
    try:
        sessions = get_active_sessions(user_id)
        history = get_login_history(user_id)
        return jsonify({'active_sessions': sessions, 'login_history': history})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/update', methods=['POST'])
@login_required
def api_update():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    try:
        updated = update_teacher_profile(user_id, payload)
        return jsonify({'success': True, 'profile': updated, 'message': 'تم حفظ وتحديث البيانات الشخصية بنجاح 🟢'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/password', methods=['POST'])
@login_required
def api_password():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    curr_pass = payload.get('current_password', '')
    new_pass = payload.get('new_password', '')

    if not new_pass:
        return jsonify({'error': 'New password is required'}), 400

    try:
        update_password(user_id, curr_pass, new_pass)
        return jsonify({'success': True, 'message': 'تم تغيير كلمة المرور بنجاح 🔒'})
    except ValueError as ve:
        return jsonify({'error': str(ve)}), 400
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/avatar', methods=['POST'])
@login_required
def api_avatar():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    action = payload.get('action', 'upload')
    avatar_url = payload.get('avatar_url', '/static/images/default_avatar.png')

    try:
        if action == 'remove':
            remove_avatar(user_id)
            msg = 'تم إزالة الصورة الشخصية'
        else:
            upload_avatar(user_id, avatar_url)
            msg = 'تم تحديث الصورة الشخصية بنجاح'
        return jsonify({'success': True, 'message': msg})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/preferences', methods=['POST'])
@login_required
def api_save_preferences():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    try:
        saved = update_notification_preferences(user_id, payload)
        return jsonify({'success': True, 'preferences': saved, 'message': 'تم حفظ إعدادات وتفضيلات الإشعارات 🔔'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/dashboard', methods=['POST'])
@login_required
def api_save_dashboard():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    try:
        saved = save_dashboard_preferences(user_id, payload)
        return jsonify({'success': True, 'dashboard': saved, 'message': 'تم حفظ تفضيلات وتنسيق لوحة التحكم 📊'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/logout-session', methods=['POST'])
@login_required
def api_logout_session():
    user_id = current_user.id
    payload = request.get_json(silent=True) or {}
    session_id = payload.get('session_id')
    try:
        terminate_session(user_id, session_id)
        return jsonify({'success': True, 'message': 'تم إنهاء وتمرير الجلسة المحددة بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/logout-all', methods=['POST'])
@login_required
def api_logout_all():
    user_id = current_user.id
    try:
        terminate_all_sessions(user_id)
        return jsonify({'success': True, 'message': 'تم تسجيل الخروج وإنهاء جميع الأجهزة الأخرى بنجاح 🔒'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@profile_bp.route('/api/export', methods=['GET'])
@login_required
def api_export():
    user_id = current_user.id
    fmt = request.args.get('format', 'json')
    try:
        data = export_personal_data(user_id, format=fmt)
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500
