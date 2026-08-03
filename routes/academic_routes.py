from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from sqlalchemy.exc import IntegrityError
from models import db, Classes, Sections, Subject, Days, Lessons, Terms, TypeExams, Student, ExamSchedule
from models.timetable import SchoolTable
from utils.decorators import admin_required

academic_bp = Blueprint('academic', __name__, url_prefix='/academic')

@academic_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    # Redirect to classes by default
    return redirect(url_for('academic.classes'))

@academic_bp.route('/classes')
def classes():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    classes_list = Classes.query.filter_by(is_deleted=False).order_by(Classes.CID.asc()).all()
    sections_list = Sections.query.filter_by(is_deleted=False).all()
    
    total_classes = len(classes_list)
    total_sections = len(sections_list)
    active_classes = sum(1 for c in classes_list if getattr(c, 'Status', 'نشط') in ['نشط', None])
    active_sections = sum(1 for s in sections_list if getattr(s, 'Status', 'نشط') in ['نشط', None])
    
    total_students = Student.query.filter_by(is_deleted=False).count()
    avg_students_per_class = round(total_students / total_classes, 1) if total_classes > 0 else 0
    
    # Calculate overall occupancy strictly for classes where MaxStudents is defined
    total_capacity = sum(c.MaxStudents for c in classes_list if c.MaxStudents and c.MaxStudents > 0)
    overall_occupancy_rate = round((total_students / total_capacity) * 100, 1) if total_capacity > 0 else None
    
    # Enrich each class object with real dynamic metrics
    for c in classes_list:
        c.linked_sections = [s for s in c.sections if not getattr(s, 'is_deleted', False)]
        c.students_count = Student.query.filter_by(CID=c.CID, is_deleted=False).count()
        c.teachers_count = db.session.query(SchoolTable.TeacherID).filter_by(CID=c.CID, is_deleted=False).distinct().count()
        c.subjects_count = len([sub for sub in c.subjects if not getattr(sub, 'is_deleted', False)])
        
        # Calculate occupancy rate (MUST be None if MaxStudents is None or 0)
        if c.MaxStudents and c.MaxStudents > 0:
            c.occupancy_percentage = round((c.students_count / c.MaxStudents) * 100, 1)
            if c.occupancy_percentage < 70:
                c.occupancy_color = 'success'
            elif c.occupancy_percentage <= 90:
                c.occupancy_color = 'warning'
            else:
                c.occupancy_color = 'danger'
        else:
            c.occupancy_percentage = None
            c.occupancy_color = 'secondary'
            
    middle_school = sum(1 for c in classes_list if c.Stage == 'المتوسطة')
    high_school = sum(1 for c in classes_list if c.Stage == 'الثانوية')
    primary_school = sum(1 for c in classes_list if c.Stage == 'الأساسية')
    
    return render_template('academic/classes.html', 
                           classes=classes_list, 
                           sections=sections_list,
                           middle_school=middle_school,
                           high_school=high_school,
                           primary_school=primary_school,
                           total_sections=total_sections,
                           total_classes=total_classes,
                           active_classes=active_classes,
                           active_sections=active_sections,
                           avg_students_per_class=avg_students_per_class,
                           overall_occupancy_rate=overall_occupancy_rate)

@academic_bp.route('/subjects')
def subjects():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    class_id = request.args.get('class_id', type=int)
    classes = Classes.query.filter_by(is_deleted=False).all()
    
    query = Subject.query
    if hasattr(Subject, 'is_deleted'):
        query = query.filter_by(is_deleted=False)
        
    if class_id:
        from models.academic import ClassSubject
        subject_ids = [cs[0] for cs in db.session.query(ClassSubject.c.SubID).filter(ClassSubject.c.CID == class_id).all()]
        subjects_list = query.filter(Subject.SubID.in_(subject_ids)).order_by(Subject.SubID.asc()).all() if subject_ids else []
    else:
        subjects_list = query.order_by(Subject.SubID.asc()).all()
        
    total_subjects = len(subjects_list)
    active_subjects = sum(1 for s in subjects_list if getattr(s, 'Status', 'نشط') in ['نشط', None])
    inactive_subjects = sum(1 for s in subjects_list if getattr(s, 'Status', 'نشط') == 'غير نشط')
    
    from models import SchoolTable
    from models.academic import ClassSubject, TeacherSubject
    
    total_classes = len(classes)
    linked_classes_count = db.session.query(ClassSubject.c.CID).distinct().count()
    assigned_teachers_count = db.session.query(TeacherSubject.c.TeacherID).distinct().count()
    
    total_links = db.session.query(ClassSubject).count()
    avg_subjects_per_class = round(total_links / total_classes, 1) if total_classes > 0 else 0.0
    
    for s in subjects_list:
        s.linked_classes = [c for c in s.classes if not getattr(c, 'is_deleted', False)]
        s.linked_classes_count = len(s.linked_classes)
        
        t_ids_ts = [t[0] for t in db.session.query(TeacherSubject.c.TeacherID).filter(TeacherSubject.c.SubID == s.SubID).distinct().all() if t[0]]
        t_ids_st = [t[0] for t in db.session.query(SchoolTable.TeacherID).filter(SchoolTable.SubID == s.SubID, SchoolTable.is_deleted == False).distinct().all() if t[0]]
        s.assigned_teachers_count = len(set(t_ids_ts + t_ids_st))
        
        class_ids = [c.CID for c in s.linked_classes]
        if class_ids:
            s.students_count = Student.query.filter(Student.CID.in_(class_ids), Student.is_deleted == False).count()
        else:
            s.students_count = 0
            
        s.weekly_slots_count = SchoolTable.query.filter(SchoolTable.SubID == s.SubID, SchoolTable.is_deleted == False).count()
        
    selected_class = Classes.query.filter_by(CID=class_id).first() if class_id else None
    
    return render_template('academic/subjects.html', 
                           subjects=subjects_list,
                           classes=classes,
                           selected_class_id=class_id,
                           selected_class=selected_class,
                           total_subjects=total_subjects,
                           active_subjects=active_subjects,
                           inactive_subjects=inactive_subjects,
                           linked_classes_count=linked_classes_count,
                           assigned_teachers_count=assigned_teachers_count,
                           avg_subjects_per_class=avg_subjects_per_class)

@academic_bp.route('/add_class', methods=['POST'])
def add_class():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    name = request.form.get('name')
    stage = request.form.get('stage')
    if name:
        new_class = Classes(CName=name, Stage=stage)
        db.session.add(new_class)
        db.session.commit()
        flash('تمت إضافة الصف بنجاح', 'success')
    return redirect(url_for('academic.classes'))

@academic_bp.route('/add_section', methods=['POST'])
def add_section():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    name = request.form.get('name')
    class_id = request.form.get('class_id')
    if name and class_id:
        new_section = Sections(SectionName=name)
        c = Classes.query.get(class_id)
        if c:
            new_section.classes.append(c)
        db.session.add(new_section)
        db.session.commit()
        flash('تمت إضافة الشعبة بنجاح', 'success')
    return redirect(url_for('academic.classes'))

@academic_bp.route('/add_subject', methods=['POST'])
def add_subject():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    name = request.form.get('name')
    sub_type = request.form.get('type')
    department = request.form.get('department')
    status = request.form.get('status', 'نشط')
    
    if name:
        new_subject = Subject(SubName=name, Type=sub_type, Department=department, Status=status)
        db.session.add(new_subject)
        db.session.commit()
        flash('تمت إضافة المادة بنجاح', 'success')
    return redirect(url_for('academic.subjects'))

@academic_bp.route('/add_day', methods=['POST'])
def add_day():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    name = request.form.get('name')
    if name:
        db.session.add(Days(DName=name))
        db.session.commit()
        flash('تمت إضافة اليوم بنجاح', 'success')
    return redirect(url_for('academic.index'))

@academic_bp.route('/add_lesson', methods=['POST'])
def add_lesson():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    name = request.form.get('name')
    if name:
        db.session.add(Lessons(LessonName=name))
        db.session.commit()
        flash('تمت إضافة الحصة بنجاح', 'success')
    return redirect(url_for('academic.index'))

@academic_bp.route('/add_term', methods=['POST'])
def add_term():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    name = request.form.get('name')
    if name:
        db.session.add(Terms(T_Name=name))
        db.session.commit()
        flash('تمت إضافة الترم بنجاح', 'success')
    return redirect(url_for('academic.index'))

@academic_bp.route('/add_exam_type', methods=['POST'])
def add_exam_type():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    name = request.form.get('name')
    if name:
        db.session.add(TypeExams(ExamName=name))
        db.session.commit()
        flash('تمت إضافة نوع الاختبار بنجاح', 'success')
    return redirect(url_for('academic.index'))


# --- EDIT AND DELETE ROUTES ---

def handle_edit(obj, attr_name, new_val):
    if new_val:
        setattr(obj, attr_name, new_val)
        db.session.commit()
        flash('تم التعديل بنجاح', 'success')

def handle_delete(obj):
    try:
        db.session.delete(obj)
        db.session.commit()
        flash('تم الحذف بنجاح', 'success')
    except IntegrityError:
        db.session.rollback()
        flash('لا يمكن الحذف لارتباط هذا العنصر ببيانات أخرى', 'danger')

# Classes
@academic_bp.route('/edit_class/<int:id>', methods=['POST'])
def edit_class(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    c = Classes.query.get_or_404(id)
    name = request.form.get('name')
    stage = request.form.get('stage')
    if name: c.CName = name
    if stage: c.Stage = stage
    db.session.commit()
    flash('تم تعديل الصف بنجاح', 'success')
    return redirect(url_for('academic.classes'))

@academic_bp.route('/delete_class/<int:id>', methods=['POST'])
def delete_class(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    c = Classes.query.get_or_404(id)
    student_count = Student.query.filter_by(CID=id, is_deleted=False).count()
    if student_count > 0:
        flash('لا يمكن حذف الصف لاحتوائه على طلاب مسجلين بالفعلي. يرجى نقل الطلاب أو تفريغ الصف أولاً.', 'danger')
        return redirect(url_for('academic.classes'))
    handle_delete(c)
    return redirect(url_for('academic.classes'))

# Sections
@academic_bp.route('/edit_section/<int:id>', methods=['POST'])
def edit_section(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    s = Sections.query.get_or_404(id)
    name = request.form.get('name')
    if name: s.SectionName = name
    class_id = request.form.get('class_id')
    if class_id:
        c = Classes.query.get(class_id)
        if c and c not in s.classes:
            s.classes.append(c)
    db.session.commit()
    flash('تم تعديل الشعبة بنجاح', 'success')
    return redirect(url_for('academic.classes'))

@academic_bp.route('/delete_section/<int:id>', methods=['POST'])
def delete_section(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    s = Sections.query.get_or_404(id)
    student_count = Student.query.filter_by(SectionID=id, is_deleted=False).count()
    if student_count > 0:
        flash('لا يمكن حذف الشعبة لاحتوائها على طلاب مسجلين بالفعلي. يرجى نقل الطلاب أو تفريغ الشعبة أولاً.', 'danger')
        return redirect(url_for('academic.classes'))
    s.classes.clear()
    handle_delete(s)
    return redirect(url_for('academic.classes'))

# Subjects (handled via enriched endpoints at end of module)

# Days
@academic_bp.route('/edit_day/<int:id>', methods=['POST'])
def edit_day(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    d = Days.query.get_or_404(id)
    handle_edit(d, 'DName', request.form.get('name'))
    return redirect(url_for('academic.index'))

@academic_bp.route('/delete_day/<int:id>', methods=['POST'])
def delete_day(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    d = Days.query.get_or_404(id)
    handle_delete(d)
    return redirect(url_for('academic.index'))

# Lessons
@academic_bp.route('/edit_lesson/<int:id>', methods=['POST'])
def edit_lesson(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    l = Lessons.query.get_or_404(id)
    handle_edit(l, 'LessonName', request.form.get('name'))
    return redirect(url_for('academic.index'))

@academic_bp.route('/delete_lesson/<int:id>', methods=['POST'])
def delete_lesson(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    l = Lessons.query.get_or_404(id)
    handle_delete(l)
    return redirect(url_for('academic.index'))

# Terms
@academic_bp.route('/edit_term/<int:id>', methods=['POST'])
def edit_term(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    t = Terms.query.get_or_404(id)
    handle_edit(t, 'T_Name', request.form.get('name'))
    return redirect(url_for('academic.index'))

@academic_bp.route('/delete_term/<int:id>', methods=['POST'])
def delete_term(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    t = Terms.query.get_or_404(id)
    handle_delete(t)
    return redirect(url_for('academic.index'))

# Exam Types
@academic_bp.route('/edit_exam_type/<int:id>', methods=['POST'])
def edit_exam_type(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    et = TypeExams.query.get_or_404(id)
    handle_edit(et, 'ExamName', request.form.get('name'))
    return redirect(url_for('academic.index'))

@academic_bp.route('/delete_exam_type/<int:id>', methods=['POST'])
def delete_exam_type(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    et = TypeExams.query.get_or_404(id)
    handle_delete(et)
    return redirect(url_for('academic.index'))

@academic_bp.route('/classes/export/excel')
def export_classes_excel():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    import io
    from flask import send_file
    
    ids_param = request.args.get('ids', '').strip()
    query = Classes.query.filter_by(is_deleted=False)
    if ids_param:
        id_list = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
        classes_list = query.filter(Classes.CID.in_(id_list)).all()
    else:
        classes_list = query.order_by(Classes.CID.asc()).all()
        
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "قائمة الصفوف والشعب"
    ws.sheet_view.rightToLeft = True
    
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    
    headers = ["كود الصف", "اسم الصف", "المرحلة الدراسية", "عدد الشعب", "عدد الطلاب", "السعة القصوى", "نسبة الإشغال", "عدد المعلمين", "عدد المواد"]
    ws.append(headers)
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        
    for c in classes_list:
        st_count = Student.query.filter_by(CID=c.CID, is_deleted=False).count()
        t_count = db.session.query(SchoolTable.TeacherID).filter_by(CID=c.CID, is_deleted=False).distinct().count()
        sub_count = len([sub for sub in c.subjects if not getattr(sub, 'is_deleted', False)])
        sec_count = len([sec for sec in c.sections if not getattr(sec, 'is_deleted', False)])
        
        occ = f"{round((st_count / c.MaxStudents) * 100, 1)}%" if c.MaxStudents and c.MaxStudents > 0 else "غير محددة"
        max_st = c.MaxStudents if c.MaxStudents else "غير محددة"
        
        row = [
            f"CLS-{c.CID}",
            c.CName,
            c.Stage or 'غير محددة',
            sec_count,
            st_count,
            max_st,
            occ,
            t_count,
            sub_count
        ]
        ws.append(row)
        for cell in ws[ws.max_row]:
            cell.alignment = align_center
            
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
        ws.column_dimensions[col].width = 20
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='classes_export.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@academic_bp.route('/classes/export/pdf')
def export_classes_pdf():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    from datetime import datetime
    
    ids_param = request.args.get('ids', '').strip()
    query = Classes.query.filter_by(is_deleted=False)
    if ids_param:
        id_list = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
        classes_list = query.filter(Classes.CID.in_(id_list)).all()
    else:
        classes_list = query.order_by(Classes.CID.asc()).all()
        
    for c in classes_list:
        c.linked_sections = [s for s in c.sections if not getattr(s, 'is_deleted', False)]
        c.students_count = Student.query.filter_by(CID=c.CID, is_deleted=False).count()
        c.teachers_count = db.session.query(SchoolTable.TeacherID).filter_by(CID=c.CID, is_deleted=False).distinct().count()
        c.subjects_count = len([sub for sub in c.subjects if not getattr(sub, 'is_deleted', False)])
        c.occ_str = f"{round((c.students_count / c.MaxStudents) * 100, 1)}%" if c.MaxStudents and c.MaxStudents > 0 else "غير محددة"
        
    return render_template('academic/classes_pdf_report.html', classes=classes_list, generated_at=datetime.now().strftime('%Y-%m-%d %H:%M'))

@academic_bp.route('/classes/bulk-delete', methods=['POST'])
def bulk_delete_classes():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'الرجاء تسجيل الدخول أولاً'}), 401
    from flask import jsonify
    data = request.get_json() or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'message': 'لم يتم تحديد أي صف للحذف'}), 400
        
    # Student enrollment protection check!
    blocked_classes = []
    classes_to_delete = []
    
    for cid in ids:
        c = Classes.query.get(cid)
        if c:
            st_count = Student.query.filter_by(CID=c.CID, is_deleted=False).count()
            if st_count > 0:
                blocked_classes.append(c.CName)
            else:
                classes_to_delete.append(c)
                
    if blocked_classes:
        msg = f"تعذر حذف الصفوف التالية لاحتوائها على طلاب مسجلين: ({', '.join(blocked_classes)}). يرجى نقل الطلاب أولاً."
        return jsonify({'success': False, 'message': msg, 'blocked': True})
        
    for c in classes_to_delete:
        db.session.delete(c)
        
    db.session.commit()
    return jsonify({'success': True, 'message': f'تم حذف {len(classes_to_delete)} صفوف بنجاح', 'count': len(classes_to_delete)})

@academic_bp.route('/classes/bulk-status', methods=['POST'])
def bulk_status_classes():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'الرجاء تسجيل الدخول أولاً'}), 401
    from flask import jsonify
    data = request.get_json() or {}
    ids = data.get('ids', [])
    new_status = data.get('status', 'نشط')
    if not ids:
        return jsonify({'success': False, 'message': 'لم يتم تحديد أي صف لتحديث الحالة'}), 400
        
    classes_list = Classes.query.filter(Classes.CID.in_(ids)).all()
    for c in classes_list:
        if hasattr(c, 'Status'):
            c.Status = new_status
    db.session.commit()
    return jsonify({'success': True, 'message': f'تم تحديث حالة {len(classes_list)} صفوف إلى "{new_status}" بنجاح', 'count': len(classes_list)})

@academic_bp.route('/edit_subject/<int:id>', methods=['POST'])
def edit_subject(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    subject = Subject.query.get_or_404(id)
    name = request.form.get('name')
    sub_type = request.form.get('type')
    department = request.form.get('department')
    weekly_hours = request.form.get('weekly_hours', type=int) or 0
    status = request.form.get('status', 'نشط')
    color = request.form.get('color')
    class_ids = request.form.getlist('class_ids')
    
    if name:
        subject.SubName = name
        subject.Type = sub_type
        subject.Department = department
        subject.WeeklyHours = weekly_hours
        subject.Status = status
        if color:
            subject.Color = color
            
        if class_ids is not None:
            subject.classes = []
            if class_ids:
                target_classes = Classes.query.filter(Classes.CID.in_([int(cid) for cid in class_ids])).all()
                subject.classes.extend(target_classes)
                
        db.session.commit()
        flash('تم تحديث بيانات المادة بنجاح', 'success')
    return redirect(url_for('academic.subjects'))

@academic_bp.route('/delete_subject/<int:id>', methods=['POST'])
def delete_subject(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    subject = Subject.query.get_or_404(id)
    
    from models import SchoolTable
    slots_count = SchoolTable.query.filter_by(SubID=subject.SubID, is_deleted=False).count()
    
    if slots_count > 0:
        flash(f'تعذر حذف المادة "{subject.SubName}" لارتباطها بـ {slots_count} حصص في الجدول الأسبوعي.', 'danger')
        return redirect(url_for('academic.subjects'))
        
    if hasattr(subject, 'is_deleted'):
        subject.is_deleted = True
    else:
        db.session.delete(subject)
        
    db.session.commit()
    flash('تم حذف المادة بنجاح', 'success')
    return redirect(url_for('academic.subjects'))

@academic_bp.route('/subjects/export/excel')
def export_subjects_excel():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment
    import io
    from flask import send_file
    from models import SchoolTable
    from models.academic import TeacherSubject
    
    ids_param = request.args.get('ids', '').strip()
    query = Subject.query
    if hasattr(Subject, 'is_deleted'):
        query = query.filter_by(is_deleted=False)
        
    if ids_param:
        id_list = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
        subjects_list = query.filter(Subject.SubID.in_(id_list)).all()
    else:
        subjects_list = query.order_by(Subject.SubID.asc()).all()
        
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "قائمة المواد الدراسية"
    ws.sheet_view.rightToLeft = True
    
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    
    headers = ["كود المادة", "اسم المادة", "النوع", "القسم/المرحلة", "الحصص الأسبوعية", "الصفوف المرتبطة", "عدد المعلمين", "عدد الطلاب", "الحالة"]
    ws.append(headers)
    
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        
    for s in subjects_list:
        linked_cls = [c for c in s.classes if not getattr(c, 'is_deleted', False)]
        cls_names = ", ".join([c.CName for c in linked_cls]) or "جميع الصفوف"
        
        t_ids_ts = [t[0] for t in db.session.query(TeacherSubject.c.TeacherID).filter(TeacherSubject.c.SubID == s.SubID).distinct().all() if t[0]]
        t_ids_st = [t[0] for t in db.session.query(SchoolTable.TeacherID).filter(SchoolTable.SubID == s.SubID, SchoolTable.is_deleted == False).distinct().all() if t[0]]
        teachers_count = len(set(t_ids_ts + t_ids_st))
        
        class_ids = [c.CID for c in linked_cls]
        st_count = Student.query.filter(Student.CID.in_(class_ids), Student.is_deleted == False).count() if class_ids else 0
        
        row = [
            f"SUB-{s.SubID}",
            s.SubName,
            s.Type or 'أساسية',
            s.Department or 'جميع المراحل',
            getattr(s, 'WeeklyHours', 0) or 0,
            cls_names,
            teachers_count,
            st_count,
            getattr(s, 'Status', 'نشط') or 'نشط'
        ]
        ws.append(row)
        for cell in ws[ws.max_row]:
            cell.alignment = align_center
            
    for col in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I']:
        ws.column_dimensions[col].width = 22
        
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    return send_file(output, as_attachment=True, download_name='subjects_export.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@academic_bp.route('/subjects/export/pdf')
def export_subjects_pdf():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    from datetime import datetime
    from models import SchoolTable
    from models.academic import TeacherSubject
    
    ids_param = request.args.get('ids', '').strip()
    query = Subject.query
    if hasattr(Subject, 'is_deleted'):
        query = query.filter_by(is_deleted=False)
        
    if ids_param:
        id_list = [int(x) for x in ids_param.split(',') if x.strip().isdigit()]
        subjects_list = query.filter(Subject.SubID.in_(id_list)).all()
    else:
        subjects_list = query.order_by(Subject.SubID.asc()).all()
        
    for s in subjects_list:
        s.linked_classes = [c for c in s.classes if not getattr(c, 'is_deleted', False)]
        t_ids_ts = [t[0] for t in db.session.query(TeacherSubject.c.TeacherID).filter(TeacherSubject.c.SubID == s.SubID).distinct().all() if t[0]]
        t_ids_st = [t[0] for t in db.session.query(SchoolTable.TeacherID).filter(SchoolTable.SubID == s.SubID, SchoolTable.is_deleted == False).distinct().all() if t[0]]
        s.teachers_count = len(set(t_ids_ts + t_ids_st))
        class_ids = [c.CID for c in s.linked_classes]
        s.students_count = Student.query.filter(Student.CID.in_(class_ids), Student.is_deleted == False).count() if class_ids else 0
        s.weekly_slots_count = SchoolTable.query.filter(SchoolTable.SubID == s.SubID, SchoolTable.is_deleted == False).count()
        
    return render_template('academic/subjects_pdf_report.html', subjects=subjects_list, generated_at=datetime.now().strftime('%Y-%m-%d %H:%M'))

@academic_bp.route('/subjects/bulk-status', methods=['POST'])
def bulk_status_subjects():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'الرجاء تسجيل الدخول أولاً'}), 401
    from flask import jsonify
    data = request.get_json() or {}
    ids = data.get('ids', [])
    new_status = data.get('status', 'نشط')
    if not ids:
        return jsonify({'success': False, 'message': 'لم يتم تحديد أي مادة لتحديث الحالة'}), 400
        
    subjects_list = Subject.query.filter(Subject.SubID.in_(ids)).all()
    for s in subjects_list:
        if hasattr(s, 'Status'):
            s.Status = new_status
    db.session.commit()
    return jsonify({'success': True, 'message': f'تم تحديث حالة {len(subjects_list)} مواد إلى "{new_status}" بنجاح', 'count': len(subjects_list)})

@academic_bp.route('/subjects/bulk-delete', methods=['POST'])
def bulk_delete_subjects():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'الرجاء تسجيل الدخول أولاً'}), 401
    from flask import jsonify
    data = request.get_json() or {}
    ids = data.get('ids', [])
    if not ids:
        return jsonify({'success': False, 'message': 'لم يتم تحديد أي مادة للحذف'}), 400
        
    from models import SchoolTable
    blocked_subjects = []
    subjects_to_delete = []
    
    for sub_id in ids:
        s = Subject.query.get(sub_id)
        if s:
            slots_count = SchoolTable.query.filter_by(SubID=s.SubID, is_deleted=False).count()
            if slots_count > 0:
                blocked_subjects.append(s.SubName)
            else:
                subjects_to_delete.append(s)
                
    if blocked_subjects:
        msg = f"تعذر حذف المواد التالية لارتباطها بجدول الحصص الأسبوعي: ({', '.join(blocked_subjects)})."
        return jsonify({'success': False, 'message': msg, 'blocked': True})
        
    for s in subjects_to_delete:
        if hasattr(s, 'is_deleted'):
            s.is_deleted = True
        else:
            db.session.delete(s)
            
    db.session.commit()
    return jsonify({'success': True, 'message': f'تم حذف {len(subjects_to_delete)} مواد بنجاح', 'count': len(subjects_to_delete)})
