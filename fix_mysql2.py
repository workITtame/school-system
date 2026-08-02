from app import create_app
from models import db
from sqlalchemy import text
from sqlalchemy.exc import OperationalError

app = create_app()

def alter_db():
    with app.app_context():
        queries = [
            "ALTER TABLE Teacher ADD COLUMN Gender VARCHAR(10)",
            "ALTER TABLE Teacher ADD COLUMN Notes TEXT"
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
