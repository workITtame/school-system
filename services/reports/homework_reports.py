"""
==========================================================================
HOMEWORK REPORTS SERVICE (services/reports/homework_reports.py)
==========================================================================
Calculates homework metrics directly from DB models.
"""

from models import Homework

def get_homework_reports_metrics():
    total_homework = Homework.query.count()
    return {
        "total_homework": total_homework
    }
