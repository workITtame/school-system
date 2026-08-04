from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, ExamSchedule, Subject, Classes, Sections, TypeExams, Student, Marks
from datetime import datetime, date
from utils.decorators import admin_required
from collections import defaultdict
from sqlalchemy import func

exams_bp = Blueprint('exams', __name__, url_prefix='/exams')

def get_teacher_exams_data():
    today_date = date.today()
    schedules = ExamSchedule.query.order_by(ExamSchedule.ExamDate.desc()).all()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    exam_types = TypeExams.query.all()

    # ─── status counts ───────────────────────────────────────────────
    total_exams     = len(schedules)
    active_exams    = sum(1 for s in schedules if s.Status in ['مفعل','نشطة','نشط','جارية'])
    upcoming_exams  = sum(1 for s in schedules if s.Status in ['مجدول','لم تبدأ بعد'])
    finished_exams  = sum(1 for s in schedules if s.Status in ['منتهي','منتهية','تم التصحيح'])
    corrected_exams = sum(1 for s in schedules if s.Status == 'تم التصحيح')
    pending_correction = sum(1 for s in schedules if s.Status in ['بانتظار التصحيح','غير مصحح'])
    cancelled_exams = sum(1 for s in schedules if s.Status in ['ملغى','ملغي'])

    # ─── marks stats ─────────────────────────────────────────────────
    all_marks = Marks.query.all()
    scores = [float(m.Score) for m in all_marks if m.Score is not None]
    avg_score   = round(sum(scores) / len(scores), 1) if scores else 0.0
    max_score   = round(max(scores), 1) if scores else 0.0
    min_score   = round(min(scores), 1) if scores else 0.0
    pass_marks  = [s for s in scores if s >= 50]
    fail_marks  = [s for s in scores if s < 50]
    pass_rate   = round((len(pass_marks) / len(scores) * 100), 1) if scores else 0.0
    fail_rate   = round((len(fail_marks) / len(scores) * 100), 1) if scores else 0.0

    # ─── subjects with exams ─────────────────────────────────────────
    subjects_with_exams = len(set(s.SubID for s in schedules if s.SubID)) or len(subjects)

    # ─── fill demo if DB empty ───────────────────────────────────────
    if total_exams == 0:
        total_exams = 24; active_exams = 8; upcoming_exams = 5
        finished_exams = 9; corrected_exams = 6; pending_correction = 3

    if not scores:
        avg_score=78.6; max_score=98.0; min_score=42.0
        pass_rate=72.4; fail_rate=27.6

    kpi = {
        'total_exams':      total_exams,
        'active_exams':     active_exams,
        'upcoming_exams':   upcoming_exams,
        'finished_exams':   finished_exams,
        'corrected_exams':  corrected_exams,
        'pending_correction': pending_correction,
        'avg_score':        avg_score,
        'max_score':        max_score,
        'min_score':        min_score,
        'pass_rate':        pass_rate,
        'fail_rate':        fail_rate,
        'subjects_count':   subjects_with_exams
    }

    # ─── current / latest exam ───────────────────────────────────────
    active_s = schedules[0] if schedules else None
    total_students_in_class = 0
    if active_s and active_s.CID:
        total_students_in_class = Student.query.filter_by(CID=active_s.CID).count()

    current_active_exam = {
        'name':          active_s.ExamName if (active_s and active_s.ExamName) else 'اختبار نهاية الفصل الثاني',
        'subject_name':  active_s.subject.SubName if (active_s and active_s.subject) else 'الرياضيات',
        'type':          'نهائي',
        'class_name':    active_s.school_class.CName if (active_s and active_s.school_class) else 'الثالث الثانوي',
        'section_name':  active_s.section.SectionName if (active_s and active_s.section) else 'شعبة أ',
        'term_name':     active_s.term.T_Name if (active_s and active_s.term) else 'الفصل الثاني',
        'academic_year': '2024 - 2025',
        'exam_date_str': active_s.ExamDate.strftime('%Y-%m-%d') if (active_s and active_s.ExamDate) else '2024-05-28',
        'start_time':    '09:00 AM',
        'end_time':      '11:00 AM',
        'max_mark':      '100 درجة',
        'pass_mark':     '50 درجة',
        'students_count': str(total_students_in_class or 28) + ' طالب'
    }

    # ─── status distribution for pie ─────────────────────────────────
    tot = float(total_exams or 1)
    status_distribution = {
        'active':        active_exams,
        'active_pct':    round(active_exams / tot * 100, 1),
        'finished':      finished_exams,
        'finished_pct':  round(finished_exams / tot * 100, 1),
        'upcoming':      upcoming_exams,
        'upcoming_pct':  round(upcoming_exams / tot * 100, 1),
        'cancelled':     cancelled_exams,
        'cancelled_pct': round(cancelled_exams / tot * 100, 1),
        'pending':       pending_correction,
        'pending_pct':   round(pending_correction / tot * 100, 1)
    }

    # ─── best subjects by avg score from Marks table ─────────────────
    sub_scores = defaultdict(list)
    for m in all_marks:
        if m.subject and m.Score is not None:
            sub_scores[m.subject.SubName].append(float(m.Score))

    best_subjects_by_score = []
    if sub_scores:
        max_avg = max(sum(v)/len(v) for v in sub_scores.values()) if sub_scores else 100
        for name, vals in sorted(sub_scores.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:5]:
            avg = round(sum(vals)/len(vals), 1)
            best_subjects_by_score.append({'name': name, 'score': avg, 'pct': round(avg/max_avg*100, 1)})

    if not best_subjects_by_score:
        best_subjects_by_score = [
            {'name': 'الرياضيات',       'score': 85.4, 'pct': 100.0},
            {'name': 'الفيزياء',         'score': 78.6, 'pct': 92.0},
            {'name': 'الكيمياء',         'score': 74.2, 'pct': 87.0},
            {'name': 'الأحياء',          'score': 71.8, 'pct': 84.0},
            {'name': 'اللغة الإنجليزية', 'score': 69.3, 'pct': 81.2}
        ]

    # ─── best students (highest avg score) ───────────────────────────
    stu_scores = defaultdict(list)
    for m in all_marks:
        if m.student and m.Score is not None:
            stu_scores[m.student.SName].append(float(m.Score))

    best_students = []
    for name, vals in sorted(stu_scores.items(), key=lambda x: sum(x[1])/len(x[1]), reverse=True)[:5]:
        best_students.append({'name': name, 'avg': round(sum(vals)/len(vals), 1)})

    if not best_students:
        best_students = [
            {'name': 'أحمد سعيد',     'avg': 95.2},
            {'name': 'فاطمة محمد',    'avg': 93.8},
            {'name': 'خالد العمري',   'avg': 91.5},
            {'name': 'مريم حسن',      'avg': 90.1},
            {'name': 'يوسف علي',      'avg': 88.7}
        ]

    # ─── struggling students (lowest avg score) ──────────────────────
    struggling_students = []
    for name, vals in sorted(stu_scores.items(), key=lambda x: sum(x[1])/len(x[1]))[:4]:
        avg = round(sum(vals)/len(vals), 1)
        if avg < 60:
            struggling_students.append({'name': name, 'avg': avg})

    if not struggling_students:
        struggling_students = [
            {'name': 'عمر صالح',   'avg': 38.4},
            {'name': 'لينا كريم',   'avg': 44.7},
            {'name': 'منى أحمد',   'avg': 47.2}
        ]

    # ─── upcoming exams list ─────────────────────────────────────────
    upcoming_exams_list = []
    for ex in schedules:
        if ex.ExamDate and ex.ExamDate >= today_date:
            delta = (ex.ExamDate - today_date).days
            if delta == 0:   rel_tag = 'اليوم'
            elif delta == 1: rel_tag = 'غداً'
            elif delta <= 6: rel_tag = f'بعد {delta} أيام'
            else:            rel_tag = ex.ExamDate.strftime('%Y-%m-%d')
            upcoming_exams_list.append({
                'title':    ex.ExamName or 'اختبار',
                'date_str': ex.ExamDate.strftime('%Y-%m-%d'),
                'rel_tag':  rel_tag,
                'subject':  ex.subject.SubName if ex.subject else ''
            })

    if not upcoming_exams_list:
        upcoming_exams_list = [
            {'title': 'اختبار الكيمياء التجريبي', 'date_str': '2024-06-03', 'rel_tag': 'بعد 6 أيام', 'subject': 'الكيمياء'},
            {'title': 'اختبار اللغة الإنجليزية',  'date_str': '2024-05-30', 'rel_tag': 'بعد 4 أيام', 'subject': 'اللغة الإنجليزية'},
            {'title': 'اختبار نهاية الفصل',         'date_str': '2024-05-28', 'rel_tag': 'غداً',        'subject': 'الرياضيات'}
        ]

    # ─── exams needing correction ────────────────────────────────────
    uncorrected_exams = [ex for ex in schedules if ex.Status in ['بانتظار التصحيح','غير مصحح','منتهي','منتهية']][:3]
    uncorrected_list = []
    for ex in uncorrected_exams:
        uncorrected_list.append({
            'title':   ex.ExamName or 'اختبار',
            'subject': ex.subject.SubName if ex.subject else ''
        })

    if not uncorrected_list:
        uncorrected_list = [
            {'title': 'اختبار الأحياء النصفي', 'subject': 'الأحياء'},
            {'title': 'اختبار التاريخ القصير',  'subject': 'التاريخ'}
        ]

    # ─── system alerts ───────────────────────────────────────────────
    system_alerts = []
    if pending_correction > 0:
        system_alerts.append({'type': 'warning', 'icon': 'fa-pen-to-square', 'title': f'هناك {pending_correction} اختبارات بانتظار التصحيح'})
    if upcoming_exams > 0:
        system_alerts.append({'type': 'info', 'icon': 'fa-calendar', 'title': f'اختبار الكيمياء التجريبي بعد 6 أيام'})
    system_alerts.append({'type': 'danger', 'icon': 'fa-circle-xmark', 'title': '2 اختبار منتهي لم يتم إغلاقه'})

    # ─── per-schedule student counts (for the table) ─────────────────
    for ex in schedules:
        ex._total_students = Student.query.filter_by(CID=ex.CID).count() if ex.CID else 0
        ex._present = ex._total_students   # simplification: all present
        ex._absent  = 0
        ex._avg     = avg_score
        ex._pass_pct = pass_rate

    return {
        'schedules':            schedules,
        'subjects':             subjects,
        'classes':              classes,
        'sections':             sections,
        'exam_types':           exam_types,
        'kpi':                  kpi,
        'current_active_exam':  current_active_exam,
        'status_distribution':  status_distribution,
        'best_subjects_by_score': best_subjects_by_score,
        'best_students':         best_students,
        'struggling_students':   struggling_students,
        'upcoming_exams_list':   upcoming_exams_list,
        'uncorrected_list':      uncorrected_list,
        'system_alerts':         system_alerts,
        'today':                 today_date.strftime('%Y-%m-%d')
    }


@exams_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    data = get_teacher_exams_data()

    return render_template('exams/index.html',
        schedules           = data['schedules'],
        subjects            = data['subjects'],
        classes             = data['classes'],
        sections            = data['sections'],
        exam_types          = data['exam_types'],
        kpi                 = data['kpi'],
        current_active_exam = data['current_active_exam'],
        status_distribution = data['status_distribution'],
        best_subjects_by_score = data['best_subjects_by_score'],
        best_students       = data['best_students'],
        struggling_students = data['struggling_students'],
        upcoming_exams_list = data['upcoming_exams_list'],
        uncorrected_list    = data['uncorrected_list'],
        system_alerts       = data['system_alerts'],
        today               = data['today'],
        total_exams         = data['kpi']['total_exams'],
        active_exams        = data['kpi']['active_exams'],
        upcoming_exams      = data['kpi']['upcoming_exams'],
        finished_exams      = data['kpi']['finished_exams']
    )


@exams_bp.route('/add', methods=['POST'])
@admin_required
def add_exam():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    sub_id    = request.form.get('sub_id')
    class_id  = request.form.get('class_id')
    exam_date = request.form.get('exam_date')
    exam_time = request.form.get('exam_time')
    exam_type = request.form.get('exam_type')
    status    = request.form.get('status', 'مجدول')

    if sub_id and class_id and exam_date and exam_time:
        try:
            date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            new_exam = ExamSchedule(
                SubID=sub_id, CID=class_id,
                ExamDate=date_obj, ExamTime=exam_time,
                ExamName=exam_type, Status=status
            )
            db.session.add(new_exam)
            db.session.commit()
            flash('تمت إضافة الاختبار بنجاح', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ: {str(e)}', 'danger')
    else:
        flash('جميع الحقول مطلوبة', 'warning')

    return redirect(url_for('exams.index'))


@exams_bp.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete_exam(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    exam = ExamSchedule.query.get_or_404(id)
    try:
        db.session.delete(exam)
        db.session.commit()
        flash('تم حذف الاختبار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
    return redirect(url_for('exams.index'))
