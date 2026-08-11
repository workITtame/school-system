from .extensions import db, AuditMixin

class Marks(db.Model, AuditMixin):
    __tablename__ = 'Marks'
    M_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('Student.SID'), index=True)
    SubID = db.Column(db.Integer, db.ForeignKey('Subject.SubID'), index=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('TypeExams.ExamID'), nullable=True)
    HomeworkID = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=True)
    assessment_type = db.Column(db.String(20), default='exam', nullable=False)
    assessment_id = db.Column(db.Integer, nullable=True)
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teacher.TeacherID'))
    Score = db.Column(db.Numeric(5, 2))
    MaxScore = db.Column(db.Numeric(5, 2), default=100)   # الدرجة الكاملة
    Grade = db.Column(db.String(5))
    Percentage = db.Column(db.Numeric(5, 2), nullable=True)  # النسبة المئوية
    T_ID = db.Column(db.Integer, db.ForeignKey('Terms.T_ID'))
    Notes = db.Column(db.String(255), nullable=True)      # ملاحظات المعلم

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_marks_score_range'),
    )

    # Relationships
    student = db.relationship('Student')
    subject = db.relationship('Subject')
    exam = db.relationship('TypeExams')
    homework = db.relationship('Homework')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')

class DetailMarks(db.Model, AuditMixin):
    __tablename__ = 'DetailMarks'
    DT_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('Student.SID'), index=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('TypeExams.ExamID'), nullable=True)
    HomeworkID = db.Column(db.Integer, db.ForeignKey('homework.id'), nullable=True)
    assessment_type = db.Column(db.String(20), default='exam', nullable=False)
    assessment_id = db.Column(db.Integer, nullable=True)
    SubID = db.Column(db.Integer, db.ForeignKey('Subject.SubID'), index=True)
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teacher.TeacherID'))
    Score = db.Column(db.Numeric(5, 2))
    MaxScore = db.Column(db.Numeric(5, 2), default=100)
    T_ID = db.Column(db.Integer, db.ForeignKey('Terms.T_ID'))

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_detail_marks_score_range'),
    )

    # Relationships
    student = db.relationship('Student')
    exam = db.relationship('TypeExams')
    homework = db.relationship('Homework')
    subject = db.relationship('Subject')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')

class HomeworkMarks(db.Model, AuditMixin):
    __tablename__ = 'HomeworkMarks'
    HM_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('Student.SID'), index=True, nullable=False)
    SubID = db.Column(db.Integer, db.ForeignKey('Subject.SubID'), index=True, nullable=True)
    HomeworkID = db.Column(db.Integer, db.ForeignKey('homework.id'), index=True, nullable=False)
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teacher.TeacherID'), nullable=True)
    Score = db.Column(db.Numeric(5, 2), nullable=True)
    MaxScore = db.Column(db.Numeric(5, 2), default=100)
    Percentage = db.Column(db.Numeric(5, 2), nullable=True)
    Grade = db.Column(db.String(5), nullable=True)
    T_ID = db.Column(db.Integer, db.ForeignKey('Terms.T_ID'), nullable=True)
    Notes = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_homework_marks_score_range'),
        db.UniqueConstraint('SID', 'HomeworkID', name='uq_student_homework_marks'),
    )

    # Relationships
    student = db.relationship('Student')
    subject = db.relationship('Subject')
    homework = db.relationship('Homework')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')
