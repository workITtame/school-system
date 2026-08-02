from app import create_app
import json

app = create_app()
client = app.test_client()

print("--- Testing Students API ---")

# Login to get JWT Token
login_res = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': '123456'})
token = login_res.json['data']['token']
headers = {'Authorization': f'Bearer {token}', 'Content-Type': 'application/json'}

# 1. Add Student (POST)
print("\n1. POST /api/v1/students")
add_res = client.post('/api/v1/students', data=json.dumps({'SName': 'API Test Student', 'Gender': 'Female'}), headers=headers)
print(f"Status: {add_res.status_code}")
new_student = add_res.get_json()['data']
print(new_student)
student_id = new_student['SID']

# 2. Get All Students (GET)
print("\n2. GET /api/v1/students")
get_all = client.get('/api/v1/students', headers=headers)
print(f"Status: {get_all.status_code}")
print(f"Total students: {get_all.get_json()['meta']['total']}")

# 3. Get Single Student (GET)
print(f"\n3. GET /api/v1/students/{student_id}")
get_one = client.get(f'/api/v1/students/{student_id}', headers=headers)
print(f"Status: {get_one.status_code}")
print(get_one.get_json()['data']['SName'])

# 4. Update Student (PUT)
print(f"\n4. PUT /api/v1/students/{student_id}")
update_res = client.put(f'/api/v1/students/{student_id}', data=json.dumps({'SName': 'API Test Student Updated'}), headers=headers)
print(f"Status: {update_res.status_code}")
print(update_res.get_json()['data']['SName'])

# 5. Delete Student (DELETE)
print(f"\n5. DELETE /api/v1/students/{student_id}")
delete_res = client.delete(f'/api/v1/students/{student_id}', headers=headers)
print(f"Status: {delete_res.status_code}")
print(delete_res.get_json()['message'])

# 6. Verify Deletion (GET)
print(f"\n6. Verify DELETE /api/v1/students/{student_id}")
get_deleted = client.get(f'/api/v1/students/{student_id}', headers=headers)
print(f"Status: {get_deleted.status_code}")
print(get_deleted.get_json()['message'])
