from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import db, SchoolTable, Classes, Sections, Subject, Teacher, Days, Lessons, Terms

timetable_bp = Blueprint('timetable', __name__, url_prefix='/timetable')

@timetable_bp.route('/')
def index():
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))

    return render_template('timetable/index.html')
