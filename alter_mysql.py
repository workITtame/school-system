from app import create_app
from models import db
from sqlalchemy import text

app = create_app()

def alter_db():
    with app.app_context():
        queries = [
            "ALTER TABLE Student ADD COLUMN Status VARCHAR(20) DEFAULT 'نشط'",
            "ALTER TABLE Teacher ADD COLUMN Status VARCHAR(20) DEFAULT 'نشط'",
            "ALTER TABLE Classes ADD COLUMN Stage VARCHAR(50)",
            "ALTER TABLE Subject ADD COLUMN Type VARCHAR(50)",
            "ALTER TABLE Subject ADD COLUMN Department VARCHAR(50)",
            "ALTER TABLE Subject ADD COLUMN Status VARCHAR(20) DEFAULT 'نشط'"
        ]
        
        for q in queries:
            try:
                db.session.execute(text(q))
                print(f"Success: {q}")
            except Exception as e:
                print(f"Failed or already exists: {q} \nError: {e}")
                
        db.session.commit()
        print("Creating any missing tables (like ExamSchedule)...")
        db.create_all()
        print("Done!")

if __name__ == '__main__':
    alter_db()
