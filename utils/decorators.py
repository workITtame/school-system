from functools import wraps
from flask import flash, redirect, url_for
from flask_login import current_user

from flask import session

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        role = session.get('user_role') or session.get('role') or getattr(current_user, 'role', None)
        if not current_user.is_authenticated or role != 'admin':
            flash('عذراً، هذه الصفحة مخصصة لمدراء النظام فقط', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function

def teacher_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role not in ['admin', 'teacher']:
            flash('عذراً، يجب أن يكون لديك صلاحيات للوصول لهذه الصفحة', 'danger')
            return redirect(url_for('dashboard.index'))
        return f(*args, **kwargs)
    return decorated_function
