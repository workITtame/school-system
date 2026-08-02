from app import create_app
import re

app = create_app()

def inspect_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read()

# Let's inspect route files
student_routes = inspect_file('routes/student_routes.py')
teacher_routes = inspect_file('routes/teacher_routes.py')
academic_routes = inspect_file('routes/academic_routes.py')
timetable_routes = inspect_file('routes/timetable_routes.py')
homework_routes = inspect_file('routes/homework_routes.py')
exam_routes = inspect_file('routes/exam_routes.py')
grade_routes = inspect_file('routes/grade_routes.py')
attendance_routes = inspect_file('routes/attendance_routes.py')
messages_routes = inspect_file('routes/messages_routes.py')
user_routes = inspect_file('routes/user_routes.py')
settings_routes = inspect_file('routes/settings_routes.py')

print("--- STUDENT ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", student_routes))
print(re.findall(r"request\.files\.get\('([^']+)'\)", student_routes))

print("\n--- TEACHER ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", teacher_routes))
print(re.findall(r"request\.files\.get\('([^']+)'\)", teacher_routes))

print("\n--- ACADEMIC ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", academic_routes))

print("\n--- TIMETABLE ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", timetable_routes))

print("\n--- HOMEWORK ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", homework_routes))

print("\n--- EXAM ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", exam_routes))

print("\n--- GRADE ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", grade_routes))

print("\n--- ATTENDANCE ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", attendance_routes))

print("\n--- MESSAGES ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", messages_routes))

print("\n--- USER ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", user_routes))

print("\n--- SETTINGS ROUTES SAVED FIELDS ---")
print(re.findall(r"request\.form\.get\('([^']+)'\)", settings_routes))
