from functools import wraps
from flask import flash, redirect, url_for, abort, session
from flask_login import current_user

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('user_role') or session.get('role') or getattr(current_user, 'role', None)
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if role != 'admin':
            flash('عذراً، هذه الصفحة مخصصة لمدراء النظام فقط', 'danger')
            return redirect(url_for('teacher.dashboard'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('user_role') or session.get('role') or getattr(current_user, 'role', None)
        if not current_user.is_authenticated:
            return redirect(url_for('auth.login'))
        if role not in ['admin', 'teacher']:
            flash('عذراً، هذه الصفحة مخصصة للكادر التعليمي والإداري فقط', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

