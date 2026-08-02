import requests

session = requests.Session()

# 1. Web Login
login_url = "http://127.0.0.1:5000/login"
res1 = session.post(login_url, data={'username': 'admin', 'password': '123456'})
print("Login status:", res1.status_code)

# 2. Get Teacher Page
teacher_url = "http://127.0.0.1:5000/teacher/"
res2 = session.get(teacher_url)
print("Teacher page status:", res2.status_code)

if res2.status_code == 200:
    token_str = 'name="jwt-token" content="'
    idx = res2.text.find(token_str)
    if idx != -1:
        start_idx = idx + len(token_str)
        end_idx = res2.text.find('"', start_idx)
        jwt_token = res2.text[start_idx:end_idx]
        print("Extracted JWT Token:", jwt_token[:20] + "..." if jwt_token else "EMPTY")
        
        # 3. Call API
        api_url = "http://127.0.0.1:5000/api/v1/teachers?page=1&limit=10&search="
        headers = {'Authorization': f'Bearer {jwt_token}', 'Content-Type': 'application/json'}
        res3 = session.get(api_url, headers=headers)
        print("API status:", res3.status_code)
        print("API response:", res3.text)
    else:
        print("No jwt-token meta tag found!")
