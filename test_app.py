from app import create_app

try:
    app = create_app()
    print("App created successfully!")
except Exception as e:
    print("App creation failed:", e)
