from app import create_app
from models import db, Student

app = create_app()
with app.app_context():
    try:
        students = Student.query.all()
        print("Success Students:", len(students))
    except Exception as e:
        print("Error Students:", str(e))
