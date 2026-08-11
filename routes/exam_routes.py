import logging
from datetime import date, datetime
from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_required, current_user
from sqlalchemy.orm import joinedload
from models import db, Subject, Classes, Sections, Student, SchoolTable, Teacher, ExamSchedule, Terms, Marks
from services.teacher_exam_service import (
    get_teacher_exam_statistics,
    get_teacher_exams,
    get_exam_details,
    create_exam,
    update_exam,
    publish_exam,
    close_exam,
    duplicate_exam,
    soft_delete_exam,
    restore_exam,
    get_exam_students,
    get_exam_results,
    get_exam_statistics
)

logger = logging.getLogger(__name__)

exam_bp = Blueprint('exams', __name__, url_prefix='/exams')
exams_bp = exam_bp

def _get_teacher_subjects_classes_sections(user_id):
    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return [], [], []

    slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    sub_ids = {s.SubID for s in slots if s.SubID}
    cls_ids = {s.CID for s in slots if s.CID}
    sec_ids = {s.SectionID for s in slots if s.SectionID}

    if teacher and hasattr(teacher, 'subjects') and teacher.subjects:
        for s in teacher.subjects:
            if hasattr(s, 'SubID'): sub_ids.add(s.SubID)

    subjects = Subject.query.filter(Subject.SubID.in_(list(sub_ids)), Subject.is_deleted == False).all() if sub_ids else []
    classes = Classes.query.filter(Classes.CID.in_(list(cls_ids)), Classes.is_deleted == False).all() if cls_ids else []
    sections = Sections.query.filter(Sections.SectionID.in_(list(sec_ids)), Sections.is_deleted == False).all() if sec_ids else []

    return subjects, classes, sections

@exam_bp.route('/', methods=['GET'])
@login_required
def index():
    user_role = getattr(current_user, 'role', '').strip("'") if current_user and hasattr(current_user, 'role') else None
    
    if user_role == 'teacher':
        user_id = current_user.id
        subject_id = request.args.get('subject_id')
        class_id = request.args.get('class_id')
        section_id = request.args.get('section_id')
        status = request.args.get('status')
        search = request.args.get('search')
        page = request.args.get('page', 1, type=int)

        subjects, classes, sections = _get_teacher_subjects_classes_sections(user_id)
        kpi_stats = get_teacher_exam_statistics(user_id)

        try:
            exams_data = get_teacher_exams(
                user_id=user_id,
                subject_id=subject_id,
                class_id=class_id,
                section_id=section_id,
                status=status,
                search=search,
                page=page,
                per_page=10
            )
        except Exception as e:
            logger.error(f"Error fetching teacher exams: {e}")
            exams_data = {'items': [], 'total': 0, 'page': 1, 'per_page': 10, 'total_pages': 1}

        teacher = Teacher.query.filter_by(user_id=user_id).first()

        return render_template(
            'teacher/exams.html',
            kpi=kpi_stats,
            exam_list=exams_data['items'],
            pagination=exams_data,
            subjects=subjects,
            classes=classes,
            sections=sections,
            teacher_info=teacher,
            today=date.today().strftime('%Y-%m-%d')
        )

    # ══════════════════════════════════════════════════════
    # ADMIN / SYSTEM MANAGER VIEW (exams/index.html)
    # ══════════════════════════════════════════════════════
    schedules = ExamSchedule.query.options(
        joinedload(ExamSchedule.subject),
        joinedload(ExamSchedule.school_class),
        joinedload(ExamSchedule.section),
        joinedload(ExamSchedule.term)
    ).filter(ExamSchedule.is_deleted == False).all()

    today_str = date.today().strftime('%Y-%m-%d')
    today_date = date.today()

    for ex in schedules:
        st_count = Student.query.filter_by(CID=ex.CID, is_deleted=False).count() if ex.CID else 0
        ex._total_students = st_count
        
        exam_marks = Marks.query.filter(
            Marks.assessment_type == 'exam',
            (Marks.ExamID == ex.ScheduleID) | (Marks.assessment_id == ex.ScheduleID)
        ).all()
            
        scores = [float(m.Score) for m in exam_marks if m.Score is not None]
        ex._present = len(scores)
        ex._absent = max(0, st_count - len(scores)) if (len(scores) > 0 or (ex.Status or '') in ['تم التصحيح', 'منتهي', 'منشور', 'مكتمل', 'بانتظار التصحيح']) else 0
        ex._avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        ex._pass_pct = round((sum(1 for s in scores if s >= 60) / len(scores)) * 100, 1) if scores else 0.0

    total_exams = len(schedules)
    active_exams = sum(1 for ex in schedules if (ex.Status or '') in ['نشط', 'نشطة', 'جارية', 'مفعل'])
    upcoming_exams = sum(1 for ex in schedules if (ex.Status or '') in ['مجدول', 'لم تبدأ بعد'])
    finished_exams = sum(1 for ex in schedules if (ex.Status or '') in ['منتهي', 'منتهية', 'تم التصحيح', 'مكتمل', 'منشور'])
    corrected_exams = sum(1 for ex in schedules if (ex.Status or '') in ['تم التصحيح', 'منشور', 'منتهي', 'مكتمل'] or getattr(ex, '_present', 0) > 0)
    pending_correction = sum(1 for ex in schedules if (ex.Status or '') in ['بانتظار التصحيح', 'غير مصحح'] and getattr(ex, '_present', 0) == 0)

    # Aggregate overall score KPIs directly from all recorded exam marks
    overall_marks = Marks.query.filter(
        Marks.assessment_type == 'exam',
        Marks.Score.isnot(None)
    ).all()
    scores = [float(m.Score) for m in overall_marks if m.Score is not None]

    if scores:
        avg_score = round(sum(scores) / len(scores), 1)
        max_score = max(scores)
        min_score = min(scores)
        pass_count = sum(1 for s in scores if s >= 60)
        pass_rate = round((pass_count / len(scores)) * 100, 1)
        fail_rate = round(100.0 - pass_rate, 1)
    else:
        avg_score, max_score, min_score, pass_rate, fail_rate = 0.0, 0.0, 0.0, 0.0, 0.0

    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    terms = Terms.query.filter_by(is_deleted=False).all()
    active_term_name = terms[0].T_Name if terms else 'الفصل الدراسي'

    kpi = {
        'total_exams': total_exams,
        'active_exams': active_exams,
        'upcoming_exams': upcoming_exams,
        'finished_exams': finished_exams,
        'corrected_exams': corrected_exams,
        'pending_correction': pending_correction,
        'avg_score': avg_score,
        'pass_rate': pass_rate,
        'fail_rate': fail_rate,
        'max_score': max_score,
        'min_score': min_score,
        'subjects_count': len(subjects)
    }

    active_sched = next((s for s in schedules if (s.Status or '') in ['نشط', 'نشطة', 'جارية']), None)
    if active_sched:
        act_type = 'شهري' if 'شهري' in (active_sched.ExamName or '') else ('نصفي' if ('نصف' in (active_sched.ExamName or '') or 'فصل' in (active_sched.ExamName or '')) else ('نهائي' if 'نهائي' in (active_sched.ExamName or '') else (active_sched.ExamName or 'اختبار')))
        term_label = active_sched.term.T_Name if getattr(active_sched, 'term', None) else active_term_name
        current_active_exam = {
            'name': active_sched.ExamName or 'اختبار المواد الأساسية',
            'subject_name': active_sched.subject.SubName if active_sched.subject else 'عام',
            'type': act_type,
            'class_name': active_sched.school_class.CName if active_sched.school_class else 'جميع الصفوف',
            'section_name': active_sched.section.SectionName if active_sched.section else 'جميع الشعب',
            'term_name': term_label,
            'academic_year': '2025 - 2026',
            'exam_date_str': active_sched.ExamDate.strftime('%Y-%m-%d') if active_sched.ExamDate else today_str,
            'start_time': active_sched.ExamTime or '09:00',
            'end_time': '11:00',
            'pass_mark': 50,
            'students_count': getattr(active_sched, '_total_students', 0)
        }
    else:
        current_active_exam = None

    tot = total_exams if total_exams > 0 else 1
    status_distribution = {
        'active': active_exams,
        'active_pct': round((active_exams / tot) * 100, 1) if total_exams > 0 else 0.0,
        'finished': finished_exams,
        'finished_pct': round((finished_exams / tot) * 100, 1) if total_exams > 0 else 0.0,
        'upcoming': upcoming_exams,
        'upcoming_pct': round((upcoming_exams / tot) * 100, 1) if total_exams > 0 else 0.0,
        'cancelled': 0,
        'cancelled_pct': 0.0,
        'pending': pending_correction,
        'pending_pct': round((pending_correction / tot) * 100, 1) if total_exams > 0 else 0.0
    }

    # Dynamic Best Subjects by Score
    best_subjects_by_score = []
    if overall_marks:
        try:
            from sqlalchemy import func
            subject_marks = db.session.query(
                Subject.SubName,
                func.avg(Marks.Score).label('avg_score')
            ).join(Marks, Subject.SubID == Marks.SubID)\
             .filter(Marks.assessment_type == 'exam', Marks.Score.isnot(None))\
             .group_by(Subject.SubID, Subject.SubName)\
             .order_by(func.avg(Marks.Score).desc()).limit(5).all()

            for s_name, s_avg in subject_marks:
                val = round(float(s_avg), 1)
                best_subjects_by_score.append({
                    'name': s_name,
                    'score': str(val),
                    'pct': min(100.0, val)
                })
        except Exception as e:
            logger.error(f"Error querying subject averages: {e}")

    # Dynamic Best & Struggling Students
    best_students = []
    struggling_students = []
    if overall_marks:
        try:
            from sqlalchemy import func
            student_scores = db.session.query(
                Student.SName,
                func.avg(Marks.Score).label('avg_score')
            ).join(Marks, Student.SID == Marks.SID).filter(Student.is_deleted == False, Marks.assessment_type == 'exam', Marks.Score.isnot(None)).group_by(Student.SID, Student.SName).having(func.count(Marks.M_ID) > 0).all()

            if student_scores:
                sorted_st = sorted(student_scores, key=lambda x: float(x[1]), reverse=True)
                for name, avg in sorted_st[:5]:
                    val = round(float(avg), 1)
                    best_students.append({'name': name, 'avg': f"{val}%"})
                
                struggling = [st for st in sorted_st if float(st[1]) < 60]
                for name, avg in struggling[:5]:
                    val = round(float(avg), 1)
                    struggling_students.append({'name': name, 'avg': f"{val}%"})
        except Exception as e:
            logger.error(f"Error querying student rankings: {e}")

    # Dynamic Upcoming and Uncorrected Exams
    upcoming_exams_list = []
    uncorrected_list = []
    for ex in schedules:
        sub_name = ex.subject.SubName if ex.subject else 'مادة'
        if ex.ExamDate and ex.ExamDate >= today_date:
            rel = 'اليوم' if ex.ExamDate == today_date else (ex.ExamDate.strftime('%Y-%m-%d'))
            upcoming_exams_list.append({
                'title': ex.ExamName or f"اختبار {sub_name}",
                'date_str': ex.ExamDate.strftime('%Y-%m-%d'),
                'subject': sub_name,
                'rel_tag': rel
            })
        if (ex.Status or '') in ['بانتظار التصحيح', 'لم يصحح']:
            uncorrected_list.append({
                'title': ex.ExamName or f"اختبار {sub_name}",
                'subject': sub_name
            })

    # Dynamic System Alerts
    system_alerts = []
    if pending_correction > 0:
        system_alerts.append({
            'type': 'warning',
            'icon': 'fa-triangle-exclamation',
            'title': f"يوجد {pending_correction} اختبارات بانتظار الاعتماد والتصحيح"
        })

    return render_template(
        'exams/index.html',
        kpi=kpi,
        current_active_exam=current_active_exam,
        subjects=subjects,
        classes=classes,
        sections=sections,
        terms=terms,
        schedules=schedules,
        status_distribution=status_distribution,
        best_subjects_by_score=best_subjects_by_score,
        best_students=best_students,
        struggling_students=struggling_students,
        upcoming_exams_list=upcoming_exams_list,
        uncorrected_list=uncorrected_list,
        system_alerts=system_alerts,
        today=today_str,
        active_term_name=active_term_name
    )

def _check_teacher_exam_scope(user_id, class_id=None, sub_id=None, sched=None):
    from models import User, Teacher, SchoolTable
    user = User.query.get(user_id)
    if user and getattr(user, 'role', '') == 'admin':
        return True
    if user and getattr(user, 'role', '') == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        if not teacher:
            teacher = Teacher.query.filter_by(Email=user.username).first()
        if not teacher:
            return False
        slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
        cls_ids = {s.CID for s in slots if s.CID}
        sub_ids = {s.SubID for s in slots if s.SubID}
        if hasattr(teacher, 'subjects') and teacher.subjects:
            for s in teacher.subjects:
                if hasattr(s, 'SubID'): sub_ids.add(s.SubID)

        if sched:
            if sched.CID and sched.CID not in cls_ids:
                return False
            if sched.SubID and sched.SubID not in sub_ids:
                return False
        if class_id and class_id not in cls_ids:
            return False
        if sub_id and sub_id not in sub_ids:
            return False
        return True
    return False

@exam_bp.route('/add', methods=['POST'])
@exam_bp.route('/create', methods=['POST'])
@login_required
def add_exam():
    exam_type = request.form.get('exam_type') or request.form.get('title')
    sub_id = request.form.get('sub_id', type=int)
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)
    exam_date_str = request.form.get('exam_date')
    exam_time = request.form.get('exam_time', '09:00 - 11:00')
    status = request.form.get('status', 'مجدول')
    duration = request.form.get('duration', 60, type=int)

    t_id = request.form.get('t_id', type=int)
    location = request.form.get('location')

    if not exam_type:
        flash('يرجى إدخال اسم أو نوع الاختبار', 'warning')
        return redirect(url_for('exams.index'))

    if not sub_id or not class_id:
        flash('يرجى تحديد المادة والصف الدراسي', 'warning')
        return redirect(url_for('exams.index'))

    user_role = session.get('user_role') or getattr(current_user, 'role', '')
    user_id = session.get('user_id') or (current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None)
    if user_role == 'teacher' and user_id:
        if not _check_teacher_exam_scope(user_id, class_id=class_id, sub_id=sub_id):
            return jsonify({'error': 'Out-of-scope exam creation forbidden'}), 403

    try:
        exam_date = datetime.strptime(exam_date_str, '%Y-%m-%d').date() if exam_date_str else date.today()
        
        # Check duplicate
        existing = ExamSchedule.query.filter_by(ExamName=exam_type, SubID=sub_id, CID=class_id, ExamDate=exam_date).first()
        if existing:
            flash(f'الاختبار "{exam_type}" مجدول بالفعل لنفس المادة والصف في هذا التاريخ', 'warning')
            return redirect(url_for('exams.index'))

        new_sched = ExamSchedule(
            ExamName=exam_type,
            SubID=sub_id,
            CID=class_id,
            SectionID=section_id if section_id else None,
            T_ID=t_id if t_id else None,
            Location=location if location else None,
            ExamDate=exam_date,
            ExamTime=exam_time,
            Duration=duration,
            Status=status
        )
        db.session.add(new_sched)
        db.session.commit()
        flash('تم إضافة الاختبار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error adding exam: {e}")
        flash(f'حدث خطأ عند إضافة الاختبار: {e}', 'danger')

    return redirect(url_for('exams.index'))

@exam_bp.route('/edit/<int:id>', methods=['POST'])
@login_required
def edit_exam(id):
    sched = ExamSchedule.query.get(id)
    if not sched:
        flash('الاختبار غير موجود', 'warning')
        return redirect(url_for('exams.index'))

    user_role = session.get('user_role') or getattr(current_user, 'role', '')
    user_id = session.get('user_id') or (current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None)
    if user_role == 'teacher' and user_id:
        if not _check_teacher_exam_scope(user_id, sched=sched):
            return jsonify({'error': 'Out-of-scope exam modification forbidden'}), 403

    exam_type = request.form.get('exam_type') or request.form.get('title')
    sub_id = request.form.get('sub_id', type=int)
    class_id = request.form.get('class_id', type=int)
    section_id = request.form.get('section_id', type=int)
    exam_date_str = request.form.get('exam_date')
    exam_time = request.form.get('exam_time')
    status = request.form.get('status')
    duration = request.form.get('duration', type=int)

    t_id = request.form.get('t_id', type=int)
    location = request.form.get('location')

    if exam_type: sched.ExamName = exam_type
    if sub_id: sched.SubID = sub_id
    if class_id: sched.CID = class_id
    if section_id is not None: sched.SectionID = section_id if section_id else None
    if t_id is not None: sched.T_ID = t_id if t_id else None
    if location is not None: sched.Location = location if location else None
    if exam_time: sched.ExamTime = exam_time
    if status: sched.Status = status
    if duration: sched.Duration = duration
    if exam_date_str:
        try:
            sched.ExamDate = datetime.strptime(exam_date_str, '%Y-%m-%d').date()
        except ValueError:
            pass

    try:
        db.session.commit()
        flash('تم تحديث بيانات الاختبار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error editing exam: {e}")
        flash(f'حدث خطأ أثناء تعديل الاختبار: {e}', 'danger')

    return redirect(url_for('exams.index'))

@exam_bp.route('/publish/<int:id>', methods=['POST'])
@login_required
def publish_exam_route(id):
    sched = ExamSchedule.query.get(id)
    if not sched:
        flash('الاختبار غير موجود', 'warning')
        return redirect(url_for('exams.index'))

    user_role = session.get('user_role') or getattr(current_user, 'role', '')
    user_id = session.get('user_id') or (current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None)
    if user_role == 'teacher' and user_id:
        if not _check_teacher_exam_scope(user_id, sched=sched):
            return jsonify({'error': 'Out-of-scope exam publish forbidden'}), 403

    sched.Status = 'منشور'
    try:
        db.session.commit()
        flash('تم نشر الاختبار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {e}', 'danger')
    return redirect(url_for('exams.index'))

@exam_bp.route('/close/<int:id>', methods=['POST'])
@login_required
def close_exam_route(id):
    sched = ExamSchedule.query.get(id)
    if not sched:
        flash('الاختبار غير موجود', 'warning')
        return redirect(url_for('exams.index'))

    user_role = session.get('user_role') or getattr(current_user, 'role', '')
    user_id = session.get('user_id') or (current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None)
    if user_role == 'teacher' and user_id:
        if not _check_teacher_exam_scope(user_id, sched=sched):
            return jsonify({'error': 'Out-of-scope exam close forbidden'}), 403

    sched.Status = 'منتهي'
    try:
        db.session.commit()
        flash('تم إغلاق الاختبار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ: {e}', 'danger')
    return redirect(url_for('exams.index'))

@exam_bp.route('/duplicate/<int:id>', methods=['POST'])
@login_required
def duplicate_exam_route(id):
    sched = ExamSchedule.query.get(id)
    if not sched:
        flash('الاختبار غير موجود', 'warning')
        return redirect(url_for('exams.index'))

    user_role = session.get('user_role') or getattr(current_user, 'role', '')
    user_id = session.get('user_id') or (current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None)
    if user_role == 'teacher' and user_id:
        if not _check_teacher_exam_scope(user_id, sched=sched):
            return jsonify({'error': 'Out-of-scope exam duplicate forbidden'}), 403

    try:
        dup = ExamSchedule(
            ExamName=f"نسخة - {sched.ExamName}",
            SubID=sched.SubID,
            CID=sched.CID,
            SectionID=sched.SectionID,
            ExamDate=date.today(),
            ExamTime=sched.ExamTime,
            Duration=sched.Duration,
            Status='مجدول'
        )
        db.session.add(dup)
        db.session.commit()
        flash('تم تكرار الاختبار بنجاح بدون نسخ درجات الطلاب', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء نسخ الاختبار: {e}', 'danger')
    return redirect(url_for('exams.index'))

@exam_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete_exam(id):
    sched = ExamSchedule.query.get(id)
    if not sched:
        flash('الاختبار غير موجود', 'warning')
        return redirect(url_for('exams.index'))

    user_role = session.get('user_role') or getattr(current_user, 'role', '')
    user_id = session.get('user_id') or (current_user.id if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else None)
    if user_role == 'teacher' and user_id:
        if not _check_teacher_exam_scope(user_id, sched=sched):
            return jsonify({'error': 'Out-of-scope exam deletion forbidden'}), 403

    try:
        from models.grade import Marks, DetailMarks
        Marks.query.filter(
            Marks.assessment_type == 'exam',
            (Marks.ExamID == id) | (Marks.assessment_id == id)
        ).delete(synchronize_session=False)
        DetailMarks.query.filter(
            DetailMarks.assessment_type == 'exam',
            (DetailMarks.ExamID == id) | (DetailMarks.assessment_id == id)
        ).delete(synchronize_session=False)

        db.session.delete(sched)
        db.session.commit()
        flash('تم حذف الاختبار والدرجات المرتبطة به بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting exam: {e}")
        flash(f'حدث خطأ عند حذف الاختبار: {e}', 'danger')

    return redirect(url_for('exams.index'))

@exam_bp.route('/api/list', methods=['GET'])
@login_required
def api_list():
    user_id = current_user.id
    subject_id = request.args.get('subject_id')
    class_id = request.args.get('class_id')
    section_id = request.args.get('section_id')
    status = request.args.get('status')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)

    try:
        data = get_teacher_exams(
            user_id=user_id,
            subject_id=subject_id,
            class_id=class_id,
            section_id=section_id,
            status=status,
            search=search,
            page=page,
            per_page=10
        )
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Unauthorized teacher access'}), 403
    except Exception as e:
        logger.error(f"API List error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/details/<int:exam_id>', methods=['GET'])
@login_required
def api_details(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        data = get_exam_details(exam_id, current_user.id)
        if not data:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify(data)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Details error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/students/<int:exam_id>', methods=['GET'])
@login_required
def api_students(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        students = get_exam_students(exam_id, current_user.id)
        return jsonify(students)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Students error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/results/<int:exam_id>', methods=['GET'])
@login_required
def api_results(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        results = get_exam_results(exam_id, current_user.id)
        return jsonify(results)
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Results error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/create', methods=['POST'])
@login_required
def api_create():
    payload = request.get_json() or request.form
    try:
        exam_id = create_exam(current_user.id, payload)
        return jsonify({'success': True, 'id': exam_id, 'message': 'تم إنشاء الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Create error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/update/<int:exam_id>', methods=['POST'])
@login_required
def api_update(exam_id):
    payload = request.get_json() or request.form
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        success = update_exam(exam_id, current_user.id, payload)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم تحديث البيانات بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Update error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/publish/<int:exam_id>', methods=['POST'])
@login_required
def api_publish(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        success = publish_exam(exam_id, current_user.id)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم نشر الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Publish error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/close/<int:exam_id>', methods=['POST'])
@login_required
def api_close(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        success = close_exam(exam_id, current_user.id)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم إغلاق الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Close error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/duplicate/<int:exam_id>', methods=['POST'])
@login_required
def api_duplicate(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        dup_id = duplicate_exam(exam_id, current_user.id)
        if not dup_id:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'id': dup_id, 'message': 'تم نسخ الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Duplicate error: {e}")
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/restore/<int:exam_id>', methods=['POST'])
@login_required
def api_restore(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        success = restore_exam(exam_id, current_user.id)
        return jsonify({'success': True, 'message': 'تم استعادة الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@exam_bp.route('/api/delete/<int:exam_id>', methods=['DELETE', 'POST'])
@login_required
def api_delete(exam_id):
    try:
        sched = ExamSchedule.query.get(exam_id)
        if not sched:
            return jsonify({'error': 'Exam not found'}), 404
        success = soft_delete_exam(exam_id, current_user.id)
        if not success:
            return jsonify({'error': 'Exam not found'}), 404
        return jsonify({'success': True, 'message': 'تم حذف الاختبار بنجاح'})
    except PermissionError:
        return jsonify({'error': 'Out-of-scope access forbidden'}), 403
    except Exception as e:
        logger.error(f"API Delete error: {e}")
        return jsonify({'error': str(e)}), 500
