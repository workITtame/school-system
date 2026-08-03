from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import or_
from sqlalchemy.orm import joinedload, selectinload
from models import db, Student, Teacher, Classes, Subject, User, Qualifications
from models.timetable import SchoolTable
from models.schemas import students_schema, student_schema, teachers_schema, teacher_schema, classes_schema, class_schema, school_tables_schema
from flask_jwt_extended import jwt_required
from werkzeug.security import generate_password_hash
import os
import uuid
from datetime import datetime

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

def api_response(success, message="Success", data=None, meta=None, status_code=200):
    response = {
        "success": success,
        "message": message,
        "data": data if data is not None else {}
    }
    if meta:
        response["meta"] = meta
    return jsonify(response), status_code

@api_bp.route("/status", methods=['GET'])
def status():
    return api_response(True, "API is running properly")

@api_bp.route("/students", methods=['GET'])
def get_students():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search_term = request.args.get('search', '', type=str).strip()
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    gender = request.args.get('gender', type=str)
    status_filter = request.args.get('status', type=str)
    
    try:
        query = Student.query.options(
            joinedload(Student.school_class),
            joinedload(Student.section),
            selectinload(Student.attendances)
        ).filter_by(is_deleted=False)
        
        if search_term:
            search_pattern = f"%{search_term}%"
            query = query.filter(or_(
                Student.SName.like(search_pattern),
                Student.SID.like(search_pattern),
                Student.Parent_Name.like(search_pattern),
                Student.Parent_Number.like(search_pattern),
                Student.Neighborhood.like(search_pattern)
            ))
            
        if class_id:
            query = query.filter(Student.CID == class_id)
        if section_id:
            query = query.filter(Student.SectionID == section_id)
        if gender:
            query = query.filter(Student.Gender == gender)
        if status_filter:
            query = query.filter(Student.Status == status_filter)
            
        paginated = query.order_by(Student.SID.desc()).paginate(page=page, per_page=limit, error_out=False)
        
        from models.grade import Marks
        
        # Batch fetch marks for current page students to avoid N+1 queries
        student_ids = [s.SID for s in paginated.items]
        student_marks_map = {}
        if student_ids:
            marks_records = Marks.query.filter(Marks.SID.in_(student_ids)).all()
            for m in marks_records:
                if m.SID not in student_marks_map:
                    student_marks_map[m.SID] = []
                if m.Score is not None:
                    student_marks_map[m.SID].append(m.Score)
        
        data = []
        today = datetime.now().date()
        
        for s in paginated.items:
            s_dict = student_schema.dump(s)
            
            # Class & Section names
            s_dict['class_name'] = s.school_class.CName if s.school_class else '—'
            s_dict['section_name'] = s.section.SectionName if s.section else '—'
            
            # Attendance Rate calculation
            total_att = len(s.attendances) if s.attendances else 0
            present_att = sum(1 for a in s.attendances if a.Status in ['حاضر', 'Present', 'حضور']) if s.attendances else 0
            s_dict['attendance_rate'] = round((present_att / total_att) * 100, 1) if total_att > 0 else 100.0
            
            # GPA / Average Grade calculation
            scores = student_marks_map.get(s.SID, [])
            s_dict['gpa'] = round(sum(scores) / len(scores), 1) if scores else '—'
            
            # Age calculation
            if s.DOB:
                age = today.year - s.DOB.year - ((today.month, today.day) < (s.DOB.month, s.DOB.day))
                s_dict['age'] = age
            else:
                s_dict['age'] = '—'
                
            s_dict['updated_at_formatted'] = s.updated_at.strftime('%Y-%m-%d') if hasattr(s, 'updated_at') and s.updated_at else '—'
            data.append(s_dict)
            
        return api_response(True, "Students retrieved successfully", data, meta={
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": paginated.page
        })
    except Exception as e:
        return api_response(False, f"DB Error: {str(e)}")

@api_bp.route("/students", methods=['POST'])
@jwt_required()
def add_student():
    """Professional API endpoint to add a new student"""
    if not request.is_json:
        return api_response(False, "Missing JSON in request", status_code=400)
        
    data = request.get_json()
    
    # Basic validation
    if not data.get('SName'):
        return api_response(False, "Student name (SName) is required", status_code=400)
        
    try:
        # Deserialize JSON to Student object using Marshmallow
        new_student = student_schema.load(data, session=db.session)
        db.session.add(new_student)
        db.session.commit()
        
        # Serialize the created object back to JSON
        result = student_schema.dump(new_student)
        return api_response(True, "Student added successfully", result, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"Failed to add student: {str(e)}", status_code=500)

@api_bp.route("/students/<int:id>", methods=['GET'])
@jwt_required()
def get_student(id):
    student = Student.query.filter_by(SID=id, is_deleted=False).first()
    if not student:
        return api_response(False, "الطالب غير موجود أو تم حذفه", status_code=404)
        
    data = student_schema.dump(student)
    return api_response(True, "تم جلب بيانات الطالب بنجاح", data)

@api_bp.route("/students/<int:id>", methods=['PUT'])
@jwt_required()
def update_student(id):
    student = Student.query.filter_by(SID=id, is_deleted=False).first()
    if not student:
        return api_response(False, "الطالب غير موجود", status_code=404)
        
    if not request.is_json:
        return api_response(False, "البيانات يجب أن تكون بصيغة JSON", status_code=400)
        
    data = request.get_json()
    
    # Validation
    if 'SName' in data and len(data['SName'].strip()) < 3:
        return api_response(False, "اسم الطالب يجب أن يكون 3 أحرف على الأقل", status_code=400)
        
    try:
        updated_student = student_schema.load(data, instance=student, session=db.session, partial=True)
        db.session.commit()
        
        result = student_schema.dump(updated_student)
        return api_response(True, "تم تحديث بيانات الطالب بنجاح", result)
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"حدث خطأ أثناء التحديث: {str(e)}", status_code=500)

@api_bp.route("/students/<int:id>", methods=['DELETE'])
@jwt_required()
def delete_student(id):
    student = Student.query.filter_by(SID=id, is_deleted=False).first()
    if not student:
        return api_response(False, "الطالب غير موجود", status_code=404)
        
    try:
        student.is_deleted = True
        db.session.commit()
        return api_response(True, "تم حذف الطالب بنجاح (Soft Delete)")
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"حدث خطأ أثناء الحذف: {str(e)}", status_code=500)

@api_bp.route("/teachers", methods=['GET'])
@jwt_required()
def get_teachers():
    page = request.args.get('page', 1, type=int)
    limit = request.args.get('limit', 10, type=int)
    search_term = request.args.get('search', '', type=str)
    qual_filter = request.args.get('qual', '', type=str)
    status_filter = request.args.get('status', '', type=str)
    gender_filter = request.args.get('gender', '', type=str)
    class_id = request.args.get('class_id', type=int)
    
    try:
        from models import SchoolTable
        from models.academic import ClassSubject, TeacherSubject
        query = Teacher.query.filter_by(is_deleted=False)
        
        if class_id:
            t_ids = [t[0] for t in db.session.query(SchoolTable.TeacherID).filter(SchoolTable.CID == class_id, SchoolTable.is_deleted == False).distinct().all() if t[0]]
            s_ids = [s[0] for s in db.session.query(ClassSubject.SubjectID).filter(ClassSubject.ClassID == class_id).all() if s[0]]
            if s_ids:
                ts_teacher_ids = [t[0] for t in db.session.query(TeacherSubject.teacher_id).filter(TeacherSubject.subject_id.in_(s_ids)).distinct().all() if t[0]]
                t_ids.extend(ts_teacher_ids)
            query = query.filter(Teacher.TeacherID.in_(list(set(t_ids))))
        
        if search_term:
            query = query.filter(Teacher.TeacherName.like(f"%{search_term}%"))
            
        if qual_filter:
            query = query.join(Teacher.qualification).filter(Qualifications.QName == qual_filter)
            
        if status_filter:
            query = query.filter(Teacher.Status == status_filter)
            
        if gender_filter:
            query = query.filter(Teacher.Gender == gender_filter)
            
        paginated = query.order_by(Teacher.TeacherID.desc()).paginate(page=page, per_page=limit, error_out=False)
        
        data = teachers_schema.dump(paginated.items)
        
        for idx, t in enumerate(paginated.items):
            if t.user:
                data[idx]['Role'] = t.user.role
            if t.qualification:
                data[idx]['q_name'] = t.qualification.QName
            data[idx]['subjects'] = [{'SubID': s.SubID, 'SubName': s.SubName} for s in t.subjects]
            
            # Calculate dynamic slots and taught classes from timetable (SchoolTable)
            t_slots = SchoolTable.query.filter_by(TeacherID=t.TeacherID, is_deleted=False).all()
            data[idx]['slots_count'] = len(t_slots)
            data[idx]['classes_count'] = len(set(s.CID for s in t_slots if s.CID))
            
        return api_response(True, "Teachers retrieved successfully", data, meta={
            "total": paginated.total,
            "pages": paginated.pages,
            "current_page": paginated.page
        })
    except Exception as e:
        return api_response(False, f"DB Error: {str(e)}")

@api_bp.route("/teachers", methods=['POST'])
@jwt_required()
def add_teacher():
    """Professional API endpoint to add a new teacher with image and role support"""
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    if not data.get('TeacherName'):
        return api_response(False, "اسم المعلم مطلوب", status_code=400)
    if not data.get('Email'):
        return api_response(False, "البريد الإلكتروني مطلوب", status_code=400)
        
    email = data.get('Email')
    existing_user = User.query.filter_by(username=email, is_deleted=False).first()
    if existing_user:
        return api_response(False, "البريد الإلكتروني مسجل مسبقاً في النظام", status_code=400)
        
    try:
        password = data.get('Password') or '123456'
        role = data.get('Role') or 'teacher'
        
        new_user = User(username=email, name=data.get('TeacherName'), role=role)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.flush()
        
        dob_str = data.get('DOB')
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        
        q_name = data.get('q_name')
        qid = None
        if q_name:
            q = Qualifications.query.filter_by(QName=q_name).first()
            if not q:
                q = Qualifications(QName=q_name)
                db.session.add(q)
                db.session.commit()
            qid = q.QID
            

        
        photo_filename = None
        if not request.is_json and 'Image' in request.files:
            photo = request.files['Image']
            if photo and photo.filename:
                ext = os.path.splitext(photo.filename)[1]
                photo_filename = str(uuid.uuid4()) + ext
                photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'teachers', photo_filename)
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                photo.save(photo_path)
                photo_filename = 'uploads/teachers/' + photo_filename
                
        new_teacher = Teacher(
            user_id=new_user.id,
            TeacherName=data.get('TeacherName'),
            Email=email,
            Phone=data.get('Phone'),
            Gender=data.get('Gender', 'ذكر'),
            Password=generate_password_hash(password),
            Salary=data.get('Salary') if data.get('Salary') else None,
            DOB=dob,
            POB=data.get('POB'),
            TeacherTitle=data.get('TeacherTitle'),
            Currency=data.get('Currency'),
            QID=qid,
            Status=data.get('Status', 'نشط'),
            Image=photo_filename
        )

        subject_ids = data.get('subject_ids') or request.form.getlist('subject_ids')
        if subject_ids:
            if isinstance(subject_ids, str):
                subject_ids = [int(x) for x in subject_ids.split(',') if x.strip().isdigit()]
            elif isinstance(subject_ids, list):
                subject_ids = [int(x) for x in subject_ids if str(x).isdigit()]
            new_teacher.subjects = Subject.query.filter(Subject.SubID.in_(subject_ids)).all()

        db.session.add(new_teacher)
        db.session.commit()
        
        result = teacher_schema.dump(new_teacher)
        result['subjects'] = [{'SubID': s.SubID, 'SubName': s.SubName} for s in new_teacher.subjects]
        return api_response(True, "تمت إضافة المعلم بنجاح", result, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"فشل إضافة المعلم: {str(e)}", status_code=500)

@api_bp.route("/teachers/<int:id>", methods=['GET'])
@jwt_required()
def get_teacher(id):
    teacher = Teacher.query.filter_by(TeacherID=id, is_deleted=False).first()
    if not teacher:
        return api_response(False, "المعلم غير موجود أو تم حذفه", status_code=404)
        
    data = teacher_schema.dump(teacher)
    if teacher.user:
        data['Role'] = teacher.user.role
    if teacher.qualification:
        data['q_name'] = teacher.qualification.QName
    data['subjects'] = [{'SubID': s.SubID, 'SubName': s.SubName} for s in teacher.subjects]
    return api_response(True, "تم جلب بيانات المعلم", data)

@api_bp.route("/teachers/<int:id>", methods=['PUT'])
@jwt_required()
def update_teacher(id):
    teacher = Teacher.query.filter_by(TeacherID=id, is_deleted=False).first()
    if not teacher:
        return api_response(False, "المعلم غير موجود", status_code=404)
        
    data = request.get_json() if request.is_json else request.form.to_dict()
    
    email = data.get('Email')
    if email and email != teacher.Email:
        existing_user = User.query.filter_by(username=email, is_deleted=False).first()
        if existing_user:
            return api_response(False, "البريد الإلكتروني مسجل مسبقاً لمعلم آخر", status_code=400)
    
    try:
        teacher.TeacherName = data.get('TeacherName', teacher.TeacherName)
        if email:
            teacher.Email = email
            if teacher.user: teacher.user.username = email
            
        teacher.Phone = data.get('Phone', teacher.Phone)
        teacher.Salary = data.get('Salary') if data.get('Salary') else teacher.Salary
        
        dob_str = data.get('DOB')
        if dob_str:
            teacher.DOB = datetime.strptime(dob_str, '%Y-%m-%d').date()
            
        teacher.POB = data.get('POB', teacher.POB)
        teacher.TeacherTitle = data.get('TeacherTitle', teacher.TeacherTitle)
        teacher.Currency = data.get('Currency', teacher.Currency)
        
        if 'Status' in data:
            teacher.Status = data.get('Status')

        if 'Gender' in data:
            teacher.Gender = data.get('Gender')
        
        q_name = data.get('q_name')
        if q_name:
            q = Qualifications.query.filter_by(QName=q_name).first()
            if not q:
                q = Qualifications(QName=q_name)
                db.session.add(q)
                db.session.commit()
            teacher.QID = q.QID
            

            
        role = data.get('Role')
        if role and teacher.user:
            teacher.user.role = role
            
        password = data.get('Password')
        if password:
            hashed_pw = generate_password_hash(password)
            teacher.Password = hashed_pw
            if teacher.user:
                teacher.user.set_password(password)
                
        if not request.is_json and 'Image' in request.files:
            photo = request.files['Image']
            if photo and photo.filename:
                ext = os.path.splitext(photo.filename)[1]
                photo_filename = str(uuid.uuid4()) + ext
                photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'teachers', photo_filename)
                os.makedirs(os.path.dirname(photo_path), exist_ok=True)
                photo.save(photo_path)
                teacher.Image = 'uploads/teachers/' + photo_filename
                
        if 'subject_ids' in data or 'subject_ids' in request.form:
            subject_ids = data.get('subject_ids') or request.form.getlist('subject_ids')
            if isinstance(subject_ids, str):
                subject_ids = [int(x) for x in subject_ids.split(',') if x.strip().isdigit()]
            elif isinstance(subject_ids, list):
                subject_ids = [int(x) for x in subject_ids if str(x).isdigit()]
            
            current_sub_ids = {s.SubID for s in teacher.subjects}
            target_sub_ids = set(subject_ids)
            
            # Remove unselected subjects
            for sub in list(teacher.subjects):
                if sub.SubID not in target_sub_ids:
                    teacher.subjects.remove(sub)
                    
            # Add newly selected subjects
            to_add_ids = target_sub_ids - current_sub_ids
            if to_add_ids:
                new_subs = Subject.query.filter(Subject.SubID.in_(to_add_ids)).all()
                for sub in new_subs:
                    teacher.subjects.append(sub)

        db.session.commit()
        result = teacher_schema.dump(teacher)
        result['subjects'] = [{'SubID': s.SubID, 'SubName': s.SubName} for s in teacher.subjects]
        return api_response(True, "تم تحديث بيانات المعلم بنجاح", result)
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"حدث خطأ أثناء التحديث: {str(e)}", status_code=500)

@api_bp.route("/teachers/<int:id>", methods=['DELETE'])
@jwt_required()
def delete_teacher(id):
    teacher = Teacher.query.filter_by(TeacherID=id, is_deleted=False).first()
    if not teacher:
        return api_response(False, "المعلم غير موجود", status_code=404)

    # Delete Protection: Check if teacher is assigned to active timetable slots
    timetable_count = SchoolTable.query.filter_by(TeacherID=id, is_deleted=False).count()
    if timetable_count > 0:
        return api_response(False, "لا يمكن حذف المعلم لأنه مرتبط بجدول حصص أسبوعي نشط.", status_code=400)
        
    try:
        if teacher.user:
            teacher.user.is_deleted = True
        teacher.is_deleted = True
        db.session.commit()
        return api_response(True, "تم حذف المعلم بنجاح")
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"حدث خطأ أثناء الحذف: {str(e)}", status_code=500)

@api_bp.route("/classes", methods=['GET'])
@jwt_required()
def get_classes():
    classes_list = Classes.query.all()
    data = classes_schema.dump(classes_list)
    return api_response(True, "Classes retrieved successfully", data)

@api_bp.route("/classes", methods=['POST'])
@jwt_required()
def add_class():
    if not request.is_json:
        return api_response(False, "Missing JSON in request", status_code=400)
        
    data = request.get_json()
    
    if not data.get('CName'):
        return api_response(False, "Class name (CName) is required", status_code=400)
        
    try:
        new_class = class_schema.load(data, session=db.session)
        db.session.add(new_class)
        db.session.commit()
        
        result = class_schema.dump(new_class)
        return api_response(True, "Class added successfully", result, status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"Failed to add class: {str(e)}", status_code=500)

@api_bp.route("/timetable/reference-data", methods=['GET'])
@jwt_required()
def get_timetable_reference_data():
    from models.academic import Classes, Days, Lessons, Terms
    from models.teacher import Teacher
    
    try:
        terms = Terms.query.all()
        classes = Classes.query.all()
        days = Days.query.all()
        lessons = Lessons.query.all()
        teachers = Teacher.query.filter_by(is_deleted=False).all()
        
        data = {
            "terms": [{"T_ID": t.T_ID, "T_Name": t.T_Name} for t in terms],
            "days": [{"DayID": d.DayID, "DName": d.DName} for d in days],
            "lessons": [{"LessonID": l.LessonID, "LessonName": l.LessonName} for l in lessons],
            "classes": [],
            "teachers": [
                {
                    "TeacherID": t.TeacherID, 
                    "TeacherName": t.TeacherName,
                    "subjects": [s.SubID for s in t.subjects]
                } for t in teachers
            ]
        }
        
        for c in classes:
            data["classes"].append({
                "CID": c.CID,
                "CName": c.CName,
                "sections": [{"SectionID": s.SectionID, "SectionName": s.SectionName} for s in c.sections],
                "subjects": [{"SubID": s.SubID, "SubName": s.SubName} for s in c.subjects]
            })
            
        return api_response(True, "Reference data retrieved successfully", data)
    except Exception as e:
        return api_response(False, f"DB Error: {str(e)}", status_code=500)

@api_bp.route("/timetable", methods=['GET'])
@jwt_required()
def get_timetable():
    term_id = request.args.get('term_id', type=int)
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    
    if not all([term_id, class_id, section_id]):
        return api_response(False, "term_id, class_id, and section_id are required", status_code=400)
        
    try:
        entries = SchoolTable.query.filter_by(
            CID=class_id, 
            SectionID=section_id, 
            T_ID=term_id, 
            is_deleted=False
        ).all()
        
        data = school_tables_schema.dump(entries)
        
        # Enrich the data with relationships
        for idx, entry in enumerate(entries):
            data[idx]['SubjectName'] = entry.subject.SubName if entry.subject else None
            data[idx]['SubjectColor'] = entry.subject.Color if entry.subject else None
            data[idx]['TeacherName'] = entry.teacher.TeacherName if entry.teacher else None
            data[idx]['DayName'] = entry.day.DName if entry.day else None
            data[idx]['LessonName'] = entry.lesson.LessonName if entry.lesson else None
            
        return api_response(True, "Timetable retrieved successfully", data)
    except Exception as e:
        return api_response(False, f"DB Error: {str(e)}", status_code=500)

@api_bp.route("/timetable", methods=['POST'])
@jwt_required()
def add_timetable_entry():
    if not request.is_json:
        return api_response(False, "Missing JSON in request", status_code=400)
        
    data = request.get_json()
    
    required_fields = ['term_id', 'class_id', 'section_id', 'day_id', 'lesson_id', 'subject_id', 'teacher_id']
    if not all(field in data for field in required_fields):
        return api_response(False, "جميع الحقول مطلوبة لإضافة حصة", status_code=400)
        
    try:
        from models.teacher import Teacher
        teacher = Teacher.query.get(data['teacher_id'])
        if not teacher:
            return api_response(False, "المعلم غير موجود", status_code=404)
        
        teacher_sub_ids = [s.SubID for s in teacher.subjects]
        if teacher_sub_ids and int(data['subject_id']) not in teacher_sub_ids:
            return api_response(False, "غير مصرح: هذا المعلم لا يدرس المادة المحددة.", status_code=400)

        # Check teacher conflict
        teacher_conflict = SchoolTable.query.filter_by(
            TeacherID=data['teacher_id'], 
            DayID=data['day_id'], 
            LessonID=data['lesson_id'], 
            T_ID=data['term_id'],
            is_deleted=False
        ).first()
        
        if teacher_conflict:
            return api_response(False, "تعارض: هذا المعلم لديه حصة أخرى في نفس الوقت.", status_code=409)

        # Check class conflict
        class_conflict = SchoolTable.query.filter_by(
            CID=data['class_id'], 
            SectionID=data['section_id'], 
            DayID=data['day_id'], 
            LessonID=data['lesson_id'], 
            T_ID=data['term_id'],
            is_deleted=False
        ).first()
        
        if class_conflict:
            return api_response(False, "تعارض: هذا الصف والشعبة لديهم حصة مسبقاً في هذا الوقت.", status_code=409)

        new_entry = SchoolTable(
            T_ID=data['term_id'],
            CID=data['class_id'],
            SectionID=data['section_id'],
            DayID=data['day_id'],
            LessonID=data['lesson_id'],
            SubID=data['subject_id'],
            TeacherID=data['teacher_id']
        )
        db.session.add(new_entry)
        db.session.commit()
        
        return api_response(True, "تم إضافة الحصة إلى الجدول بنجاح", status_code=201)
        
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"حدث خطأ أثناء الحفظ: {str(e)}", status_code=500)

@api_bp.route("/timetable/<int:id>", methods=['DELETE'])
@jwt_required()
def delete_timetable_entry(id):
    try:
        entry = SchoolTable.query.get(id)
        if not entry or entry.is_deleted:
            return api_response(False, "الحصة غير موجودة", status_code=404)
            
        entry.is_deleted = True
        db.session.commit()
        return api_response(True, "تم حذف الحصة بنجاح")
        
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"حدث خطأ أثناء الحذف: {str(e)}", status_code=500)

# ==========================================
# GRADES API ROUTES
# ==========================================

@api_bp.route("/grades/reference", methods=['GET'])
@jwt_required()
def get_grades_reference():
    from models.academic import Classes, Terms, Subject
    from models.timetable import TypeExams
    
    try:
        terms = Terms.query.all()
        classes = Classes.query.all()
        subjects = Subject.query.all()
        exams = TypeExams.query.all()
        
        data = {
            "terms": [{"T_ID": t.T_ID, "T_Name": t.T_Name} for t in terms],
            "exams": [{"ExamID": e.ExamID, "ExamName": e.ExamName} for e in exams],
            "subjects": [{"SubID": s.SubID, "SubName": s.SubName} for s in subjects],
            "classes": []
        }
        
        for c in classes:
            data["classes"].append({
                "CID": c.CID,
                "CName": c.CName,
                "sections": [{"SectionID": s.SectionID, "SectionName": s.SectionName} for s in c.sections],
                "subjects": [{"SubID": s.SubID, "SubName": s.SubName} for s in c.subjects]
            })
            
        return api_response(True, "Reference data retrieved successfully", data)
    except Exception as e:
        return api_response(False, f"DB Error: {str(e)}", status_code=500)


@api_bp.route("/grades/class", methods=['GET'])
@jwt_required()
def get_class_grades():
    term_id = request.args.get('term_id', type=int)
    class_id = request.args.get('class_id', type=int)
    section_id = request.args.get('section_id', type=int)
    subject_id = request.args.get('subject_id', type=int)
    exam_id = request.args.get('exam_id', type=int)
    
    if not all([term_id, class_id, section_id, subject_id, exam_id]):
        return api_response(False, "جميع معايير الفلترة مطلوبة", status_code=400)
        
    try:
        from models.student import Student
        from models.grade import Marks
        
        students = Student.query.filter_by(
            CID=class_id,
            SectionID=section_id,
            is_deleted=False
        ).all()
        
        results = []
        for st in students:
            # Check for existing mark
            mark = Marks.query.filter_by(
                SID=st.SID,
                SubID=subject_id,
                ExamID=exam_id,
                T_ID=term_id
            ).first()
            
            results.append({
                "SID": st.SID,
                "StudentName": st.StudentName,
                "Score": float(mark.Score) if mark and mark.Score is not None else None,
                "Grade": mark.Grade if mark else None
            })
            
        return api_response(True, "Students and grades retrieved", results)
    except Exception as e:
        return api_response(False, f"DB Error: {str(e)}", status_code=500)


@api_bp.route("/grades/bulk", methods=['POST'])
@jwt_required()
def save_bulk_grades():
    if not request.is_json:
        return api_response(False, "Missing JSON in request", status_code=400)
        
    data = request.get_json()
    
    required_fields = ['term_id', 'subject_id', 'exam_id', 'grades']
    if not all(field in data for field in required_fields):
        return api_response(False, "جميع الحقول مطلوبة (ترم، مادة، امتحان، درجات)", status_code=400)
        
    term_id = data['term_id']
    subject_id = data['subject_id']
    exam_id = data['exam_id']
    grades_list = data['grades']
    
    # Get the teacher id
    user_id = get_jwt_identity()
    from models.user import User
    from models.teacher import Teacher
    user = User.query.get(user_id)
    
    teacher_id = None
    if user and user.role == 'teacher':
        teacher = Teacher.query.filter_by(user_id=user.id).first()
        if teacher:
            teacher_id = teacher.TeacherID
            # Optional: Strict Check if teacher teaches this subject
            # if subject_id not in [s.SubID for s in teacher.subjects]:
            #     return api_response(False, "لا يمكنك إدخال درجات مادة لا تدرسها", status_code=403)
            
    # Default to 1 for admin or if teacher not found
    if not teacher_id:
        teacher_id = 1 

    try:
        from models.grade import Marks, DetailMarks
        
        def calculate_letter(score):
            if score >= 90: return 'A'
            if score >= 80: return 'B'
            if score >= 70: return 'C'
            if score >= 60: return 'D'
            return 'F'

        for item in grades_list:
            sid = item.get('sid')
            score_val = item.get('score')
            
            if sid is None or score_val is None or score_val == "":
                continue
                
            score = float(score_val)
            if score < 0 or score > 100:
                return api_response(False, "الدرجة يجب أن تكون بين 0 و 100", status_code=400)
                
            letter_grade = calculate_letter(score)

            # 1. UPSERT Marks
            mark = Marks.query.filter_by(SID=sid, SubID=subject_id, ExamID=exam_id, T_ID=term_id).first()
            if not mark:
                mark = Marks(SID=sid, SubID=subject_id, ExamID=exam_id, T_ID=term_id, TeacherID=teacher_id, Score=score, Grade=letter_grade)
                db.session.add(mark)
            else:
                mark.Score = score
                mark.Grade = letter_grade
                mark.TeacherID = teacher_id

            # 2. UPSERT DetailMarks
            detail = DetailMarks.query.filter_by(SID=sid, SubID=subject_id, ExamID=exam_id, T_ID=term_id).first()
            if not detail:
                detail = DetailMarks(SID=sid, SubID=subject_id, ExamID=exam_id, T_ID=term_id, TeacherID=teacher_id, Score=score)
                db.session.add(detail)
            else:
                detail.Score = score
                detail.TeacherID = teacher_id
                
        db.session.commit()
        return api_response(True, "تم حفظ الدرجات بنجاح", status_code=200)
    except Exception as e:
        db.session.rollback()
        return api_response(False, f"DB Error: {str(e)}", status_code=500)
