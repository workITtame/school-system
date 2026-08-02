from flask import Blueprint, render_template, request, redirect, url_for, session
from models import Qualifications
from utils.decorators import admin_required

teacher_bp = Blueprint('teacher', __name__, url_prefix='/teacher')

from models import Qualifications, Teacher

@teacher_bp.route('/')
def index():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    qualifications = Qualifications.query.all()
    
    total_teachers = Teacher.query.filter_by(is_deleted=False).count()
    male_teachers = Teacher.query.filter(Teacher.is_deleted == False, Teacher.Gender.in_(['ذكر', 'Male'])).count()
    female_teachers = Teacher.query.filter(Teacher.is_deleted == False, Teacher.Gender.in_(['أنثى', 'Female'])).count()
    active_teachers = Teacher.query.filter_by(is_deleted=False, Status='نشط').count()
    
    return render_template('teacher/index.html', 
                           qualifications=qualifications,
                           total_teachers=total_teachers,
                           male_teachers=male_teachers,
                           female_teachers=female_teachers,
                           new_teachers=active_teachers)

@teacher_bp.route('/view/<int:id>')
def view_teacher(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    teacher = Teacher.query.get_or_404(id)
    return render_template('teacher/view.html', teacher=teacher)
