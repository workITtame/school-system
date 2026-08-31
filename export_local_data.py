import os
import json
from datetime import datetime, date
from decimal import Decimal

def model_to_dict(obj):
    if not obj:
        return None
    d = {}
    for column in obj.__table__.columns:
        val = getattr(obj, column.name)
        if isinstance(val, (datetime, date)):
            val = val.isoformat()
        elif isinstance(val, Decimal):
            val = float(val)
        d[column.name] = val
    return d

def export_local_data():
    from app import create_app, db
    from models import (
        User, Student, Teacher, Classes, Sections, 
        Subject, Lessons, Terms, ExamSchedule, Marks, 
        Attendance, Homework, Message, Notification, School
    )

    app = create_app()
    with app.app_context():
        data = {
            'schools': [model_to_dict(s) for s in School.query.all()],
            'users': [model_to_dict(u) for u in User.query.all()],
            'classes': [model_to_dict(c) for c in Classes.query.all()],
            'sections': [model_to_dict(sec) for sec in Sections.query.all()],
            'teachers': [model_to_dict(t) for t in Teacher.query.all()],
            'students': [model_to_dict(st) for st in Student.query.all()],
            'subjects': [model_to_dict(sub) for sub in Subject.query.all()],
            'homeworks': [model_to_dict(h) for h in Homework.query.all()],
            'terms': [model_to_dict(tm) for tm in Terms.query.all()],
            'lessons': [model_to_dict(ls) for ls in Lessons.query.all()]
        }

        out_path = os.path.join(app.root_path, 'seed_data.json')
        with open(out_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        print(f"Successfully exported local database to {out_path}")
        return out_path

if __name__ == '__main__':
    export_local_data()
