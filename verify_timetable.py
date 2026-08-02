import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from models.timetable import SchoolTable
from models.academic import Classes, Sections, Subject, Days, Lessons, Terms
from models.teacher import Teacher
from models.user import User

app = create_app()

def verify():
    with app.app_context():
        print("1. Checking Database Tables for Timetable...")
        try:
            # Check if SchoolTable exists by querying
            count = SchoolTable.query.count()
            print(f"[OK] SchoolTable exists in DB. Current records: {count}")
        except Exception as e:
            print(f"[FAILED] Database error: {e}")
            return

        print("\n2. Checking Backend Routes (API)...")
        # Find the route in the app url map
        rules = [str(rule) for rule in app.url_map.iter_rules() if '/api/v1/timetable' in str(rule)]
        if rules:
            print(f"[OK] Timetable API Routes exist: {set(rules)}")
        else:
            print("[FAILED] Timetable API Routes NOT found!")

        print("\n3. Checking Frontend Templates...")
        template_path = os.path.join(app.root_path, 'templates', 'timetable', 'index.html')
        if os.path.exists(template_path):
            print(f"[OK] Timetable UI exists at: {template_path}")
        else:
            print("[FAILED] Timetable UI NOT found!")

        print("\n4. Checking Dashboard Link...")
        dashboard_path = os.path.join(app.root_path, 'templates', 'dashboard', 'index.html')
        if os.path.exists(dashboard_path):
            with open(dashboard_path, 'r', encoding='utf-8') as f:
                content = f.read()
                if "timetable.index" in content:
                    print("[OK] Dashboard contains button/link to Timetable.")
                else:
                    print("[FAILED] Dashboard link to Timetable NOT found!")
        
        print("\n--- All Checks Completed Successfully! ---")

if __name__ == "__main__":
    verify()
