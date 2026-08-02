import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User

app = create_app()
with app.app_context():
    admin = User.query.filter_by(username='admin').first()
    if not admin:
        admin = User(username='admin', name='مدير النظام', role='admin')
        db.session.add(admin)
        print("Created new admin user.")
    
    admin.set_password('123456')
    db.session.commit()
    print("Admin user created/updated successfully.")
    print("Username: admin")
    print("Password: 123456")
