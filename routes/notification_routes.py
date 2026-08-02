from flask import Blueprint, render_template, session, redirect, url_for
from flask_login import login_required

notifications_bp = Blueprint('notifications', __name__, url_prefix='/notifications')

@notifications_bp.route('/')
@login_required
def index():
    # Sample notifications list
    notifications_list = [
        {'id': 1, 'title': 'تم إضافة واجب جديد في مادة الرياضيات', 'time': 'قبل 10 دقائق', 'category': 'واجبات', 'read': False},
        {'id': 2, 'title': 'تنبيه: اختبار الشهر الأول للصف الأول الثانوي', 'time': 'قبل ساعة', 'category': 'اختبارات', 'read': False},
        {'id': 3, 'title': 'تم تسجيل غياب لـ 3 طلاب في شعبة 1', 'time': 'قبل 3 ساعات', 'category': 'حضور', 'read': True},
        {'id': 4, 'title': 'اجتماع مجلس المعلمين القادم غداً الساعة 10 صباحاً', 'time': 'أمس', 'category': 'إدارة', 'read': True},
    ]
    return render_template('notifications.html', notifications=notifications_list)
