from datetime import datetime, date

def format_relative_time(value):
    """Formats a datetime/date object into Arabic relative time string."""
    if not value:
        return 'الآن'
    
    now = datetime.now()
    if isinstance(value, date) and not isinstance(value, datetime):
        value = datetime.combine(value, datetime.min.time())

    diff = now - value
    seconds = int(diff.total_seconds())

    if seconds < 60:
        return 'الآن'
    elif seconds < 120:
        return 'منذ دقيقة'
    elif seconds < 3600:
        minutes = seconds // 60
        return f"منذ {minutes} دقائق"
    elif seconds < 7200:
        return 'منذ ساعة'
    elif seconds < 86400:
        hours = seconds // 3600
        return f"منذ {hours} ساعات"
    elif seconds < 172800:
        return 'أمس'
    else:
        days = seconds // 86400
        return f"منذ {days} أيام"

def format_days_remaining(value):
    """Formats an exam date into Arabic remaining days string."""
    if not value:
        return '-'

    today = datetime.now().date()
    if isinstance(value, datetime):
        value = value.date()

    diff_days = (value - today).days

    if diff_days < 0:
        return 'منتهية'
    elif diff_days == 0:
        return 'اليوم'
    elif diff_days == 1:
        return 'غداً'
    elif diff_days == 2:
        return 'بعد يومين'
    else:
        return f"بعد {diff_days} أيام"

def get_notification_meta(category_name):
    """Returns meta details (title, icon, badge color) for a notification category."""
    cat = (category_name or '').strip().lower()
    
    if 'إداري' in cat or 'اداري' in cat or 'نظام' in cat or 'إدارة' in cat:
        return {'title': 'إداري', 'icon': 'fa-solid fa-building-user', 'color': 'purple', 'bg_class': 'bg-purple-subtle text-purple'}
    elif 'واجب' in cat:
        return {'title': 'واجب', 'icon': 'fa-solid fa-book-bookmark', 'color': 'warning', 'bg_class': 'bg-warning-subtle text-warning'}
    elif 'اختبار' in cat or 'امتحان' in cat:
        return {'title': 'اختبار', 'icon': 'fa-solid fa-file-signature', 'color': 'danger', 'bg_class': 'bg-danger-subtle text-danger'}
    elif 'حضور' in cat or 'غياب' in cat:
        return {'title': 'حضور', 'icon': 'fa-solid fa-user-check', 'color': 'success', 'bg_class': 'bg-success-subtle text-success'}
    else:
        return {'title': 'رسالة', 'icon': 'fa-regular fa-envelope', 'color': 'primary', 'bg_class': 'bg-primary-subtle text-primary'}

def register_template_filters(app):
    """Registers custom Jinja template filters to Flask app."""
    app.jinja_env.filters['format_relative_time'] = format_relative_time
    app.jinja_env.filters['format_days_remaining'] = format_days_remaining
    app.jinja_env.filters['get_notification_meta'] = get_notification_meta
