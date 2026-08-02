from .extensions import db, AuditMixin

# Association Table for Classes and Sections
ClassesSections = db.Table('ClassesSections',
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('CID', db.Integer, db.ForeignKey('Classes.CID')),
    db.Column('SectionID', db.Integer, db.ForeignKey('Sections.SectionID'))
)

# Association Table for Subject and Classes
ClassSubject = db.Table('ClassSubject',
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('SubID', db.Integer, db.ForeignKey('Subject.SubID')),
    db.Column('CID', db.Integer, db.ForeignKey('Classes.CID'))
)

# Association Table for Subject and Teacher
TeacherSubject = db.Table('TeacherSubject',
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('SubID', db.Integer, db.ForeignKey('Subject.SubID')),
    db.Column('TeacherID', db.Integer, db.ForeignKey('Teacher.TeacherID'))
)

class Classes(db.Model, AuditMixin):
    __tablename__ = 'Classes'
    CID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CName = db.Column(db.String(50), unique=True)
    Stage = db.Column(db.String(50))           # الثانوية, المتوسطة, الابتدائية
    MaxStudents = db.Column(db.Integer, default=40)  # الحد الأقصى للطلاب
    
    sections = db.relationship('Sections', secondary=ClassesSections, backref=db.backref('classes', lazy='dynamic'))
    subjects = db.relationship('Subject', secondary=ClassSubject, backref=db.backref('classes', lazy='dynamic'))

class Sections(db.Model, AuditMixin):
    __tablename__ = 'Sections'
    SectionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SectionName = db.Column(db.String(10))
    MaxStudents = db.Column(db.Integer, default=40)  # الحد الأقصى للطلاب في الشعبة

class Subject(db.Model, AuditMixin):
    __tablename__ = 'Subject'
    SubID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubName = db.Column(db.String(100), unique=True)
    Type = db.Column(db.String(50))            # أساسية, اختيارية
    Department = db.Column(db.String(50))      # علمي, أدبي, جميع المراحل
    WeeklyHours = db.Column(db.Integer, default=0)  # الحصص الأسبوعية
    Status = db.Column(db.String(20), default='نشط')
    Color = db.Column(db.String(20), default='#e2e8f0')  # لون المادة في الجدول

class Days(db.Model, AuditMixin):
    __tablename__ = 'Days'
    DayID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DName = db.Column(db.String(20))

class Lessons(db.Model, AuditMixin):
    __tablename__ = 'Lessons'
    LessonID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    LessonName = db.Column(db.String(50))
    StartTime = db.Column(db.String(10), nullable=True)   # وقت البداية مثل 08:00
    EndTime = db.Column(db.String(10), nullable=True)     # وقت النهاية مثل 08:45

class Terms(db.Model, AuditMixin):
    __tablename__ = 'Terms'
    T_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    T_Name = db.Column(db.String(50))
    AcademicYear = db.Column(db.String(20), nullable=True)  # السنة الدراسية مثل 2024-2025

class ExamSchedule(db.Model, AuditMixin):
    __tablename__ = 'ExamSchedule'
    ScheduleID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamName = db.Column(db.String(100))
    SubID = db.Column(db.Integer, db.ForeignKey('Subject.SubID'))
    CID = db.Column(db.Integer, db.ForeignKey('Classes.CID'))
    SectionID = db.Column(db.Integer, db.ForeignKey('Sections.SectionID'))
    T_ID = db.Column(db.Integer, db.ForeignKey('Terms.T_ID'), nullable=True)
    ExamDate = db.Column(db.Date)
    ExamTime = db.Column(db.String(50))
    Duration = db.Column(db.Integer, default=60)   # مدة الامتحان بالدقائق
    Location = db.Column(db.String(100), nullable=True)  # قاعة الامتحان
    Status = db.Column(db.String(20), default='مجدول')   # مجدول, جارية, منتهية
    
    subject = db.relationship('Subject')
    school_class = db.relationship('Classes')
    section = db.relationship('Sections')
    term = db.relationship('Terms')
