import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'super_secret_key_school_management_system_2026_secure'
    # تم تغيير قاعدة البيانات إلى MySQL
    # يرجى تثبيت pymysql باستخدام الأمر: pip install pymysql
    # وتعديل بيانات الاتصال (المستخدم، كلمة المرور، واسم قاعدة البيانات) بما يتناسب مع خادمك
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'mysql+pymysql://root:@127.0.0.1/school_system_db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(BASE_DIR, 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
