from .extensions import db, AuditMixin

class Qualifications(db.Model, AuditMixin):
    __tablename__ = 'qualifications'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    QID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    QName = db.Column(db.String(100))
    
    # Relationships
    teachers = db.relationship('Teacher', back_populates='qualification', lazy=True)

class Teacher(db.Model, AuditMixin):
    __tablename__ = 'teacher'
    TeacherID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    TeacherName = db.Column(db.String(100), index=True)
    Email = db.Column(db.String(100), unique=True, index=True)
    Phone = db.Column(db.String(20))
    Password = db.Column(db.String(255))
    Image = db.Column(db.String(255))
    Gender = db.Column(db.String(10))          # ذكر / أنثى
    DOB = db.Column(db.Date)
    POB = db.Column(db.String(100))
    TeacherTitle = db.Column(db.String(50))
    Salary = db.Column(db.Numeric(10, 2))
    Currency = db.Column(db.String(10))
    QID = db.Column(db.Integer, db.ForeignKey('qualifications.QID', ondelete='SET NULL'))
    Status = db.Column(db.String(20), default='نشط')
    Notes = db.Column(db.Text, nullable=True)  # ملاحظات
    Bio = db.Column(db.Text, nullable=True)
    Qualification = db.Column(db.String(255), nullable=True)
    OfficeHours = db.Column(db.String(255), nullable=True)
    Specialization = db.Column(db.String(255), nullable=True)
    Preferences = db.Column(db.Text, nullable=True)
    
    __table_args__ = (
        db.CheckConstraint('Salary >= 0', name='check_salary_positive'),
        {'mysql_engine': 'InnoDB'}
    )
    
    # Relationships
    qualification = db.relationship('Qualifications', back_populates='teachers')
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    user = db.relationship('User', back_populates='teacher_profile')
    subjects = db.relationship('Subject', secondary='teachersubject', backref=db.backref('teachers', lazy='dynamic'))
