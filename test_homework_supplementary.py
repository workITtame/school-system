from app import create_app
from models import db, Homework, Subject, Classes, Sections
from datetime import date, timedelta

def run_supp_audit():
    app = create_app()
    with app.app_context():
        # Check permissions & edge cases
        sub = Subject.query.first()
        c = Classes.query.first()
        
        # Test past due date handling
        past_date = date.today() - timedelta(days=5)
        hw_past = Homework(
            title="واجب بتاريخ سابق (اختبار)",
            sub_id=sub.SubID,
            class_id=c.CID,
            due_date=past_date,
            status="متأخر"
        )
        db.session.add(hw_past)
        db.session.commit()
        
        past_id = hw_past.id
        print("Past Due Date Homework Created:", past_id)
        
        # Clean up
        db.session.delete(hw_past)
        db.session.commit()
        print("Past Due Date Cleaned Up Successfully")

if __name__ == "__main__":
    run_supp_audit()
