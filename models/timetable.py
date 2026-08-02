from .extensions import db, AuditMixin

class TypeExams(db.Model, AuditMixin):
    __tablename__ = 'TypeExams'
    ExamID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamName = db.Column(db.String(100))

class SchoolTable(db.Model, AuditMixin):
    __tablename__ = 'SchoolTable'
    SchoolTableID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    
    CID = db.Column(db.Integer, db.ForeignKey('Classes.CID'), index=True)
    SectionID = db.Column(db.Integer, db.ForeignKey('Sections.SectionID'), index=True)
    DayID = db.Column(db.Integer, db.ForeignKey('Days.DayID'))
    LessonID = db.Column(db.Integer, db.ForeignKey('Lessons.LessonID'))
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teacher.TeacherID'), index=True)
    SubID = db.Column(db.Integer, db.ForeignKey('Subject.SubID'))
    T_ID = db.Column(db.Integer, db.ForeignKey('Terms.T_ID'))

    # Unique constraint per class/section/day/lesson
    __table_args__ = (
        db.UniqueConstraint('CID', 'SectionID', 'DayID', 'LessonID', name='uix_timetable_slot'),
        db.UniqueConstraint('TeacherID', 'DayID', 'LessonID', name='uix_teacher_timetable_slot'),
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
    __tablename__ = 'SchoolTableTypeExam'
    ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('TypeExams.ExamID'))
    SchoolTableID = db.Column(db.Integer, db.ForeignKey('SchoolTable.SchoolTableID'))
    
    exam = db.relationship('TypeExams')
    timetable_entry = db.relationship('SchoolTable')
