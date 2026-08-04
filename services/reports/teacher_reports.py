"""
==========================================================================
TEACHER REPORTS SERVICE (services/reports/teacher_reports.py)
==========================================================================
Calculates teacher metrics directly from DB models.
"""

from models import Teacher

def get_teacher_reports_metrics():
    total_teachers = Teacher.query.filter_by(is_deleted=False).count()
    return {
        "total_teachers": total_teachers
    }
