from flask import Blueprint, render_template, request, make_response, send_file, current_app, jsonify
from routes.auth_routes import login_required
from models import db, Student, Classes, Sections, Marks, TypeExams, Subject, Terms, Teacher, Attendance, Homework
from models.extensions import cache
from utils.pdf_generator import generate_student_pdf
import io
import os

import openpyxl
from openpyxl.styles import Font, Alignment, PatternFill

reports_bp = Blueprint('reports', __name__)

@reports_bp.route("/reports")
@login_required
def index():
    from services.reports import get_reports_dashboard_metrics, get_reports_registry
    
    metrics = get_reports_dashboard_metrics()
    reports = get_reports_registry()
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    subjects = Subject.query.filter_by(is_deleted=False).all()
    terms = Terms.query.filter_by(is_deleted=False).all()
    students = Student.query.filter_by(is_deleted=False).order_by(Student.SName).all()
    
    recent_reports = [
        {"id": 1, "title": "كشف درجات الفصل الثاني", "type": "كشف درجات صف", "class_name": "الثالث الثانوي / الشعبة أ", "subject_name": "الرياضيات", "created_at": "2024-05-26 10:30 AM", "author": "أ. سمير غانم", "status": "مكتمل"},
        {"id": 2, "title": "تقرير أداء طلاب الفصل الثاني", "type": "تقرير الأداء الأكاديمي", "class_name": "الثالث الثانوي / الشعبة أ", "subject_name": "الرياضيات", "created_at": "2024-05-25 08:45 AM", "author": "أ. سمير غانم", "status": "مكتمل"},
        {"id": 3, "title": "تقرير الحضور والغياب", "type": "تقرير الحضور والغياب", "class_name": "الثالث الثانوي / الشعبة أ", "subject_name": "الرياضيات", "created_at": "2024-05-24 11:20 AM", "author": "أ. سمير غانم", "status": "مكتمل"},
        {"id": 4, "title": "نتائج الاختبار النهائي", "type": "تقرير الاختبارات", "class_name": "الثالث الثانوي / الشعبة أ", "subject_name": "الرياضيات", "created_at": "2024-05-23 02:15 PM", "author": "أ. سمير غانم", "status": "مكتمل"},
        {"id": 5, "title": "تقرير المتفوقين", "type": "تقرير المتفوقين", "class_name": "الثالث الثانوي", "subject_name": "جميع المواد", "created_at": "2024-05-22 09:10 AM", "author": "أ. سمير غانم", "status": "مكتمل"}
    ]

    return render_template("reports/index.html", 
                           metrics=metrics, 
                           reports=reports,
                           classes=classes,
                           sections=sections,
                           subjects=subjects,
                           terms=terms,
                           students=students,
                           recent_reports=recent_reports)

@reports_bp.route("/reports/analytics")
@login_required
def analytics():
    from services.reports import get_reports_dashboard_metrics
    metrics = get_reports_dashboard_metrics()
    return render_template("reports/analytics.html", metrics=metrics)

@reports_bp.route("/reports/student")
@login_required
def student_report():
    classes = Classes.query.filter_by(is_deleted=False).all()
    sections = Sections.query.filter_by(is_deleted=False).all()
    
    sel_class_id = request.args.get('class_id', type=int)
    sel_section_id = request.args.get('section_id', type=int)
    sel_student_id = request.args.get('student_id')
    
    query = Student.query.filter_by(is_deleted=False)
    if sel_class_id:
        query = query.filter_by(CID=sel_class_id)
    if sel_section_id:
        query = query.filter_by(SectionID=sel_section_id)
    students = query.order_by(Student.SName).all()
        
    selected_student = None
    report_data = None
    average = 0
    
    if sel_student_id:
        try:
            s_id = int(sel_student_id)
            selected_student = Student.query.get(s_id)
        except (ValueError, TypeError):
            selected_student = None

        if selected_student:
            marks = Marks.query.filter_by(SID=selected_student.SID).all()
            report_data = {}
            total_score = 0
            count = 0
            for mark in marks:
                exam_name = "امتحان الفصل الدراسي"
                if hasattr(mark, 'exam') and mark.exam:
                    exam_name = mark.exam.ExamName
                elif mark.ExamID:
                    ex_obj = TypeExams.query.get(mark.ExamID)
                    if ex_obj: exam_name = ex_obj.ExamName

                sub_name = mark.subject.SubName if mark.subject else "مادة دراسية"
                score_val = float(mark.Score) if mark.Score is not None else 0.0

                grade_item = {
                    'subject_name': sub_name,
                    'score': score_val,
                    'grade_symbol': mark.Grade or '—',
                    'notes': mark.Notes or ''
                }

                if exam_name not in report_data:
                    report_data[exam_name] = []
                report_data[exam_name].append(grade_item)
                if mark.Score is not None:
                    total_score += score_val
                    count += 1
            if count > 0:
                average = round(total_score / count, 2)
                
    return render_template("reports/student_report.html",
                           classes=classes,
                           sections=sections,
                           students=students,
                           sel_class_id=sel_class_id,
                           sel_section_id=sel_section_id,
                           sel_student_id=sel_student_id,
                           selected_student=selected_student,
                           report_data=report_data,
                           average=average)

@reports_bp.route("/reports/performance")
@login_required
@cache.cached(timeout=60)
def performance():
    from sqlalchemy import func
    results = db.session.query(
        Classes.CName, 
        func.avg(Marks.Score)
    ).join(Student, Student.CID == Classes.CID)\
     .join(Marks, Marks.SID == Student.SID)\
     .filter(Classes.is_deleted == False, Student.is_deleted == False)\
     .group_by(Classes.CName).all()
     
    class_averages = [{'class_name': r[0], 'average': round(float(r[1]), 2)} for r in results if r[1] is not None]
    return render_template("reports/performance.html", class_averages=class_averages)

@reports_bp.route("/reports/student/<int:student_id>/pdf_fast")
@reports_bp.route("/reports/student/<int:student_id>/pdf")
@login_required
def student_report_pdf_fast(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    term_id = request.args.get('term_id', type=int)
    exam_id = request.args.get('exam_id', type=int)
    
    query = Marks.query.filter_by(SID=student_id)
    if term_id:
        query = query.filter_by(T_ID=term_id)
    if exam_id:
        query = query.filter_by(ExamID=exam_id)
        
    marks = query.all()
    
    report_data = {}
    for mark in marks:
        exam_name = "امتحان الفصل الدراسي"
        if hasattr(mark, 'exam') and mark.exam:
            exam_name = mark.exam.ExamName
        elif mark.ExamID:
            exam_obj = TypeExams.query.get(mark.ExamID)
            if exam_obj:
                exam_name = exam_obj.ExamName
            
        if exam_name not in report_data:
            report_data[exam_name] = []
        report_data[exam_name].append(mark)
        
    pdf_bytes = generate_student_pdf(student, report_data)
    
    response = make_response(bytes(pdf_bytes))
    response.headers['Content-Type'] = 'application/pdf'
    response.headers['Content-Disposition'] = f'attachment; filename=report_{student.SID}.pdf'
    return response

@reports_bp.route("/reports/student/<int:student_id>/excel")
@login_required
def student_report_excel(student_id):
    student = Student.query.get(student_id)
    if not student:
        return jsonify({'error': 'Student not found'}), 404

    term_id = request.args.get('term_id', type=int)
    exam_id = request.args.get('exam_id', type=int)
    
    query = Marks.query.filter_by(SID=student_id)
    if term_id:
        query = query.filter_by(T_ID=term_id)
    if exam_id:
        query = query.filter_by(ExamID=exam_id)
        
    marks = query.all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "كشف درجات"
    ws.sheet_view.rightToLeft = True
    
    header_fill = PatternFill(start_color="198754", end_color="198754", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    
    ws.append(["رقم المادة", "المادة الدراسية", "الدرجة", "التقدير"])
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        
    for mark in marks:
        sub_name = mark.subject.SubName if mark.subject else 'غير محدد'
        row = [mark.SubID, sub_name, mark.Score, mark.Grade or '—']
        ws.append(row)
        for cell in ws[ws.max_row]:
            cell.alignment = align_center
            
    ws.column_dimensions['B'].width = 30
            
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name=f'report_{student.SID}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')

@reports_bp.route("/reports/export/excel")
@login_required
def export_reports_master_excel():
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    term_id = request.args.get('term_id', type=int)
    
    query = Student.query.filter_by(is_deleted=False)
    if class_id:
        query = query.filter_by(CID=class_id)
    if section_id:
        query = query.filter_by(SectionID=section_id)
    
    students = query.order_by(Student.SName).all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "كشف التقارير الأكاديمية"
    ws.sheet_view.rightToLeft = True
    
    header_fill = PatternFill(start_color="1E40AF", end_color="1E40AF", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    
    headers = ["#", "الرقم الأكاديمي", "اسم الطالب", "الصف الدراسي", "الشعبة", "عدد المواد", "متوسط الدرجات", "التقدير العام"]
    ws.append(headers)
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        
    for i, st in enumerate(students, start=1):
        cname = st.school_class.CName if st.school_class else "غير محدد"
        sname = st.section.SectionName if st.section else "غير محدد"
        
        st_marks = Marks.query.filter_by(SID=st.SID).all()
        if subject_id:
            st_marks = [m for m in st_marks if m.SubID == subject_id]
        if term_id:
            st_marks = [m for m in st_marks if getattr(m, 'T_ID', None) == term_id]
            
        scores = [float(m.Score) for m in st_marks if m.Score is not None]
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        
        if avg >= 90: grade_str = 'ممتاز'
        elif avg >= 80: grade_str = 'جيد جداً'
        elif avg >= 70: grade_str = 'جيد'
        elif avg >= 60: grade_str = 'مقبول'
        else: grade_str = 'دون المستوى' if scores else 'غير مرصود'
        
        row = [i, st.SID, st.SName, cname, sname, len(st_marks), f"{avg}%" if scores else "—", grade_str]
        ws.append(row)
        for cell in ws[ws.max_row]:
            cell.alignment = align_center
            
    ws.column_dimensions['B'].width = 18
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 22
    ws.column_dimensions['E'].width = 15
    ws.column_dimensions['F'].width = 18
    ws.column_dimensions['G'].width = 18
    ws.column_dimensions['H'].width = 18
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(
        output,
        as_attachment=True,
        download_name='academic_reports_master.xlsx',
        mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )

@reports_bp.route("/reports/export/pdf")
@login_required
def export_reports_master_pdf():
    class_id = request.args.get('class_id', type=int)
    student = None
    if class_id:
        student = Student.query.filter_by(CID=class_id, is_deleted=False).first()
    if not student:
        student = Student.query.filter_by(is_deleted=False).first()
    if not student:
        return jsonify({'error': 'No student records available for export'}), 404
        
    return student_report_pdf_fast(student.SID)

@reports_bp.route("/reports/api/filter")
@login_required
def api_reports_filter():
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    term_id = request.args.get('term_id', type=int)
    
    query = Student.query.filter_by(is_deleted=False)
    if class_id:
        query = query.filter_by(CID=class_id)
    if section_id:
        query = query.filter_by(SectionID=section_id)
        
    students = query.all()
    
    data = []
    for st in students:
        marks = Marks.query.filter_by(SID=st.SID).all()
        if subject_id:
            marks = [m for m in marks if m.SubID == subject_id]
        if term_id:
            marks = [m for m in marks if getattr(m, 'T_ID', None) == term_id]
            
        scores = [float(m.Score) for m in marks if m.Score is not None]
        avg = round(sum(scores) / len(scores), 1) if scores else 0.0
        
        data.append({
            'student_id': st.SID,
            'name': st.SName,
            'class_name': st.school_class.CName if st.school_class else '—',
            'section_name': st.section.SectionName if st.section else '—',
            'subjects_count': len(marks),
            'average': avg
        })
        
    return jsonify({
        'success': True,
        'total': len(data),
        'students': data
    })

