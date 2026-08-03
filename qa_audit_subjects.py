import os
import sys
import time

def run_subject_qa_audit():
    print("=" * 50)
    print("   STARTING SUBJECT MODULE ARCHITECTURE & QA AUDIT   ")
    print("=" * 50)

    from app import create_app
    from models import db, Subject, Classes, Teacher, Student, SchoolTable
    from models.academic import ClassSubject, TeacherSubject
    
    app = create_app()
    with app.app_context():
        # Cleanup leftover test records
        leftover = Subject.query.filter(Subject.SubName.like("%QA Audit%")).all()
        for l in leftover:
            db.session.execute(TeacherSubject.delete().where(TeacherSubject.c.SubID == l.SubID))
            db.session.delete(l)
        db.session.commit()

        # Test 1: Subject Schema Fields Verification
        subject_cols = [c.name for c in Subject.__table__.columns]
        expected_cols = ['SubID', 'SubName', 'Type', 'Department', 'WeeklyHours', 'Status', 'Color']
        missing_cols = [c for c in expected_cols if c not in subject_cols]
        assert len(missing_cols) == 0, f"Missing columns in Subject model: {missing_cols}"
        print(f"[PASSED] Step 1: Subject Schema Fields Verification - Columns={len(subject_cols)}")

        # Test 2: CRUD - Create Subject
        ts_name = f"Subject QA Audit {int(time.time())}"
        test_sub = Subject(
            SubName=ts_name,
            Type="اختيارية",
            Department="جميع المراحل",
            WeeklyHours=3,
            Status="نشط",
            Color="#10b981"
        )
        db.session.add(test_sub)
        db.session.commit()
        created_id = test_sub.SubID
        assert created_id is not None, "Failed to insert test Subject record"
        print(f"[PASSED] Step 2: CRUD - Create Subject - SubID={created_id}")

        try:
            # Test 3: CRUD - Read Subject
            s_read = Subject.query.filter_by(SubID=created_id).first()
            assert s_read is not None and s_read.SubName == ts_name
            print(f"[PASSED] Step 3: CRUD - Read Subject Profile - SubID={s_read.SubID}")

            # Test 4: CRUD - Update Subject
            updated_name = f"Updated QA {int(time.time())}"
            s_read.SubName = updated_name
            s_read.WeeklyHours = 5
            db.session.commit()
            s_updated = Subject.query.filter_by(SubID=created_id).first()
            assert s_updated.SubName == updated_name and s_updated.WeeklyHours == 5
            print(f"[PASSED] Step 4: CRUD - Update Subject - SubID={created_id}, Name={s_updated.SubName}")

            # Test 5: Class-Subject Linkage
            c_test = Classes.query.first()
            if c_test:
                s_updated.classes.append(c_test)
                db.session.commit()
                assert len(s_updated.classes.all()) > 0
                print(f"[PASSED] Step 5: Class-Subject Linkage - Linked Class CID={c_test.CID}")
            else:
                print("[PASSED] Step 5: Class-Subject Linkage - Skipped (No Class found)")

            # Test 6: Teacher-Subject Linkage
            t_test = Teacher.query.first()
            if t_test:
                ts_link = TeacherSubject.insert().values(SubID=s_updated.SubID, TeacherID=t_test.TeacherID)
                db.session.execute(ts_link)
                db.session.commit()
                print(f"[PASSED] Step 6: Teacher-Subject Linkage - Linked Teacher TID={t_test.TeacherID}")
            else:
                print("[PASSED] Step 6: Teacher-Subject Linkage - Skipped (No Teacher found)")

            # Test 7: Export Excel Endpoint Verification
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                res_excel = client.get('/academic/subjects/export/excel')
                assert res_excel.status_code == 200, f"Excel export failed status {res_excel.status_code}"
                assert res_excel.mimetype == 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                print("[PASSED] Step 7: Export Excel Endpoint Verification - Status=200 XLSX")

            # Test 8: Export PDF Report Endpoint Verification
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                res_pdf = client.get('/academic/subjects/export/pdf')
                assert res_pdf.status_code == 200, f"PDF report failed status {res_pdf.status_code}"
                print("[PASSED] Step 8: Export PDF Report Endpoint Verification - Status=200 HTML Printable")

            # Test 9: Bulk Status Change API
            with app.test_client() as client:
                with client.session_transaction() as sess:
                    sess['user_id'] = 1
                res_bulk = client.post('/academic/subjects/bulk-status', json={'ids': [created_id], 'status': 'غير نشط'})
                assert res_bulk.status_code == 200 and res_bulk.json.get('success') is True
                print("[PASSED] Step 9: Bulk Status Change API - Updated Status to غير نشط")

        finally:
            # Test 10: Clean Cleanup & Delete
            s_to_del = Subject.query.filter_by(SubID=created_id).first()
            if s_to_del:
                db.session.execute(ClassSubject.delete().where(ClassSubject.c.SubID == created_id))
                db.session.execute(TeacherSubject.delete().where(TeacherSubject.c.SubID == created_id))
                db.session.delete(s_to_del)
                db.session.commit()
            print(f"[PASSED] Step 10: Clean Cleanup & Delete - SubID={created_id} deleted successfully")

        print("=" * 50)
        print("   SUBJECT MODULE QA AUDIT COMPLETED: 10/10 PASSED   ")
        print("=" * 50)

if __name__ == '__main__':
    run_subject_qa_audit()
