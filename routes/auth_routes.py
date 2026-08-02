from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_user, logout_user, login_required, current_user
from flask_jwt_extended import create_access_token
from models import db, User
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

MAX_FAILED_ATTEMPTS = 5
LOCKOUT_MINUTES = 15

# ==========================================
# 1. Web UI Routes (Using Flask-Login)
# ==========================================

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))
        
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")
        
        user = User.query.filter_by(username=username).first()
        
        if not user:
            flash("اسم المستخدم غير صحيح.", "danger")
            return render_template("login.html")
            
        if user.is_locked():
            flash(f"الحساب مقفل مؤقتاً لمدة {LOCKOUT_MINUTES} دقيقة بسبب كثرة المحاولات الخاطئة. يرجى المحاولة لاحقاً.", "danger")
            return render_template("login.html")
            
        if user.check_password(password):
            # Success
            user.failed_login_attempts = 0
            user.locked_until = None
            user.last_login = datetime.utcnow()
            db.session.commit()
            
            # Login user session
            login_user(user)
            
            # Keep legacy session variables just in case old templates use them
            session['user_id'] = user.id
            session['user_name'] = user.name
            session['user_role'] = user.role
            
            # Create a JWT token for the browser session to access the APIs
            access_token = create_access_token(identity=str(user.id))
            session['jwt_token'] = access_token
            
            
            return redirect(url_for('dashboard.index'))
        else:
            # Failed attempt
            user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
            if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
                user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
                flash(f"تم قفل الحساب مؤقتاً لمدة {LOCKOUT_MINUTES} دقيقة لتجاوز الحد الأقصى ({MAX_FAILED_ATTEMPTS}) للمحاولات.", "danger")
            else:
                remaining = MAX_FAILED_ATTEMPTS - user.failed_login_attempts
                flash(f"كلمة المرور غير صحيحة. يتبقى لك {remaining} محاولات قبل قفل الحساب.", "warning")
            db.session.commit()
            
    return render_template("login.html")

@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    session.clear() # Clear legacy session
    flash("تم تسجيل الخروج بنجاح", "success")
    return redirect(url_for('auth.login'))

@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name")
        email = request.form.get("email")
        password = request.form.get("password")
        
        if name:
            current_user.name = name
            session['user_name'] = name
        if email:
            current_user.username = email
        if password:
            current_user.set_password(password)
            
        db.session.commit()
        flash("تم تحديث بيانات الملف الشخصي بنجاح", "success")
        return redirect(url_for("auth.profile"))
        
    return render_template("profile.html")

# ==========================================
# 2. API Routes (Using Flask-JWT-Extended)
# ==========================================

@auth_bp.route("/api/v1/auth/login", methods=["POST"])
def api_login():
    """
    مسار تسجيل الدخول الخاص بـ API لإرجاع JWT Token
    """
    if not request.is_json:
        return jsonify({"success": False, "message": "يجب إرسال البيانات بصيغة JSON"}), 400
        
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")
    
    if not username or not password:
        return jsonify({"success": False, "message": "اسم المستخدم وكلمة المرور مطلوبان"}), 400
        
    user = User.query.filter_by(username=username).first()
    
    if not user:
        return jsonify({"success": False, "message": "اسم المستخدم غير صحيح"}), 401
        
    if user.is_locked():
        return jsonify({"success": False, "message": "الحساب مقفل مؤقتاً بسبب كثرة المحاولات."}), 403
        
    if user.check_password(password):
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        access_token = create_access_token(identity=str(user.id))
        return jsonify({
            "success": True, 
            "message": "تم تسجيل الدخول بنجاح", 
            "data": {
                "token": access_token,
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "name": user.name,
                    "role": user.role
                }
            }
        }), 200
    else:
        user.failed_login_attempts = (user.failed_login_attempts or 0) + 1
        if user.failed_login_attempts >= MAX_FAILED_ATTEMPTS:
            user.locked_until = datetime.utcnow() + timedelta(minutes=LOCKOUT_MINUTES)
            db.session.commit()
            return jsonify({"success": False, "message": "تم قفل الحساب مؤقتاً بسبب كثرة المحاولات"}), 403
        else:
            db.session.commit()
            return jsonify({"success": False, "message": "كلمة المرور غير صحيحة"}), 401


@auth_bp.route("/users")
@login_required
def users_list():
    if getattr(current_user, 'role', '') != 'admin':
        flash('عذراً، هذه الصفحة مخصصة لمدراء النظام فقط', 'danger')
        return redirect(url_for('dashboard.index'))
    users = User.query.filter_by(is_deleted=False).order_by(User.id.asc()).all()
    return render_template("users/manage.html", users=users)
