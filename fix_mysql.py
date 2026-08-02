from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

def alter_db():
    with app.app_context():
        queries = [
            "ALTER TABLE Subject ADD COLUMN WeeklyHours INT DEFAULT 0",
            "ALTER TABLE Subject ADD COLUMN Color VARCHAR(20) DEFAULT '#e2e8f0'",
            "ALTER TABLE Classes ADD COLUMN MaxStudents INT DEFAULT 40",
            "ALTER TABLE Sections ADD COLUMN MaxStudents INT DEFAULT 40",
            "ALTER TABLE Lessons ADD COLUMN StartTime VARCHAR(10)",
            "ALTER TABLE Lessons ADD COLUMN EndTime VARCHAR(10)",
            "ALTER TABLE Terms ADD COLUMN AcademicYear VARCHAR(20)",
            "ALTER TABLE ExamSchedule ADD COLUMN Duration INT DEFAULT 60",
            "ALTER TABLE ExamSchedule ADD COLUMN Location VARCHAR(100)"
        ]
        
        for q in queries:
            try:
                db.session.execute(text(q))
                print(f"Success: {q}")
            except Exception as e:
                print(f"Failed or already exists: {q} \nError: {e}")
                
        db.session.commit()
        db.create_all()
        print("Done fixing MySQL DB!")

if __name__ == '__main__':
    alter_db()
