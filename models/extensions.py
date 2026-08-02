from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from flask_caching import Cache
from flask_marshmallow import Marshmallow
from flask_bcrypt import Bcrypt
from flask_login import LoginManager
from flask_jwt_extended import JWTManager

db = SQLAlchemy()
cache = Cache()
ma = Marshmallow()
bcrypt = Bcrypt()
login_manager = LoginManager()
jwt = JWTManager()

class AuditMixin:
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_deleted = db.Column(db.Boolean, default=False)
