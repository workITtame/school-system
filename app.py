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
    from routes.grade_routes import grades_bp, grades_legacy_bp
    from routes.report_routes import reports_bp
    from routes.api_routes import api_bp
    from routes.attendance_routes import attendance_bp
    from routes.message_routes import messages_bp
    from routes.homework_routes import homework_bp
    from routes.notification_routes import notifications_bp
    from routes.grading_routes import grading_bp
    from routes.gradebook_routes import gradebook_bp
    from routes.admin_teacher_communication_routes import admin_teacher_bp
    from routes.profile_routes import profile_bp

    @jwt.unauthorized_loader
    def unauthorized_callback(callback):
        return jsonify({"success": False, "message": "Missing Authorization Header"}), 401

    @jwt.invalid_token_loader
    def invalid_token_callback(callback):
        return jsonify({"success": False, "message": "Invalid Token"}), 401

    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        from flask_login import current_user
        if (hasattr(current_user, 'is_authenticated') and current_user.is_authenticated) or 'user_id' in session:
            # Refresh token for valid web session
            user_id = str(current_user.id) if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else str(session.get('user_id', '1'))
            session['jwt_token'] = create_access_token(identity=user_id)
        return jsonify({"success": False, "message": "Token has expired"}), 401

    from flask_jwt_extended import create_access_token
    from flask_login import current_user
    
    from flask import request
    @app.before_request
    def ensure_jwt_token():
        if request.endpoint == 'static':
            return
        if (hasattr(current_user, 'is_authenticated') and current_user.is_authenticated) or 'user_id' in session:
            user_id = str(current_user.id) if hasattr(current_user, 'is_authenticated') and current_user.is_authenticated else str(session.get('user_id', '1'))
            session['jwt_token'] = create_access_token(identity=user_id)

    @app.context_processor
    def inject_school_info():
        try:
            from models.school import School
            school = db.session.query(School).first()
            if school and school.SchoolName:
                return {'school_info': school, 'current_school_name': school.SchoolName}
        except Exception:
            pass
        return {'school_info': None, 'current_school_name': 'مدرسة المستقبل'}

    app.register_blueprint(auth_bp)
    app.register_blueprint(students_bp)
    app.register_blueprint(academic_bp)
    app.register_blueprint(teacher_bp)
    app.register_blueprint(timetable_bp)
    app.register_blueprint(grades_bp)
    app.register_blueprint(grades_legacy_bp)
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
    app.register_blueprint(admin_teacher_bp)
    app.register_blueprint(profile_bp)
    
    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(500)
    def server_error(e):
        import traceback
        err_tb = traceback.format_exc()
        print("=== CRITICAL 500 SERVER ERROR ===", flush=True)
        print(err_tb, flush=True)
        print("=================================", flush=True)
        if os.path.exists(os.path.join(app.template_folder, '500.html')):
            return render_template('500.html'), 500
        return f"<div style='direction:rtl; font-family:sans-serif; padding:20px;'><h2>حدث خطأ في الخادم (500)</h2><pre>{err_tb}</pre></div>", 500

    @app.route('/')
    def index():
        return redirect(url_for('auth.login'))

    try:
        init_db_if_not_exists(app)
    except Exception as e:
        print(f"Auto DB init status: {e}")

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
            
            # Run automatic schema migration to ensure all missing columns exist
            try:
                from migrate_db import run_migrations
                run_migrations()
            except Exception as mig_err:
                print(f"Auto migration status: {mig_err}")
            
            # Ensure default admin exists
            admin = User.query.filter_by(username='admin').first()
            if not admin:
                admin = User(username='admin', name='مدير النظام', role='admin')
                admin.set_password('123456')
                db.session.add(admin)
                db.session.commit()
                print("Default admin user created (username: admin / pass: 123456).")
                
            cleanup_attendance_duplicates()
    except Exception as e:
        print(f"Error checking/creating database: {e}")

def cleanup_attendance_duplicates():
    """Remove duplicate attendance records for the same student on the same date."""
    try:
        from models.student import Attendance
        from sqlalchemy import func
        dups = db.session.query(
            Attendance.SID, Attendance.Date, func.count(Attendance.AttendanceID)
        ).group_by(Attendance.SID, Attendance.Date).having(func.count(Attendance.AttendanceID) > 1).all()

        if dups:
            for sid, date_val, count in dups:
                records = Attendance.query.filter_by(SID=sid, Date=date_val).order_by(
                    Attendance.updated_at.desc(), Attendance.created_at.desc(), Attendance.AttendanceID.desc()
                ).all()
                if len(records) > 1:
                    for dup in records[1:]:
                        db.session.delete(dup)
            db.session.commit()
            print("Verified and cleaned up duplicate attendance records.")
    except Exception as e:
        db.session.rollback()
        print(f"Error during attendance cleanup: {e}")

if __name__ == "__main__":
    app = create_app()
    init_db_if_not_exists(app)
    app.run(debug=True)
