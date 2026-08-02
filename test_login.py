from app import create_app
app = create_app()
client = app.test_client()
r1 = client.post('/login', data={'username':'admin', 'password':'123456'})
print('Login status:', r1.status_code, r1.location)
with client.session_transaction() as sess:
    print('Session:', dict(sess))
r2 = client.post('/students/add', data={'name': 'User UI Test', 'gender': 'Male', 'class_id': '', 'section_id': '', 'neighborhood': ''}, follow_redirects=False)
print('Add status:', r2.status_code, r2.location)
