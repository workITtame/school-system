from app import create_app
import json

app = create_app()
app.config['TESTING'] = True

with app.test_client() as client:
    res = client.post('/api/v1/auth/login', json={'username': 'admin', 'password': '123456'})
    if res.status_code == 200:
        token = res.json['data']['token']
        headers = {'Authorization': f'Bearer {token}'}
        res2 = client.get('/api/v1/students?page=1&limit=10', headers=headers)
        print("Students API Status:", res2.status_code)
        print("Students API Response:", res2.get_data(as_text=True))
    else:
        print("Login failed:", res.get_data(as_text=True))
