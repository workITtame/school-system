from flask import Blueprint, render_template, request, redirect, url_for, flash, session, current_app
from werkzeug.utils import secure_filename
import os
from models import db, Student, Classes, Sections, Directorate, Country, Governorates
from datetime import datetime, timedelta
import uuid
from utils.decorators import admin_required

students_bp = Blueprint('students', __name__, url_prefix='/students')

@students_bp.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    # Lookup data for Modals (Add / Edit)
    countries = Country.query.all()
    governorates = Governorates.query.all()
    directorates = Directorate.query.all()
    classes = Classes.query.all()
    sections = Sections.query.all()
    
    total_students = Student.query.filter_by(is_deleted=False).count()
    active_students = Student.query.filter_by(is_deleted=False, Status='نشط').count()
    inactive_students = Student.query.filter(Student.is_deleted == False, Student.Status != 'نشط').count()
    male_students = Student.query.filter(Student.is_deleted == False, Student.Gender.in_(['ذكر', 'Male'])).count()
    female_students = Student.query.filter(Student.is_deleted == False, Student.Gender.in_(['أنثى', 'Female'])).count()
    new_students = Student.query.filter(Student.is_deleted == False, Student.created_at >= (datetime.utcnow() - timedelta(days=30))).count()
    
    return render_template('students.html', 
                           countries=countries, 
                           governorates=governorates, 
                           directorates=directorates, 
                           classes=classes, 
                           sections=sections,
                           total_students=total_students,
                           active_students=active_students,
                           inactive_students=inactive_students,
                           male_students=male_students,
                           female_students=female_students,
                           new_students=new_students)

@students_bp.route('/add', methods=['GET', 'POST'])
@admin_required
def add_student():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    if request.method == 'POST':
        name = request.form.get('name')
        if not name or not name.strip():
            flash('الرجاء إدخال اسم الطالب بشكل صحيح', 'warning')
            return redirect(url_for('students.add_student'))
        gender = request.form.get('gender')
        dob_str = request.form.get('dob')
        parent_name = request.form.get('parent_name')
        parent_phone = request.form.get('parent_number')
        parent_work = request.form.get('parent_work')
        
        country_name = request.form.get('country_name')
        country_id = None
        if country_name:
            c = Country.query.filter_by(Country_Name=country_name).first()
            if not c:
                c = Country(Country_Name=country_name)
                db.session.add(c)
                db.session.commit()
            country_id = c.CountryID
        
        g_name = request.form.get('g_name')
        g_id = None
        if g_name:
            gov = Governorates.query.filter_by(G_Name=g_name).first()
            if not gov:
                gov = Governorates(G_Name=g_name, CountryID=country_id)
                db.session.add(gov)
                db.session.commit()
            g_id = gov.G_ID

        directorate_name = request.form.get('directorate_name')
        directorate_id = None
        if directorate_name:
            disc = Directorate.query.filter_by(Disc_Name=directorate_name).first()
            if not disc:
                disc = Directorate(Disc_Name=directorate_name, G_ID=g_id)
                db.session.add(disc)
                db.session.commit()
            directorate_id = disc.DiscID
        
        neighborhood = request.form.get('neighborhood')
        
        class_id = request.form.get('class_id')
        section_id = request.form.get('section_id')
        
        dob = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None

        photo = request.files.get('photo')
        photo_filename = None
        if photo and photo.filename:
            ext = os.path.splitext(photo.filename)[1]
            photo_filename = str(uuid.uuid4()) + ext
            photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'students', photo_filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            photo.save(photo_path)
            photo_filename = 'uploads/students/' + photo_filename
            
        new_student = Student(
            SName=name,
            Gender=gender,
            DOB=dob,
            Image=photo_filename,
            Parent_Name=parent_name,
            Parent_Number=parent_phone,
            Parent_Work=parent_work,
            CountryID=country_id if country_id else None,
            G_ID=g_id if g_id else None,
            DiscID=directorate_id if directorate_id else None,
            Neighborhood=neighborhood,
            CID=class_id if class_id else None,
            SectionID=section_id if section_id else None,
            Status=request.form.get('status', 'نشط')
        )
        try:
            db.session.add(new_student)
            db.session.commit()
            flash('تمت إضافة الطالب بنجاح', 'success')
            return redirect(url_for('students.home'))
        except Exception as e:
            db.session.rollback()
            flash(f'حدث خطأ أثناء حفظ بيانات الطالب: {str(e)}', 'danger')
            return redirect(url_for('students.add_student'))
        
    countries = Country.query.all()
    governorates = Governorates.query.all()
    directorates = Directorate.query.all()
    classes = Classes.query.all()
    sections = Sections.query.all()
    return render_template('add_student.html', countries=countries, governorates=governorates, directorates=directorates, classes=classes, sections=sections)

@students_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@admin_required
def edit_student(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    student = Student.query.get_or_404(id)
    
    if request.method == 'POST':
        student.SName = request.form.get('name')
        student.Gender = request.form.get('gender')
        
        dob_str = request.form.get('dob')
        student.DOB = datetime.strptime(dob_str, '%Y-%m-%d').date() if dob_str else None
        
        student.Parent_Name = request.form.get('parent_name')
        student.Parent_Number = request.form.get('parent_number')
        student.Parent_Work = request.form.get('parent_work')
        student.Neighborhood = request.form.get('neighborhood')
        
        country_name = request.form.get('country_name')
        if country_name:
            c = Country.query.filter_by(Country_Name=country_name).first()
            if not c:
                c = Country(Country_Name=country_name)
                db.session.add(c)
                db.session.commit()
            student.CountryID = c.CountryID
        else:
            student.CountryID = None
        
        g_name = request.form.get('g_name')
        if g_name:
            gov = Governorates.query.filter_by(G_Name=g_name).first()
            if not gov:
                gov = Governorates(G_Name=g_name, CountryID=student.CountryID)
                db.session.add(gov)
                db.session.commit()
            student.G_ID = gov.G_ID
        else:
            student.G_ID = None

        directorate_name = request.form.get('directorate_name')
        if directorate_name:
            disc = Directorate.query.filter_by(Disc_Name=directorate_name).first()
            if not disc:
                disc = Directorate(Disc_Name=directorate_name, G_ID=student.G_ID)
                db.session.add(disc)
                db.session.commit()
            student.DiscID = disc.DiscID
        else:
            student.DiscID = None
        
        class_id = request.form.get('class_id')
        student.CID = class_id if class_id else None
            
        section_id = request.form.get('section_id')
        student.SectionID = section_id if section_id else None
        
        status = request.form.get('status')
        if status:
            student.Status = status
        
        photo = request.files.get('photo')
        if photo and photo.filename:
            ext = os.path.splitext(photo.filename)[1]
            photo_filename = str(uuid.uuid4()) + ext
            photo_path = os.path.join(current_app.root_path, 'static', 'uploads', 'students', photo_filename)
            os.makedirs(os.path.dirname(photo_path), exist_ok=True)
            photo.save(photo_path)
            student.Image = 'uploads/students/' + photo_filename
            
        db.session.commit()
        flash('تم تحديث بيانات الطالب بنجاح', 'success')
        return redirect(url_for('students.home'))
        
    countries = Country.query.all()
    governorates = Governorates.query.all()
    directorates = Directorate.query.all()
    classes = Classes.query.all()
    sections = Sections.query.all()
    return render_template('edit_student.html', student=student, countries=countries, governorates=governorates, directorates=directorates, classes=classes, sections=sections)

@students_bp.route('/delete/<int:id>', methods=['POST'])
@admin_required
def delete_student(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
        
    student = Student.query.get_or_404(id)
    student.is_deleted = True
    db.session.commit()
    flash('تم حذف الطالب بنجاح', 'success')
    return redirect(url_for('students.home'))

@students_bp.route('/view/<int:id>')
def view_student(id):
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    student = Student.query.get_or_404(id)
    return render_template('view_student.html', student=student)
