import os
import sys

sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from app import create_app

app = create_app()

def verify():
    print("--- Verifying Phase 2 Tasks ---\n")

    print("1. Checking Backend Strict Validation in api_routes.py")
    api_path = os.path.join(app.root_path, 'routes', 'api_routes.py')
    with open(api_path, 'r', encoding='utf-8') as f:
        api_content = f.read()
        if "teacher_sub_ids and int(data['subject_id']) not in teacher_sub_ids:" in api_content:
            print("[OK] Backend (API) STRICT validation found: prevents adding subject not linked to teacher.")
        else:
            print("[FAILED] Backend strict validation not found.")

    print("\n2. Checking Grid UI & Dynamic Colors in timetable/index.html")
    html_path = os.path.join(app.root_path, 'templates', 'timetable', 'index.html')
    with open(html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
        
        if "getSubjectColor(" in html_content and "hsl(" in html_content:
            print("[OK] Frontend logic for 'ألوان مختلفة لكل مادة' (Different colors per subject) found.")
        else:
            print("[FAILED] Subject coloring logic missing.")

        if "onclick=\"handleCellClick" in html_content or "cell.onclick = () => handleCellClick" in html_content:
            print("[OK] Frontend logic for 'الضغط على الخلية' (Click-to-Edit cell) found.")
        else:
            print("[FAILED] Click-to-Edit logic missing.")
            
        if "filterClass.addEventListener('change'" in html_content and "addSubject.innerHTML" in html_content:
            print("[OK] Frontend logic for 'تظهر فقط المواد الخاصة بهذا الصف' (Filter subjects by class) found.")
        else:
            print("[FAILED] Subject filtering by class logic missing.")

    print("\n--- All Phase 2 Checks Completed! ---")

if __name__ == "__main__":
    verify()
