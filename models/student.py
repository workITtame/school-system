from .extensions import db, AuditMixin
from datetime import date

class Student(db.Model, AuditMixin):
    __tablename__ = 'Student'
    SID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SName = db.Column(db.String(100), index=True)
    DOB = db.Column(db.Date)
    Gender = db.Column(db.String(10))
    Image = db.Column(db.String(255))
    CountryID = db.Column(db.Integer, db.ForeignKey('Country.CountryID'))
    G_ID = db.Column(db.Integer, db.ForeignKey('Governorates.G_ID'))
    DiscID = db.Column(db.Integer, db.ForeignKey('Directorate.DiscID'))
    Neighborhood = db.Column(db.String(100))
    Status = db.Column(db.String(20), default='نشط')
    
    CID = db.Column(db.Integer, db.ForeignKey('Classes.CID'), index=True)
    SectionID = db.Column(db.Integer, db.ForeignKey('Sections.SectionID'), index=True)

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
    __tablename__ = 'Attendance'
    AttendanceID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('Student.SID', ondelete='CASCADE'))
    Date = db.Column(db.Date)
    Status = db.Column(db.String(10))
    
    student = db.relationship('Student', backref=db.backref('attendances', lazy=True))
