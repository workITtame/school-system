import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

def get_database_uri():
    # 1. Check direct URL environment variables
    db_url = os.environ.get('DATABASE_URL') or os.environ.get('MYSQL_URL') or os.environ.get('MYSQL_PRIVATE_URL')
    
    if db_url:
        if db_url.startswith('mysql://'):
            db_url = db_url.replace('mysql://', 'mysql+pymysql://', 1)
        if 'charset=utf8mb4' not in db_url:
            separator = '&' if '?' in db_url else '?'
            db_url += f"{separator}charset=utf8mb4"
        return db_url

    # 2. Check individual MySQL variables
    host = os.environ.get('MYSQLHOST') or os.environ.get('MYSQLPRIVATEHOST')
    user = os.environ.get('MYSQLUSER')
    password = os.environ.get('MYSQLPASSWORD') or ''
    port = os.environ.get('MYSQLPORT') or '3306'
    database = os.environ.get('MYSQLDATABASE') or 'railway'

    if host and user and host not in ['127.0.0.1', 'localhost']:
        return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"

    # 3. If running in a cloud environment (like Railway) without MySQL env vars set:
    if os.environ.get('RAILWAY_ENVIRONMENT') or os.environ.get('PORT') or os.environ.get('RAILWAY_STATIC_URL'):
        db_dir = os.path.abspath(os.path.join(BASE_DIR, 'instance'))
        os.makedirs(db_dir, exist_ok=True)
        db_file = os.path.abspath(os.path.join(db_dir, 'school_system.db'))
        return f"sqlite:///{db_file}"

    # 4. Local development default (local MySQL)
    user = os.environ.get('MYSQLUSER') or 'root'
    password = os.environ.get('MYSQLPASSWORD') or ''
    host = '127.0.0.1'
    port = '3306'
    database = os.environ.get('MYSQLDATABASE') or 'school_system_db'
    return f"mysql+pymysql://{user}:{password}@{host}:{port}/{database}?charset=utf8mb4"

db_uri = get_database_uri()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key_school_management_system_2026_secure'
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'super_secret_jwt_key_school_management_system_2026'
    SQLALCHEMY_DATABASE_URI = db_uri
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    if db_uri.startswith('mysql'):
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'max_overflow': 20,
            'pool_recycle': 280,
            'pool_pre_ping': True
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_pre_ping': True
        }

    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

