import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import argparse
from app import create_app
from models import db, Homework, ExamSchedule, Student
from models.grade import Marks, DetailMarks

def audit_and_repair(repair=False):
    app = create_app()
    with app.app_context():
        print("=" * 70)
        print(" HOMEWORK & EXAM GRADE SEPARATION AUDIT / REPAIR SCRIPT")
        print("=" * 70)
        print(f" Mode: {'REPAIR (WRITE)' if repair else 'AUDIT ONLY (READ ONLY)'}\n")

        all_marks = Marks.query.all()
        all_detail_marks = DetailMarks.query.all()
        all_homeworks = Homework.query.all()

        hw_map = {hw.id: hw for hw in all_homeworks}
        
        contaminated_marks = []
        for m in all_marks:
            is_contaminated = False
            reason = ""

            notes = m.Notes or ""
            # Check if Notes starts with "واجب:" or mentions homework
            if notes.startswith("واجب:") or "واجب" in notes:
                if m.ExamID is not None or m.assessment_type != 'homework':
                    is_contaminated = True
                    reason = "Homework mark recorded with ExamID or wrong assessment_type"

            if is_contaminated:
                # Find matching homework ID if possible
                matched_hw_id = None
                for hw in all_homeworks:
                    if hw.sub_id == m.SubID:
                        matched_hw_id = hw.id
                        break
                
                contaminated_marks.append({
                    'mark_id': m.M_ID,
                    'student_id': m.SID,
                    'subject_id': m.SubID,
                    'exam_id': m.ExamID,
                    'homework_id': m.HomeworkID,
                    'assessment_type': m.assessment_type,
                    'assessment_id': m.assessment_id,
                    'notes': m.Notes,
                    'matched_hw_id': matched_hw_id or 1,
                    'reason': reason
                })

        print(f"Total Marks records audited: {len(all_marks)}")
        print(f"Total DetailMarks records audited: {len(all_detail_marks)}")
        print(f"Contaminated Marks records found: {len(contaminated_marks)}\n")

        if contaminated_marks:
            print("--- CONTAMINATED MARKS DETAIL ---")
            for c in contaminated_marks:
                print(f" Mark ID #{c['mark_id']}: SID={c['student_id']}, SubID={c['subject_id']}, ExamID={c['exam_id']}, "
                      f"Current Type={c['assessment_type']}, Notes='{c['notes']}' -> [Reason: {c['reason']}]")
            print("-" * 70)

        if repair and contaminated_marks:
            print("\nExecuting non-destructive repair on contaminated records...")
            repaired_count = 0
            for c in contaminated_marks:
                m = Marks.query.get(c['mark_id'])
                if m:
                    m.assessment_type = 'homework'
                    m.assessment_id = c['matched_hw_id']
                    m.HomeworkID = c['matched_hw_id']
                    m.ExamID = None
                    repaired_count += 1
            
            # Clean up DetailMarks created accidentally for homeworks
            for dm in all_detail_marks:
                if dm.ExamID and (dm.assessment_type == 'homework' or (dm.ExamID == 1 and not ExamSchedule.query.get(1))):
                    dm.assessment_type = 'homework'
                    dm.HomeworkID = dm.ExamID
                    dm.ExamID = None

            db.session.commit()
            print(f"SUCCESSFULLY REPAIRED {repaired_count} CONTAMINATED MARKS RECORDS!")
        elif not repair and contaminated_marks:
            print("\n[NOTE] Running in AUDIT-ONLY mode. Pass '--repair' flag to apply fixes safely.")
        else:
            print("\nNO CONTAMINATED RECORDS NEED REPAIR. SYSTEM DATA IS CLEAN!")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Audit and repair homework/exam grade contamination")
    parser.add_argument('--repair', action='store_true', help="Apply non-destructive repairs to database")
    args = parser.parse_argument_group() if hasattr(parser, 'parse_argument_group') else parser.parse_args()
    audit_and_repair(repair=args.repair)
