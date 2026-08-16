from .extensions import db
from datetime import datetime

class Homework(db.Model):
    __tablename__ = 'homework'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(150), nullable=False)
    sub_id = db.Column(db.Integer, db.ForeignKey('subject.SubID', ondelete='RESTRICT'), nullable=False)
    class_id = db.Column(db.Integer, db.ForeignKey('classes.CID', ondelete='RESTRICT'), nullable=False)
    section_id = db.Column(db.Integer, db.ForeignKey('sections.SectionID', ondelete='RESTRICT'), nullable=True)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='مكتمل') # مكتمل, معلق, متأخر
    description = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    subject = db.relationship('Subject', backref='homeworks')
    school_class = db.relationship('Classes', backref='homeworks')
    section = db.relationship('Sections', backref='homeworks')
