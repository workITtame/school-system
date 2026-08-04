"""
==========================================================================
EXAM REPORTS SERVICE (services/reports/exam_reports.py)
==========================================================================
Calculates exam schedule metrics directly from DB models.
"""

from models import TypeExams

def get_exam_reports_metrics():
    total_exams = TypeExams.query.count()
    return {
        "total_exams": total_exams
    }
