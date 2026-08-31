from .extensions import db, AuditMixin
from datetime import date

class Student(db.Model, AuditMixin):
    __tablename__ = 'student'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    SID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SName = db.Column(db.String(100), index=True)
    DOB = db.Column(db.Date)
    Gender = db.Column(db.String(10))
    Image = db.Column(db.String(255))
    CountryID = db.Column(db.Integer, db.ForeignKey('country.CountryID', ondelete='SET NULL'))
    G_ID = db.Column(db.Integer, db.ForeignKey('governorates.G_ID', ondelete='SET NULL'))
    DiscID = db.Column(db.Integer, db.ForeignKey('directorate.DiscID', ondelete='SET NULL'))
    Neighborhood = db.Column(db.String(100))
    Status = db.Column(db.String(20), default='نشط')
    
    CID = db.Column(db.Integer, db.ForeignKey('classes.CID', ondelete='RESTRICT'), index=True)
    SectionID = db.Column(db.Integer, db.ForeignKey('sections.SectionID', ondelete='RESTRICT'), index=True)

    Parent_Name = db.Column(db.String(100))
    Parent_Number = db.Column(db.String(20))
    Parent_Work = db.Column(db.String(100))
    
    # Relationships
    country = db.relationship('Country')
    governorate = db.relationship('Governorates')
    directorate = db.relationship('Directorate')
    school_class = db.relationship('Classes')
    section = db.relationship('Sections')

class Attendance(db.Model, AuditMixin):
    __tablename__ = 'attendance'
    __table_args__ = (
        db.UniqueConstraint('SID', 'Date', name='uq_student_date_attendance'),
        {'mysql_engine': 'InnoDB'}
    )
    AttendanceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('student.SID', ondelete='RESTRICT'), index=True)
    Date = db.Column(db.Date, index=True)
    Status = db.Column(db.String(10), index=True)
    
    student = db.relationship('Student', backref=db.backref('attendances', lazy=True))
