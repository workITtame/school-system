from .extensions import db, AuditMixin

# Association Table for Classes and Sections
ClassesSections = db.Table('classessections',
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('CID', db.Integer, db.ForeignKey('classes.CID', ondelete='CASCADE')),
    db.Column('SectionID', db.Integer, db.ForeignKey('sections.SectionID', ondelete='CASCADE')),
    mysql_engine='InnoDB'
)

# Association Table for Subject and Classes
ClassSubject = db.Table('classsubject',
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('SubID', db.Integer, db.ForeignKey('subject.SubID', ondelete='CASCADE')),
    db.Column('CID', db.Integer, db.ForeignKey('classes.CID', ondelete='CASCADE')),
    mysql_engine='InnoDB'
)

# Association Table for Subject and Teacher
TeacherSubject = db.Table('teachersubject',
    db.Column('ID', db.Integer, primary_key=True, autoincrement=True),
    db.Column('SubID', db.Integer, db.ForeignKey('subject.SubID', ondelete='CASCADE')),
    db.Column('TeacherID', db.Integer, db.ForeignKey('teacher.TeacherID', ondelete='CASCADE')),
    mysql_engine='InnoDB'
)

class Classes(db.Model, AuditMixin):
    __tablename__ = 'classes'
    __table_args__ = (
        db.UniqueConstraint('CName', 'Stage', name='uq_class_name_stage'),
        {'mysql_engine': 'InnoDB'}
    )
    CID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    CName = db.Column(db.String(50), nullable=False)
    Stage = db.Column(db.String(50))           # الثانوية, المتوسطة, الابتدائية
    MaxStudents = db.Column(db.Integer, default=40)  # الحد الأقصى للطلاب
    
    sections = db.relationship('Sections', secondary='classessections', backref=db.backref('classes', lazy='dynamic'))
    subjects = db.relationship('Subject', secondary='classsubject', backref=db.backref('classes', lazy='dynamic'))

class Sections(db.Model, AuditMixin):
    __tablename__ = 'sections'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    SectionID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SectionName = db.Column(db.String(10))
    MaxStudents = db.Column(db.Integer, default=40)  # الحد الأقصى للطلاب في الشعبة

class Subject(db.Model, AuditMixin):
    __tablename__ = 'subject'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    SubID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SubName = db.Column(db.String(100), unique=True)
    Type = db.Column(db.String(50))            # أساسية, اختيارية
    Department = db.Column(db.String(50))      # علمي, أدبي, جميع المراحل
    WeeklyHours = db.Column(db.Integer, default=0)  # الحصص الأسبوعية
    Status = db.Column(db.String(20), default='نشط')
    Color = db.Column(db.String(20), default='#e2e8f0')  # لون المادة في الجدول

class Days(db.Model, AuditMixin):
    __tablename__ = 'days'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    DayID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    DName = db.Column(db.String(20))

class Lessons(db.Model, AuditMixin):
    __tablename__ = 'lessons'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    LessonID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    LessonName = db.Column(db.String(50))
    StartTime = db.Column(db.String(10), nullable=True)   # وقت البداية مثل 08:00
    EndTime = db.Column(db.String(10), nullable=True)     # وقت النهاية مثل 08:45

class Terms(db.Model, AuditMixin):
    __tablename__ = 'terms'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    T_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    T_Name = db.Column(db.String(50))
    AcademicYear = db.Column(db.String(20), nullable=True)  # السنة الدراسية مثل 2024-2025

class ExamSchedule(db.Model, AuditMixin):
    __tablename__ = 'examschedule'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    ScheduleID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamName = db.Column(db.String(100))
    SubID = db.Column(db.Integer, db.ForeignKey('subject.SubID', ondelete='RESTRICT'))
    CID = db.Column(db.Integer, db.ForeignKey('classes.CID', ondelete='RESTRICT'))
    SectionID = db.Column(db.Integer, db.ForeignKey('sections.SectionID', ondelete='RESTRICT'))
    T_ID = db.Column(db.Integer, db.ForeignKey('terms.T_ID', ondelete='RESTRICT'), nullable=True)
    ExamDate = db.Column(db.Date)
    ExamTime = db.Column(db.String(50))
    Duration = db.Column(db.Integer, default=60)   # مدة الامتحان بالدقائق
    Location = db.Column(db.String(100), nullable=True)  # قاعة الامتحان
    Status = db.Column(db.String(20), default='مجدول')   # مجدول, جارية, منتهية
    
    subject = db.relationship('Subject')
    school_class = db.relationship('Classes')
    section = db.relationship('Sections')
    term = db.relationship('Terms')
