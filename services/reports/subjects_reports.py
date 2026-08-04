"""
==========================================================================
SUBJECTS REPORTS SERVICE (services/reports/subjects_reports.py)
==========================================================================
Calculates subject metrics directly from DB models.
"""

from models import Subject

def get_subjects_reports_metrics():
    total_subjects = Subject.query.filter_by(is_deleted=False).count()
    return {
        "total_subjects": total_subjects
    }
