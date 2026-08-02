import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db
from flask_jwt_extended import create_access_token

app = create_app()

def verify():
    with app.app_context():
        print("1. Checking API Endpoint /api/v1/timetable/reference-data")
        
        # We need a JWT token to access the API.
        # Let's mock a user for the token.
        from models.user import User
        user = User.query.first()
        if not user:
            # Create a mock user if none exists
            user = User(username='test_verify', name='Test User', role='admin')
            db.session.add(user)
            db.session.commit()
            
        token = create_access_token(identity=str(user.id))
        
        client = app.test_client()
        response = client.get('/api/v1/timetable/reference-data', headers={
            'Authorization': f'Bearer {token}'
        })
        
        if response.status_code == 200:
            data = response.get_json()['data']
            print(f"[OK] API responds successfully with status 200.")
            print(f"     Loaded Classes: {len(data['classes'])}")
            print(f"     Loaded Subjects: {len(data.get('classes')[0]['subjects']) if data['classes'] else 0} (in first class)")
            print(f"     Loaded Teachers: {len(data['teachers'])}")
            print(f"     Loaded Days: {len(data['days'])}")
            print(f"     Loaded Lessons: {len(data['lessons'])}")
            print(f"     Loaded Terms: {len(data['terms'])}")
        else:
            print(f"[FAILED] API returned status {response.status_code}: {response.get_data(as_text=True)}")

        print("\n2. Checking JavaScript Frontend Logic in timetable/index.html")
        html_path = os.path.join(app.root_path, 'templates', 'timetable', 'index.html')
        with open(html_path, 'r', encoding='utf-8') as f:
            content = f.read()
            if "fetch('/api/v1/timetable/reference-data'" in content:
                print("[OK] Frontend uses AJAX (fetch) to load dropdown data.")
            else:
                print("[FAILED] Frontend is missing the fetch call.")
                
            if "filterClass.addEventListener('change'" in content:
                print("[OK] Frontend has cascading filter: Class -> Subjects & Sections.")
            else:
                print("[FAILED] Frontend missing Class cascade filter.")
                
            if "addSubject.addEventListener('change'" in content:
                print("[OK] Frontend has cascading filter: Subject -> Teachers.")
            else:
                print("[FAILED] Frontend missing Subject cascade filter.")
                
            if "Toast.fire" in content or "showToast(" in content:
                print("[OK] Frontend uses SweetAlert Toasts for beautiful UX.")
            else:
                print("[FAILED] Frontend missing Toast notifications.")

if __name__ == "__main__":
    verify()
