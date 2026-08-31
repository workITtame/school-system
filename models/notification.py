from .extensions import db
from datetime import datetime

class Notification(db.Model):
    __tablename__ = 'notifications'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True)
    title = db.Column(db.String(150), nullable=False)
    message = db.Column(db.Text, nullable=False)
    notification_type = db.Column(db.String(50), nullable=True, default='general')
    action_url = db.Column(db.String(255), nullable=True)
    priority = db.Column(db.String(20), nullable=True, default='normal')
    is_read = db.Column(db.Boolean, default=False, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    read_at = db.Column(db.DateTime, nullable=True)

    user = db.relationship('User', backref=db.backref('notifications', lazy=True, cascade='all, delete-orphan'))
