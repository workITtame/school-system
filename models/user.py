from .extensions import db, AuditMixin, bcrypt
from flask_login import UserMixin
from datetime import datetime
from werkzeug.security import check_password_hash as check_werkzeug

class User(db.Model, UserMixin, AuditMixin):
    __tablename__ = 'users'
    __table_args__ = {'mysql_engine': 'InnoDB'}
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='teacher') # 'admin' or 'teacher'
    name = db.Column(db.String(100), nullable=False)
    
    # Brute-force protection
    failed_login_attempts = db.Column(db.Integer, default=0)
    locked_until = db.Column(db.DateTime, nullable=True)
    last_login = db.Column(db.DateTime, nullable=True)
    
    teacher_profile = db.relationship('Teacher', back_populates='user', uselist=False, cascade='all, delete-orphan')

    def set_password(self, password):
        self.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')

    def check_password(self, password):
        if not self.password_hash:
            return False

        # إذا كان hash قديم (scrypt أو pbkdf2)
        if self.password_hash.startswith('scrypt:') or self.password_hash.startswith('pbkdf2:'):
            if check_werkzeug(self.password_hash, password):
                # 🔥 تحويل إلى bcrypt
                self.set_password(password)
                db.session.commit()
                return True
            return False

        # bcrypt
        return bcrypt.check_password_hash(self.password_hash, password)

    def is_locked(self):
        if self.locked_until and self.locked_until > datetime.utcnow():
            return True
        return False
