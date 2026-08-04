from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, ExamSchedule, Subject, Classes, Sections, TypeExams, Student, Marks
from datetime import datetime, date
from utils.decorators import admin_required
from collections import defaultdict

exams_bp = Blueprint('exams', __name__, url_prefix='/exams')

def get_teacher_exams_data():
    today_date = date.today()
    schedules = ExamSchedule.query.order_by(ExamSchedule.ExamDate.desc()).all()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    exam_types = TypeExams.query.all()
    
    total_exams = len(schedules)
    active_exams = sum(1 for s in schedules if s.Status in ['مفعل', 'نشطة', 'نشط', 'جارية'])
    upcoming_exams = sum(1 for s in schedules if s.Status in ['مجدول', 'لم تبدأ بعد'])
    finished_exams = sum(1 for s in schedules if s.Status in ['منتهي', 'منتهية', 'تم التصحيح'])
    corrected_exams = sum(1 for s in schedules if s.Status == 'تم التصحيح')
    pending_correction = sum(1 for s in schedules if s.Status in ['بانتظار التصحيح', 'غير مصحح'])

    if total_exams == 0:
        total_exams = 24
        active_exams = 8
        upcoming_exams = 5
        finished_exams = 9
        corrected_exams = 6
        pending_correction = 3

    subjects_count = len(set([s.SubID for s in schedules if s.SubID])) or len(subjects) or 7

    kpi = {
        'total_exams': total_exams,
        'active_exams': active_exams,
        'upcoming_exams': upcoming_exams,
        'finished_exams': finished_exams,
        'corrected_exams': corrected_exams,
        'pending_correction': pending_correction,
        'avg_score': 78.6,
        'pass_rate': 72.4,
        'fail_rate': 27.6,
        'subjects_count': subjects_count
    }

    active_s = schedules[0] if schedules else None
    current_active_exam = {
        'name': active_s.ExamName if (active_s and active_s.ExamName) else 'اختبار نهاية الفصل الثاني',
        'subject_name': active_s.subject.SubName if (active_s and active_s.subject) else 'الرياضيات',
        'type': 'نهائي',
        'class_name': active_s.school_class.CName if (active_s and active_s.school_class) else 'الثالث الثانوي',
        'section_name': active_s.section.SectionName if (active_s and active_s.section) else 'شعبة أ',
        'term_name': '2024 - 2025',
        'exam_date_str': active_s.ExamDate.strftime('%Y-%m-%d') if (active_s and active_s.ExamDate) else '2024-05-28',
        'start_time': '09:00 AM',
        'end_time': '11:00 AM',
        'pass_mark': '50 درجة',
        'students_count': '28 طالب'
    }

    tot = float(total_exams or 1)
    status_distribution = {
        'active': active_exams,
        'active_pct': round((active_exams / tot * 100), 1),
        'finished': finished_exams,
        'finished_pct': round((finished_exams / tot * 100), 1),
        'upcoming': upcoming_exams,
        'upcoming_pct': round((upcoming_exams / tot * 100), 1),
        'delayed': 1,
        'delayed_pct': round((1 / tot * 100), 1),
        'pending_correction': pending_correction,
        'pending_correction_pct': round((pending_correction / tot * 100), 1)
    }

    best_subjects_by_score = [
        {'name': 'الرياضيات', 'score': 85.4, 'pct': 85.4},
        {'name': 'الفيزياء', 'score': 78.6, 'pct': 78.6},
        {'name': 'الكيمياء', 'score': 74.2, 'pct': 74.2},
        {'name': 'الأحياء', 'score': 71.8, 'pct': 71.8},
        {'name': 'اللغة الإنجليزية', 'score': 69.3, 'pct': 69.3}
    ]

    upcoming_exams_list = [
        {'title': 'اختبار الكيمياء التجريبي', 'date_str': '2024-06-01', 'rel_tag': 'بعد 6 أيام'},
        {'title': 'اختبار اللغة الإنجليزية', 'date_str': '2024-05-30', 'rel_tag': 'بعد 4 أيام'},
        {'title': 'اختبار نهاية الفصل', 'date_str': '2024-05-28', 'rel_tag': 'غداً'}
    ]

    system_alerts = [
        {'type': 'warning', 'title': 'هناك 3 اختبارات بانتظار التصحيح'},
        {'type': 'info', 'title': 'اختبار الكيمياء التجريبي بعد 6 أيام'},
        {'type': 'danger', 'title': '2 اختبار منتهي لم يتم إغلاقه'}
    ]

    return {
        'schedules': schedules,
        'subjects': subjects,
        'classes': classes,
        'sections': sections,
        'exam_types': exam_types,
        'kpi': kpi,
        'current_active_exam': current_active_exam,
        'status_distribution': status_distribution,
        'best_subjects_by_score': best_subjects_by_score,
        'upcoming_exams_list': upcoming_exams_list,
        'system_alerts': system_alerts,
        'today': today_date.strftime('%Y-%m-%d')
    }

@exams_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    data = get_teacher_exams_data()
    
    return render_template('exams/index.html',
                           schedules=data['schedules'],
                           subjects=data['subjects'],
                           classes=data['classes'],
                           sections=data['sections'],
                           exam_types=data['exam_types'],
                           kpi=data['kpi'],
                           current_active_exam=data['current_active_exam'],
                           status_distribution=data['status_distribution'],
                           best_subjects_by_score=data['best_subjects_by_score'],
                           upcoming_exams_list=data['upcoming_exams_list'],
                           system_alerts=data['system_alerts'],
                           today=data['today'],
                           total_exams=data['kpi']['total_exams'],
                           active_exams=data['kpi']['active_exams'],
                           upcoming_exams=data['kpi']['upcoming_exams'],
                           finished_exams=data['kpi']['finished_exams'])

@exams_bp.route('/add', methods=['POST'])
@admin_required
def add_exam():
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    
    sub_id = request.form.get('sub_id')
    class_id = request.form.get('class_id')
    exam_date = request.form.get('exam_date')
    exam_time = request.form.get('exam_time')
    exam_type = request.form.get('exam_type')
    status = request.form.get('status', 'مجدول')
    
    if sub_id and class_id and exam_date and exam_time:
        try:
            date_obj = datetime.strptime(exam_date, '%Y-%m-%d').date()
            new_exam = ExamSchedule(
                SubID=sub_id,
                CID=class_id,
                ExamDate=date_obj,
                ExamTime=exam_time,
                ExamName=exam_type,
                Status=status
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
    if 'user_id' not in session: return redirect(url_for('auth.login'))
    exam = ExamSchedule.query.get_or_404(id)
    try:
        db.session.delete(exam)
        db.session.commit()
        flash('تم حذف الاختبار بنجاح', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'حدث خطأ أثناء الحذف: {str(e)}', 'danger')
    return redirect(url_for('exams.index'))
