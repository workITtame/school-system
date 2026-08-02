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
    classes = Classes.query.all()
    sections = Sections.query.all()
    
    middle_school = sum(1 for c in classes if c.Stage == 'المتوسطة')
    high_school = sum(1 for c in classes if c.Stage == 'الثانوية')
    total_sections = len(sections)
    total_classes = len(classes)
    
    return render_template('academic/classes.html', 
                           classes=classes, 
                           sections=sections,
                           middle_school=middle_school,
                           high_school=high_school,
                           total_sections=total_sections,
                           total_classes=total_classes)

@academic_bp.route('/subjects')
def subjects():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    subjects = Subject.query.all()
    
    total_subjects = len(subjects)
    optional = sum(1 for s in subjects if s.Type == 'اختيارية')
    mandatory = sum(1 for s in subjects if s.Type == 'أساسية')
    
    return render_template('academic/subjects.html', 
                           subjects=subjects,
                           total_subjects=total_subjects,
                           optional=optional,
                           mandatory=mandatory)

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

# Subjects
@academic_bp.route('/edit_subject/<int:id>', methods=['POST'])
def edit_subject(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    s = Subject.query.get_or_404(id)
    name = request.form.get('name')
    sub_type = request.form.get('type')
    dept = request.form.get('department')
    status = request.form.get('status')
    if name: s.SubName = name
    if sub_type: s.Type = sub_type
    if dept: s.Department = dept
    if status: s.Status = status
    db.session.commit()
    flash('تم تعديل المادة الدراسية بنجاح', 'success')
    return redirect(url_for('academic.subjects'))

@academic_bp.route('/delete_subject/<int:id>', methods=['POST'])
def delete_subject(id):
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    s = Subject.query.get_or_404(id)
    timetable_count = SchoolTable.query.filter_by(SubID=id, is_deleted=False).count()
    exam_count = ExamSchedule.query.filter_by(SubID=id, is_deleted=False).count()
    if timetable_count > 0 or exam_count > 0:
        flash('لا يمكن حذف المادة الدراسية لأنها مرتبطة بجدول الحصص أو امتحانات مبرمجة.', 'danger')
        return redirect(url_for('academic.subjects'))
    handle_delete(s)
    return redirect(url_for('academic.subjects'))

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
