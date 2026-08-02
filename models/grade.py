from .extensions import db, AuditMixin

class Marks(db.Model, AuditMixin):
    __tablename__ = 'Marks'
    M_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('Student.SID'), index=True)
    SubID = db.Column(db.Integer, db.ForeignKey('Subject.SubID'), index=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('TypeExams.ExamID'))
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teacher.TeacherID'))
    Score = db.Column(db.Numeric(5, 2))
    MaxScore = db.Column(db.Numeric(5, 2), default=100)   # الدرجة الكاملة
    Grade = db.Column(db.String(5))
    Percentage = db.Column(db.Numeric(5, 2), nullable=True)  # النسبة المئوية
    T_ID = db.Column(db.Integer, db.ForeignKey('Terms.T_ID'))
    Notes = db.Column(db.String(255), nullable=True)      # ملاحظات المعلم

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_marks_score_range'),
        db.UniqueConstraint('SID', 'SubID', 'ExamID', 'T_ID', name='uix_student_exam_mark'),
    )

    # Relationships
    student = db.relationship('Student')
    subject = db.relationship('Subject')
    exam = db.relationship('TypeExams')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')

class DetailMarks(db.Model, AuditMixin):
    __tablename__ = 'DetailMarks'
    DT_ID = db.Column(db.Integer, primary_key=True, autoincrement=True)
    SID = db.Column(db.Integer, db.ForeignKey('Student.SID'), index=True)
    ExamID = db.Column(db.Integer, db.ForeignKey('TypeExams.ExamID'))
    SubID = db.Column(db.Integer, db.ForeignKey('Subject.SubID'), index=True)
    TeacherID = db.Column(db.Integer, db.ForeignKey('Teacher.TeacherID'))
    Score = db.Column(db.Numeric(5, 2))
    MaxScore = db.Column(db.Numeric(5, 2), default=100)
    T_ID = db.Column(db.Integer, db.ForeignKey('Terms.T_ID'))

    __table_args__ = (
        db.CheckConstraint('Score >= 0 AND Score <= 100', name='check_detail_marks_score_range'),
        db.UniqueConstraint('SID', 'SubID', 'ExamID', 'T_ID', name='uix_student_exam_detail_mark'),
    )

    # Relationships
    student = db.relationship('Student')
    exam = db.relationship('TypeExams')
    subject = db.relationship('Subject')
    teacher = db.relationship('Teacher')
    term = db.relationship('Terms')
