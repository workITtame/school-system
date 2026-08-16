from .extensions import db, AuditMixin

class School(db.Model, AuditMixin):
    __tablename__ = 'school'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    SchoolID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SchoolName = db.Column(db.String(100))
    SchoolType = db.Column(db.String(50))
    Phone = db.Column(db.String(20))
    Email = db.Column(db.String(100))
    Country = db.Column(db.String(50))
    City = db.Column(db.String(50))
    Governorate = db.Column(db.String(50))
    Directorate = db.Column(db.String(50))
    Neighborhood = db.Column(db.String(50))
    EstablishedYear = db.Column(db.Integer)
    Logo = db.Column(db.String(255))
    NotifyAttendanceEmail = db.Column(db.Boolean, default=True)
    NotifyGradesEnabled = db.Column(db.Boolean, default=True)
