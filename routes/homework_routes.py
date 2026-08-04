from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required
from models import db, Homework, Subject, Classes, Sections, Student, Teacher, Terms
from sqlalchemy import func
from datetime import datetime
from collections import defaultdict

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


@homework_bp.route('/analytics')
@login_required
def analytics():
    """
    Homework Analytics & Reports — Phase 4
    All data sourced exclusively from existing DB tables.
    No hardcoded values. No new tables/columns/models.
    """
    # ─── Filter parameters ────────────────────────────────────────────
    filter_class_id    = request.args.get('class_id',   type=int)
    filter_section_id  = request.args.get('section_id', type=int)
    filter_subject_id  = request.args.get('subject_id', type=int)
    filter_status      = request.args.get('status',     type=str)
    filter_date_from   = request.args.get('date_from',  type=str)
    filter_date_to     = request.args.get('date_to',    type=str)

    # ─── Base query with optional filters ─────────────────────────────
    query = Homework.query

    if filter_class_id:
        query = query.filter(Homework.class_id == filter_class_id)
    if filter_section_id:
        query = query.filter(Homework.section_id == filter_section_id)
    if filter_subject_id:
        query = query.filter(Homework.sub_id == filter_subject_id)
    if filter_status:
        query = query.filter(Homework.status == filter_status)
    if filter_date_from:
        try:
            query = query.filter(Homework.due_date >= datetime.strptime(filter_date_from, '%Y-%m-%d').date())
        except ValueError:
            pass
    if filter_date_to:
        try:
            query = query.filter(Homework.due_date <= datetime.strptime(filter_date_to, '%Y-%m-%d').date())
        except ValueError:
            pass

    homework_list = query.order_by(Homework.created_at.desc()).all()

    # ─── Top-level KPIs ───────────────────────────────────────────────
    total_count     = len(homework_list)
    completed_count = sum(1 for h in homework_list if h.status == 'مكتمل')
    pending_count   = sum(1 for h in homework_list if h.status == 'معلق')
    late_count      = sum(1 for h in homework_list if h.status == 'متأخر')
    completion_rate = round((completed_count / total_count * 100), 1) if total_count > 0 else 0
    late_rate       = round((late_count      / total_count * 100), 1) if total_count > 0 else 0

    # ─── By Subject breakdown ─────────────────────────────────────────
    subject_map = defaultdict(lambda: {'total': 0, 'completed': 0, 'pending': 0, 'late': 0, 'name': ''})
    for hw in homework_list:
        sub_id   = hw.sub_id
        sub_name = hw.subject.SubName if hw.subject else 'مادة غير محددة'
        subject_map[sub_id]['name']  = sub_name
        subject_map[sub_id]['total'] += 1
        if hw.status == 'مكتمل':
            subject_map[sub_id]['completed'] += 1
        elif hw.status == 'معلق':
            subject_map[sub_id]['pending']   += 1
        else:
            subject_map[sub_id]['late']      += 1

    subject_stats = sorted(subject_map.values(), key=lambda x: x['total'], reverse=True)
    for s in subject_stats:
        s['rate'] = round((s['completed'] / s['total'] * 100), 1) if s['total'] > 0 else 0

    # ─── By Class breakdown ───────────────────────────────────────────
    class_map = defaultdict(lambda: {'total': 0, 'completed': 0, 'pending': 0, 'late': 0, 'name': '', 'student_count': 0})
    for hw in homework_list:
        cid    = hw.class_id
        cname  = hw.school_class.CName if hw.school_class else 'صف غير محدد'
        class_map[cid]['name']  = cname
        class_map[cid]['total'] += 1
        if hw.status == 'مكتمل':
            class_map[cid]['completed'] += 1
        elif hw.status == 'معلق':
            class_map[cid]['pending']   += 1
        else:
            class_map[cid]['late']      += 1

    # Enrich with student count from Student table
    student_counts = db.session.query(Student.CID, func.count(Student.SID))\
        .filter(Student.is_deleted == False)\
        .group_by(Student.CID).all()
    sc_map = {row[0]: row[1] for row in student_counts}

    for cid, data in class_map.items():
        data['student_count'] = sc_map.get(cid, 0)
        data['rate'] = round((data['completed'] / data['total'] * 100), 1) if data['total'] > 0 else 0

    class_stats = sorted(class_map.values(), key=lambda x: x['total'], reverse=True)

    # ─── By Section breakdown ─────────────────────────────────────────
    section_map = defaultdict(lambda: {'total': 0, 'completed': 0, 'pending': 0, 'late': 0, 'name': ''})
    for hw in homework_list:
        sec_id   = hw.section_id or 0
        sec_name = hw.section.SectionName if hw.section else 'جميع الشعب'
        section_map[sec_id]['name']  = sec_name
        section_map[sec_id]['total'] += 1
        if hw.status == 'مكتمل':
            section_map[sec_id]['completed'] += 1
        elif hw.status == 'معلق':
            section_map[sec_id]['pending']   += 1
        else:
            section_map[sec_id]['late']      += 1

    for data in section_map.values():
        data['rate'] = round((data['completed'] / data['total'] * 100), 1) if data['total'] > 0 else 0
    section_stats = sorted(section_map.values(), key=lambda x: x['total'], reverse=True)

    # ─── Monthly activity (by created_at) ─────────────────────────────
    month_map = defaultdict(int)
    arabic_months = ['يناير', 'فبراير', 'مارس', 'أبريل', 'مايو', 'يونيو',
                     'يوليو', 'أغسطس', 'سبتمبر', 'أكتوبر', 'نوفمبر', 'ديسمبر']
    for hw in homework_list:
        if hw.created_at:
            key = f"{hw.created_at.year}-{hw.created_at.month:02d}"
            month_map[key] += 1

    monthly_labels = []
    monthly_data   = []
    for key in sorted(month_map.keys()):
        year, month = key.split('-')
        monthly_labels.append(f"{arabic_months[int(month)-1]} {year}")
        monthly_data.append(month_map[key])

    # ─── Due-date distribution by month ───────────────────────────────
    due_month_map = defaultdict(int)
    for hw in homework_list:
        if hw.due_date:
            key = f"{hw.due_date.year}-{hw.due_date.month:02d}"
            due_month_map[key] += 1

    due_labels = []
    due_data   = []
    for key in sorted(due_month_map.keys()):
        year, month = key.split('-')
        due_labels.append(f"{arabic_months[int(month)-1]} {year}")
        due_data.append(due_month_map[key])

    # ─── Status chart data ────────────────────────────────────────────
    status_labels = ['مكتمل', 'معلق', 'متأخر']
    status_data   = [completed_count, pending_count, late_count]
    status_colors = ['#22c55e', '#eab308', '#ef4444']

    # ─── Subject chart data (top 10) ─────────────────────────────────
    top_subjects       = subject_stats[:10]
    chart_sub_labels   = [s['name']  for s in top_subjects]
    chart_sub_total    = [s['total'] for s in top_subjects]
    chart_sub_complete = [s['completed'] for s in top_subjects]
    chart_sub_late     = [s['late']  for s in top_subjects]

    # ─── Class chart data (top 10) ────────────────────────────────────
    top_classes       = class_stats[:10]
    chart_cls_labels  = [c['name']  for c in top_classes]
    chart_cls_total   = [c['total'] for c in top_classes]
    chart_cls_complete= [c['completed'] for c in top_classes]

    # ─── Dropdown data ────────────────────────────────────────────────
    all_classes  = Classes.query.filter_by(is_deleted=False).order_by(Classes.CName).all()
    all_sections = Sections.query.filter_by(is_deleted=False).order_by(Sections.SectionName).all()
    all_subjects = Subject.query.filter_by(is_deleted=False).order_by(Subject.SubName).all()
    all_terms    = Terms.query.order_by(Terms.T_ID.desc()).all()

    # ─── Recent homework list (last 10) ───────────────────────────────
    recent_hw = homework_list[:10]

    return render_template(
        'homework/analytics.html',
        # KPIs
        total_count=total_count,
        completed_count=completed_count,
        pending_count=pending_count,
        late_count=late_count,
        completion_rate=completion_rate,
        late_rate=late_rate,
        # Stats breakdowns
        subject_stats=subject_stats,
        class_stats=class_stats,
        section_stats=section_stats,
        recent_hw=recent_hw,
        # Chart data (JSON-safe Python lists)
        status_labels=status_labels,
        status_data=status_data,
        status_colors=status_colors,
        chart_sub_labels=chart_sub_labels,
        chart_sub_total=chart_sub_total,
        chart_sub_complete=chart_sub_complete,
        chart_sub_late=chart_sub_late,
        chart_cls_labels=chart_cls_labels,
        chart_cls_total=chart_cls_total,
        chart_cls_complete=chart_cls_complete,
        monthly_labels=monthly_labels,
        monthly_data=monthly_data,
        due_labels=due_labels,
        due_data=due_data,
        # Dropdowns
        all_classes=all_classes,
        all_sections=all_sections,
        all_subjects=all_subjects,
        all_terms=all_terms,
        # Active filters
        filter_class_id=filter_class_id,
        filter_section_id=filter_section_id,
        filter_subject_id=filter_subject_id,
        filter_status=filter_status,
        filter_date_from=filter_date_from,
        filter_date_to=filter_date_to,
    )
