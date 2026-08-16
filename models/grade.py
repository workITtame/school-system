from .extensions import db, AuditMixin

class Marks(db.Model, AuditMixin):
    __tablename__ = 'marks'
    M_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('student.SID', ondelete='RESTRICT'), index=True)
    SubID = db.Column(db.Integer, db.ForeignKey('subject.SubID', ondelete='RESTRICT'), index=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('typeexams.ExamID', ondelete='SET NULL'), nullable=True)
    HomeworkID = db.Column(db.Integer, db.ForeignKey('homework.id', ondelete='SET NULL'), nullable=True)
    assessment_type = db.Column(db.String(20), default='exam', nullable=False)
    assessment_id = db.Column(db.Integer, nullable=True)
    TeacherID = db.Column(db.Integer, db.ForeignKey('teacher.TeacherID', ondelete='SET NULL'))
    Score = db.Column(db.Numeric(5, 2))
    MaxScore = db.Column(db.Numeric(5, 2), default=100)   # الدرجة الكاملة
    Grade = db.Column(db.String(5))
    Percentage = db.Column(db.Numeric(5, 2), nullable=True)  # النسبة المئوية
    T_ID = db.Column(db.Integer, db.ForeignKey('terms.T_ID', ondelete='RESTRICT'))
    Notes = db.Column(db.String(255), nullable=True)      # ملاحظات المعلم

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_marks_score_range'),
        db.UniqueConstraint('SID', 'ExamID', name='uq_student_exam_marks'),
        {'mysql_engine': 'InnoDB'}
    )

    # Relationships
    student = db.relationship('Student')
    subject = db.relationship('Subject')
    exam = db.relationship('TypeExams')
    homework = db.relationship('Homework')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')

class DetailMarks(db.Model, AuditMixin):
    __tablename__ = 'detailmarks'
    DT_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('student.SID', ondelete='RESTRICT'), index=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('typeexams.ExamID', ondelete='SET NULL'), nullable=True)
    HomeworkID = db.Column(db.Integer, db.ForeignKey('homework.id', ondelete='SET NULL'), nullable=True)
    assessment_type = db.Column(db.String(20), default='exam', nullable=False)
    assessment_id = db.Column(db.Integer, nullable=True)
    SubID = db.Column(db.Integer, db.ForeignKey('subject.SubID', ondelete='RESTRICT'), index=True)
    TeacherID = db.Column(db.Integer, db.ForeignKey('teacher.TeacherID', ondelete='SET NULL'))
    Score = db.Column(db.Numeric(5, 2))
    MaxScore = db.Column(db.Numeric(5, 2), default=100)
    T_ID = db.Column(db.Integer, db.ForeignKey('terms.T_ID', ondelete='RESTRICT'))

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_detail_marks_score_range'),
        {'mysql_engine': 'InnoDB'}
    )

    # Relationships
    student = db.relationship('Student')
    exam = db.relationship('TypeExams')
    homework = db.relationship('Homework')
    subject = db.relationship('Subject')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')

class HomeworkMarks(db.Model, AuditMixin):
    __tablename__ = 'homeworkmarks'
    HM_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('student.SID', ondelete='RESTRICT'), index=True, nullable=False)
    SubID = db.Column(db.Integer, db.ForeignKey('subject.SubID', ondelete='RESTRICT'), index=True, nullable=True)
    HomeworkID = db.Column(db.Integer, db.ForeignKey('homework.id', ondelete='RESTRICT'), index=True, nullable=False)
    TeacherID = db.Column(db.Integer, db.ForeignKey('teacher.TeacherID', ondelete='SET NULL'), nullable=True)
    Score = db.Column(db.Numeric(5, 2), nullable=True)
    MaxScore = db.Column(db.Numeric(5, 2), default=10)
    Percentage = db.Column(db.Numeric(5, 2), nullable=True)
    Grade = db.Column(db.String(5), nullable=True)
    T_ID = db.Column(db.Integer, db.ForeignKey('terms.T_ID', ondelete='RESTRICT'), nullable=True)
    Notes = db.Column(db.String(255), nullable=True)

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_homework_marks_score_range'),
        db.UniqueConstraint('SID', 'HomeworkID', name='uq_student_homework_marks'),
        {'mysql_engine': 'InnoDB'}
    )

    # Relationships
    student = db.relationship('Student')
    subject = db.relationship('Subject')
    homework = db.relationship('Homework')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')
