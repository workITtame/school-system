from functools import wraps
from flask import flash, redirect, url_for, abort, session
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        raw_role = session.get('user_role') or session.get('role') or getattr(current_user, 'role', '')
        role = str(raw_role).strip("'\"").lower() if raw_role else ''
        if not current_user.is_authenticated or role != 'admin':
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        raw_role = session.get('user_role') or session.get('role') or getattr(current_user, 'role', '')
        role = str(raw_role).strip("'\"").lower() if raw_role else ''
        if not current_user.is_authenticated or role not in ['admin', 'teacher']:
            abort(403)
        return f(*args, **kwargs)
    return decorated_function

