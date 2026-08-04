"""
==========================================================================
STUDENT REPORTS SERVICE (services/reports/student_reports.py)
==========================================================================
Calculates student reports metrics directly from DB models.
"""

from models import Student, Classes, Sections

def get_student_reports_metrics():
    total_students = Student.query.filter_by(is_deleted=False).count()
    total_classes = Classes.query.filter_by(is_deleted=False).count()
    total_sections = Sections.query.filter_by(is_deleted=False).count()
    return {
        "total_students": total_students,
        "total_classes": total_classes,
        "total_sections": total_sections
    }
