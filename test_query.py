from app import create_app
from models import db, Teacher

app = create_app()
with app.app_context():
    try:
        teachers = Teacher.query.all()
        print("Success:", len(teachers))
    except Exception as e:
        print("Error:", str(e))
