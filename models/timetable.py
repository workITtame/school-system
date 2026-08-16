from .extensions import db, AuditMixin

class TypeExams(db.Model, AuditMixin):
    __tablename__ = 'typeexams'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    ExamID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamName = db.Column(db.String(100))

class SchoolTable(db.Model, AuditMixin):
    __tablename__ = 'schooltable'
    SchoolTableID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    CID = db.Column(db.Integer, db.ForeignKey('classes.CID', ondelete='RESTRICT'), index=True)
    SectionID = db.Column(db.Integer, db.ForeignKey('sections.SectionID', ondelete='RESTRICT'), index=True)
    DayID = db.Column(db.Integer, db.ForeignKey('days.DayID', ondelete='RESTRICT'))
    LessonID = db.Column(db.Integer, db.ForeignKey('lessons.LessonID', ondelete='RESTRICT'))
    TeacherID = db.Column(db.Integer, db.ForeignKey('teacher.TeacherID', ondelete='RESTRICT'), index=True)
    SubID = db.Column(db.Integer, db.ForeignKey('subject.SubID', ondelete='RESTRICT'))
    T_ID = db.Column(db.Integer, db.ForeignKey('terms.T_ID', ondelete='RESTRICT'))

    # Unique constraint per class/section/day/lesson
    __table_args__ = (
        db.UniqueConstraint('CID', 'SectionID', 'DayID', 'LessonID', name='uix_timetable_slot'),
        db.UniqueConstraint('TeacherID', 'DayID', 'LessonID', name='uix_teacher_timetable_slot'),
        {'mysql_engine': 'InnoDB'}
    )

    # Relationships
    school_class = db.relationship('Classes')
    section = db.relationship('Sections')
    day = db.relationship('Days')
    lesson = db.relationship('Lessons')
    teacher = db.relationship('Teacher')
    subject = db.relationship('Subject')
    term = db.relationship('Terms')

class SchoolTableTypeExam(db.Model, AuditMixin):
    __tablename__ = 'schooltabletypeexam'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('typeexams.ExamID', ondelete='CASCADE'))
    SchoolTableID = db.Column(db.Integer, db.ForeignKey('schooltable.SchoolTableID', ondelete='CASCADE'))
    
    exam = db.relationship('TypeExams')
    timetable_entry = db.relationship('SchoolTable')
