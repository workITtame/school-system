from flask import Blueprint, render_template, request, make_response, send_file, current_app
from routes.auth_routes import login_required
from models import db, Student, Classes, Sections, Marks, TypeExams, Subject
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
    from models import Classes, Sections, Subject, Terms, Student
    
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
    classes = Classes.query.all()
    sections = Sections.query.all()
    
    sel_class_id = request.args.get('class_id')
    sel_section_id = request.args.get('section_id')
    sel_student_id = request.args.get('student_id')
    
    students = []
    if sel_class_id and sel_section_id:
        students = Student.query.filter_by(CID=sel_class_id, SectionID=sel_section_id, is_deleted=False).all()
        
    selected_student = None
    report_data = None
    average = 0
    
    if sel_student_id:
        selected_student = Student.query.get(sel_student_id)
        if selected_student:
            from sqlalchemy import text
            marks = db.session.execute(text("SELECT * FROM vw_student_grades WHERE student_id = :sid"), {'sid': sel_student_id}).fetchall()
            
            report_data = {}
            total_score = 0
            count = 0
            for mark in marks:
                exam_name = mark.exam_type if mark.exam_type else "امتحان غير محدد"
                if exam_name not in report_data:
                    report_data[exam_name] = []
                report_data[exam_name].append(mark)
                if mark.score is not None:
                    total_score += float(mark.score)
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
@login_required
def student_report_pdf_fast(student_id):
    student = Student.query.get_or_404(student_id)
    term_id = request.args.get('term_id')
    exam_id = request.args.get('exam_id')
    
    query = Marks.query.filter_by(SID=student_id)
    if term_id:
        query = query.filter_by(T_ID=term_id)
    if exam_id:
        query = query.filter_by(ExamID=exam_id)
        
    marks = query.all()
    
    report_data = {}
    for mark in marks:
        exam_name = "امتحان غير محدد"
        exam_obj = TypeExams.query.get(mark.ExamID) if mark.ExamID else None
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
    student = Student.query.get_or_404(student_id)
    term_id = request.args.get('term_id')
    exam_id = request.args.get('exam_id')
    
    query = Marks.query.filter_by(SID=student_id)
    if term_id:
        query = query.filter_by(T_ID=term_id)
    if exam_id:
        query = query.filter_by(ExamID=exam_id)
        
    marks = query.all()
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "كشف درجات"
    
    # Right to left view
    ws.sheet_view.rightToLeft = True
    
    # Header styling
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
        row = [mark.SubID, sub_name, mark.Score, mark.Grade]
        ws.append(row)
        for cell in ws[ws.max_row]:
            cell.alignment = align_center
            
    # Auto-adjust column width
    ws.column_dimensions['B'].width = 30
            
    # Save to memory
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    return send_file(output, as_attachment=True, download_name=f'report_{student.SID}.xlsx', mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
