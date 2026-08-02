from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_required
from models import db, Homework, Subject, Classes, Sections
from datetime import datetime

homework_bp = Blueprint('homework', __name__, url_prefix='/homework')

@homework_bp.route('/')
@login_required
def index():
    homework_list = Homework.query.order_by(Homework.due_date.desc()).all()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()

    total_count = len(homework_list)
    completed_count = sum(1 for h in homework_list if h.status == 'مكتمل')
    pending_count = sum(1 for h in homework_list if h.status == 'معلق')
    late_count = sum(1 for h in homework_list if h.status == 'متأخر')

    return render_template('homework/index.html',
                           homework_list=homework_list,
                           subjects=subjects,
                           classes=classes,
                           sections=sections,
                           total_count=total_count,
                           completed_count=completed_count,
                           pending_count=pending_count,
                           late_count=late_count)

@homework_bp.route('/add', methods=['POST'])
@login_required
def add_homework():
    title = request.form.get('title')
    sub_id = request.form.get('sub_id')
    class_id = request.form.get('class_id')
    section_id = request.form.get('section_id')
    due_date_str = request.form.get('due_date')
    status = request.form.get('status', 'معلق')
    description = request.form.get('description')

    if title and sub_id and class_id and due_date_str:
        try:
            due_date = datetime.strptime(due_date_str, '%Y-%m-%d').date()
            new_hw = Homework(
                title=title,
                sub_id=sub_id,
                class_id=class_id,
                section_id=section_id if section_id else None,
                due_date=due_date,
                status=status,
                description=description
            )
            db.session.add(new_hw)
            db.session.commit()
            flash('تمت إضافة الواجب الدراسي بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء الحفظ: {str(e)}', 'danger')
    else:
        flash('جميع الحقول الأساسية مطلوبة', 'warning')

    return redirect(url_for('homework.index'))

@homework_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_homework(id):
    hw = Homework.query.get_or_404(id)
    try:
        db.session.delete(hw)
        db.session.commit()
        flash('تم حذف الواجب بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
    return redirect(url_for('homework.index'))
