import os
from flask import Flask, redirect, url_for, jsonify, session, render_template
from config import Config
from models import db, User
from models.extensions import cache, ma, bcrypt, login_manager, jwt
from flask_cors import CORS

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    CORS(app) # Allow cross-origin requests for the professional API
    db.init_app(app)
    
    app.config['CACHE_TYPE'] = 'SimpleCache'
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300
    cache.init_app(app)
    ma.init_app(app) # Initialize Marshmallow
    bcrypt.init_app(app)
    jwt.init_app(app)
    
    from utils.template_filters import register_template_filters
    register_template_filters(app)

    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'الرجاء تسجيل الدخول للوصول إلى هذه الصفحة'
    login_manager.login_message_category = 'warning'

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints (will create these next)
    from routes.auth_routes import auth_bp
    from routes.dashboard_routes import dashboard_bp
    from routes.student_routes import students_bp
    from routes.teacher_routes import teacher_bp
    from routes.academic_routes import academic_bp
    from routes.timetable_routes import timetable_bp
    from routes.exam_routes import exams_bp
    from routes.grade_routes import grades_bp
    from routes.report_routes import reports_bp
    from routes.api_routes import api_bp
    from routes.attendance_routes import attendance_bp
    from routes.message_routes import messages_bp
    from routes.homework_routes import homework_bp
    from routes.notification_routes import notifications_bp
    from routes.grading_routes import grading_bp
    from routes.gradebook_routes import gradebook_bp

    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({"success": False, "message": "Missing Authorization Header"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({"success": False, "message": "Invalid Token"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({"success": False, "message": "Token has expired"}), 401

    from flask_jwt_extended import create_access_token
    from flask_login import current_user
    
    @app.before_request
    def ensure_jwt_token():
        if current_user.is_authenticated:
            session['jwt_token'] = create_access_token(identity=str(current_user.id))

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(academic_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(grades_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)
    app.register_blueprint(exams_bp)
    app.register_blueprint(attendance_bp)
    app.register_blueprint(messages_bp)
    app.register_blueprint(homework_bp)
    app.register_blueprint(notifications_bp)
    app.register_blueprint(grading_bp)
    app.register_blueprint(gradebook_bp)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    # Database initialization and seeding should be done via a separate script like reset_admin.py

    return app

def init_db_if_not_exists(app):
    """Check if the database exists and create it if it doesn't."""
    import pymysql
    from urllib.parse import urlparse
    
    # Parse the DATABASE_URI to get host, user, password, and db name
    db_uri = app.config['SQLALCHEMY_DATABASE_URI']
    if not db_uri.startswith('mysql'):
        return # Only do this for MySQL
        
    parsed_uri = urlparse(db_uri)
    db_name = parsed_uri.path.lstrip('/')
    
    # Connect without database to create it
    try:
        connection = pymysql.connect(
            host=parsed_uri.hostname or 'localhost',
            user=parsed_uri.username or 'root',
            password=parsed_uri.password or '',
            port=parsed_uri.port or 3306
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        connection.commit()
        connection.close()
        print(f"Verified/Created database: {db_name}")
        
        # Now create tables using SQLAlchemy
        with app.app_context():
            db.create_all()
            print("Verified/Created database tables.")
    except Exception as e:
        print(f"Error checking/creating database: {e}")

if __name__ == "__main__":
    app = create_app()
    init_db_if_not_exists(app)
    app.run(debug=True)
