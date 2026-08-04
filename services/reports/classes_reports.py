"""
==========================================================================
CLASSES REPORTS SERVICE (services/reports/classes_reports.py)
==========================================================================
Calculates class and section metrics directly from DB models.
"""

from models import Classes, Sections

def get_classes_reports_metrics():
    total_classes = Classes.query.filter_by(is_deleted=False).count()
    total_sections = Sections.query.filter_by(is_deleted=False).count()
    return {
        "total_classes": total_classes,
        "total_sections": total_sections
    }
