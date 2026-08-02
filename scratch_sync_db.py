import os
import sys

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db

app = create_app()

def sync_db():
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        print("Done!")

if __name__ == "__main__":
    sync_db()
