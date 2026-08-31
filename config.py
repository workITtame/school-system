import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_database_uri():
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL')
    
    if not db_url:
        # Check individual Railway / MySQL environment variables
        user = os.environ.get('MYSQLUSER') or 'root'
        password = os.environ.get('MYSQLPASSWORD') or ''
        host = os.environ.get('MYSQLHOST') or '127.0.0.1'
        port = os.environ.get('MYSQLPORT') or '3306'
        database = os.environ.get('MYSQLDATABASE') or 'school_system_db'
        
        db_url = f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"
    else:
        # Fix scheme if mysql:// is provided instead of mysql+pymysql://
        if db_url.startswith('mysql://'):
            db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
        if 'charset=utf8mb4' not in db_url:
            separator = '&' if '?' in db_url else '?'
            db_url += f"{separator}charset=utf8mb4"
            
    return db_url

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key_school_management_system_2026_secure'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super_secret_jwt_key_school_management_system_2026'
    SQLALCHEMY_DATABASE_URI = get_database_uri()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

