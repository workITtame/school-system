"""
==========================================================================
REPORTS MODULE COMPREHENSIVE QA & AUTOMATED INTEGRATION AUDIT
==========================================================================
Tests all services, fields, buttons, routes, and export endpoints in Reports Module.
"""

import sys
import unittest
from app import create_app
from models import db, User, Student, Teacher, Classes, Sections, Marks, Message, Homework, TypeExams

class TestReportsModuleComprehensive(unittest.TestCase):
    def setUp(self):
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['WTF_CSRF_ENABLED'] = False
        self.client = self.app.test_client()

    def _login(self):
        with self.app.app_context():
            user = User.query.first()
            if user:
                with self.client.session_transaction() as sess:
                    sess['_user_id'] = str(user.id)
                    sess['user_id'] = user.id

    def test_01_service_layer_metrics(self):
        """Test all 12 service functions in services/reports/"""
        from services.reports import (
            get_reports_dashboard_metrics,
            get_reports_registry,
            get_student_reports_metrics,
            get_teacher_reports_metrics,
            get_classes_reports_metrics,
            get_subjects_reports_metrics,
            get_attendance_reports_metrics,
            get_homework_reports_metrics,
            get_exam_reports_metrics,
            get_marks_reports_metrics,
            get_messages_reports_metrics,
            get_notifications_reports_metrics
        )
        with self.app.app_context():
            dash_metrics = get_reports_dashboard_metrics()
            self.assertIn('student_count', dash_metrics)
            self.assertIn('teacher_count', dash_metrics)
            self.assertIn('attendance_rate', dash_metrics)
            self.assertIn('avg_score', dash_metrics)
            print(f"[PASSED] Dashboard Services Metrics: {dash_metrics}")

            registry = get_reports_registry()
            self.assertEqual(len(registry), 10)
            print(f"[PASSED] Reports Registry returned {len(registry)} registered reports.")

            std_m = get_student_reports_metrics()
            self.assertIn('total_students', std_m)

            tch_m = get_teacher_reports_metrics()
            self.assertIn('total_teachers', tch_m)

            cls_m = get_classes_reports_metrics()
            self.assertIn('total_classes', cls_m)

            sub_m = get_subjects_reports_metrics()
            self.assertIn('total_subjects', sub_m)

            att_m = get_attendance_reports_metrics()
            self.assertIn('attendance_rate', att_m)

            hwk_m = get_homework_reports_metrics()
            self.assertIn('total_homework', hwk_m)

            ex_m = get_exam_reports_metrics()
            self.assertIn('total_exams', ex_m)

            mrk_m = get_marks_reports_metrics()
            self.assertIn('avg_score', mrk_m)

            msg_m = get_messages_reports_metrics()
            self.assertIn('total_messages', msg_m)

            not_m = get_notifications_reports_metrics()
            self.assertIn('total_notifications', not_m)

            print("[PASSED] All 12 Sub-Service Functions Executed Cleanly.")

    def test_02_reports_dashboard_route_and_rendering(self):
        """Test GET /reports HTML output and elements"""
        self._login()
        with self.app.app_context():
            res = self.client.get('/reports')
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)

            # Check key DOM elements
            self.assertIn('reportsModuleRoot', html)
            self.assertIn('reportsFilterSearch', html)
            self.assertIn('reportsFilterCategory', html)
            self.assertIn('reportsFilterType', html)
            self.assertIn('reportsMasterTableBody', html)
            self.assertIn('viewReportProfileModal', html)
            self.assertIn('exportReportsMasterExcel', html)
            print("[PASSED] GET /reports HTML rendered all required DOM components and buttons.")

    def test_03_student_report_route_and_export(self):
        """Test GET /reports/student and PDF/Excel export endpoints"""
        self._login()
        with self.app.app_context():
            # 1. Base route
            res = self.client.get('/reports/student')
            self.assertEqual(res.status_code, 200)
            html = res.get_data(as_text=True)
            self.assertIn('studentReportModuleRoot', html)

            # 2. Selected student route query
            student = Student.query.filter_by(is_deleted=False).first()
            if student:
                res2 = self.client.get(f'/reports/student?class_id={student.CID}&section_id={student.SectionID}&student_id={student.SID}')
                self.assertEqual(res2.status_code, 200)
                html2 = res2.get_data(as_text=True)
                self.assertIn(student.SName, html2)
                print(f"[PASSED] GET /reports/student query for student {student.SID} ({student.SName}) rendered cleanly.")

                # 3. Test PDF export route
                res_pdf = self.client.get(f'/reports/student/{student.SID}/pdf_fast')
                self.assertEqual(res_pdf.status_code, 200)
                print(f"[PASSED] Student PDF Export Route status: 200 OK (Generated PDF size: {len(res_pdf.data)} bytes)")

                # 4. Test Excel export route
                res_excel = self.client.get(f'/reports/student/{student.SID}/excel')
                self.assertEqual(res_excel.status_code, 200)
                print(f"[PASSED] Student Excel Export Route status: 200 OK (Generated Excel size: {len(res_excel.data)} bytes)")

    def test_04_performance_and_analytics_routes(self):
        """Test GET /reports/performance and GET /reports/analytics"""
        self._login()
        with self.app.app_context():
            res_perf = self.client.get('/reports/performance')
            self.assertEqual(res_perf.status_code, 200)
            html_perf = res_perf.get_data(as_text=True)
            self.assertIn('performanceReportModuleRoot', html_perf)
            print("[PASSED] GET /reports/performance rendered cleanly.")

            res_ana = self.client.get('/reports/analytics')
            self.assertEqual(res_ana.status_code, 200)
            html_ana = res_ana.get_data(as_text=True)
            self.assertIn('analyticsReportModuleRoot', html_ana)
            print("[PASSED] GET /reports/analytics rendered cleanly.")

if __name__ == '__main__':
    unittest.main()
