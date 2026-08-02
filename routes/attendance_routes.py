from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify
from datetime import date
from models import db, Student, Classes, Sections
from models.student import Attendance
from utils.decorators import admin_required

attendance_bp = Blueprint('attendance', __name__, url_prefix='/attendance')

@attendance_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    classes = Classes.query.all()
    sections = Sections.query.all()
    
    # Get current date stats
    today = date.today()
    total_students = Student.query.filter_by(Status='نشط').count()
    
    present = Attendance.query.filter(Attendance.Date == today, Attendance.Status.in_(['Present', 'حاضر'])).count()
    absent = Attendance.query.filter(Attendance.Date == today, Attendance.Status.in_(['Absent', 'غائب'])).count()
    late = Attendance.query.filter(Attendance.Date == today, Attendance.Status.in_(['Late', 'متأخر', 'تأخر'])).count()
    
    attendance_rate = 0
    if total_students > 0:
        attendance_rate = round((present / total_students) * 100, 1)
        
    return render_template('attendance.html',
                           classes=classes,
                           sections=sections,
                           today=today.strftime('%Y-%m-%d'),
                           total_students=total_students,
                           present=present,
                           absent=absent,
                           late=late,
                           attendance_rate=attendance_rate)

@attendance_bp.route('/api/students')
def get_students():
    class_id = request.args.get('class_id')
    section_id = request.args.get('section_id')
    target_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    
    query = Student.query.filter_by(Status='نشط', is_deleted=False)
    if class_id:
        query = query.filter_by(CID=class_id)
    if section_id:
        query = query.filter_by(SectionID=section_id)
        
    students = query.all()
    student_ids = [s.SID for s in students]
    
    attendances = {}
    if student_ids:
        att_records = Attendance.query.filter(Attendance.SID.in_(student_ids), Attendance.Date == target_date).all()
        attendances = {att.SID: att for att in att_records}
    
    result = []
    for s in students:
        att = attendances.get(s.SID)
        status = att.Status if att else 'غير مسجل'
        result.append({
            'SID': s.SID,
            'SName': s.SName,
            'Status': status,
            'Time': getattr(att, 'created_at', None),
            'Note': getattr(att, 'Note', '-')
        })
        
    return jsonify({'success': True, 'data': result})

@attendance_bp.route('/api/mark', methods=['POST'])
def mark_attendance():
    data = request.json
    sid = data.get('sid')
    target_date = data.get('date')
    status = data.get('status')
    
    if not all([sid, target_date, status]):
        return jsonify({'success': False, 'message': 'بيانات ناقصة'})
        
    att = Attendance.query.filter_by(SID=sid, Date=target_date).first()
    if att:
        att.Status = status
    else:
        att = Attendance(SID=sid, Date=target_date, Status=status)
        db.session.add(att)
        
    try:
        db.session.commit()
        return jsonify({'success': True})
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': str(e)})

@attendance_bp.route('/export')
def export_attendance():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    class_id = request.args.get('class_id')
    section_id = request.args.get('section_id')
    target_date = request.args.get('date', date.today().strftime('%Y-%m-%d'))
    
    query = Student.query.filter_by(Status='نشط')
    if class_id:
        query = query.filter_by(CID=class_id)
    if section_id:
        query = query.filter_by(SectionID=section_id)
        
    students = query.all()
    
    import openpyxl
    from openpyxl.styles import Font, Alignment, PatternFill
    import io
    from flask import send_file
    
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "تقرير الحضور والغياب"
    ws.sheet_view.rightToLeft = True
    
    header_fill = PatternFill(start_color="2563EB", end_color="2563EB", fill_type="solid")
    header_font = Font(color="FFFFFF", bold=True)
    align_center = Alignment(horizontal="center", vertical="center")
    
    ws.append(["#", "رقم الطالب", "اسم الطالب", "التاريخ", "الحالة"])
    for cell in ws[1]:
        cell.fill = header_fill
        cell.font = header_font
        cell.alignment = align_center
        
    student_ids = [s.SID for s in students]
    attendances = {}
    if student_ids:
        att_records = Attendance.query.filter(Attendance.SID.in_(student_ids), Attendance.Date == target_date).all()
        attendances = {att.SID: att for att in att_records}

    for idx, s in enumerate(students, 1):
        att = attendances.get(s.SID)
        status_text = att.Status if att else 'غير مسجل'
        row = [idx, s.SID, s.SName, target_date, status_text]
        ws.append(row)
        for cell in ws[ws.max_row]:
            cell.alignment = align_center
            
    ws.column_dimensions['C'].width = 30
    ws.column_dimensions['D'].width = 15
    ws.column_dimensions['E'].width = 15
    
    output = io.BytesIO()
    wb.save(output)
    output.seek(0)
    
    filename = f"attendance_{target_date}.xlsx"
    return send_file(output, as_attachment=True, download_name=filename, mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
