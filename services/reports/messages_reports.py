"""
==========================================================================
MESSAGES REPORTS SERVICE (services/reports/messages_reports.py)
==========================================================================
Calculates messages metrics directly from DB models.
"""

from models import Message

def get_messages_reports_metrics():
    total_messages = Message.query.count()
    unread_messages = Message.query.filter_by(is_read=False).count()
    return {
        "total_messages": total_messages,
        "unread_messages": unread_messages
    }
