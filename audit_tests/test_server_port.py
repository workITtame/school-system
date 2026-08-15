import urllib.request

try:
    res = urllib.request.urlopen('http://127.0.0.1:5000/login')
    print(f"Flask Server Status: {res.status}")
except Exception as e:
    print(f"Flask Server Connection Result: {e}")
