"""
==========================================================================
MARKS REPORTS SERVICE (services/reports/marks_reports.py)
==========================================================================
Calculates academic marks and performance average metrics from DB models.
"""

from sqlalchemy import func
from models import db, Marks

def get_marks_reports_metrics():
    total_marks = Marks.query.count()
    avg_score_raw = db.session.query(func.avg(Marks.Score)).scalar()
    avg_score = round(float(avg_score_raw), 1) if avg_score_raw is not None else 0.0
    return {
        "total_marks": total_marks,
        "avg_score": avg_score
    }
