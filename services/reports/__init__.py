"""
==========================================================================
ENTERPRISE REPORTS SERVICES PACKAGE (services/reports/__init__.py)
==========================================================================
Dynamic Single Source of Truth Reports Discovery & Registry Engine
"""

from .dashboard_reports import get_reports_dashboard_metrics
from .student_reports import get_student_reports_metrics
from .teacher_reports import get_teacher_reports_metrics
from .classes_reports import get_classes_reports_metrics
from .subjects_reports import get_subjects_reports_metrics
from .attendance_reports import get_attendance_reports_metrics
from .homework_reports import get_homework_reports_metrics
from .exam_reports import get_exam_reports_metrics
from .marks_reports import get_marks_reports_metrics
from .messages_reports import get_messages_reports_metrics
from .notifications_reports import get_notifications_reports_metrics

# Enterprise Reports Discovery Registry (Dynamic In-Memory Single Source of Truth Mapping)
REPORTS_REGISTRY = [
    {
        "code": "REP-STD-01",
        "name": "كشف درجات الطلاب وإصدار الشهادات",
        "category": "طلاب",
        "route_name": "reports.student_report",
        "route_path": "/reports/student",
        "icon": "fa-solid fa-user-graduate",
        "description": "استخراج كشوفات درجات المواد والامتحانات الفردية والجماعية للطلاب وإصدار بطاقات النتائج والشهادات الرسمية.",
        "tables": ["Student", "Classes", "Sections", "Marks", "TypeExams"],
        "modules": ["الطلاب", "الاختبارات والدرجات", "الصفوف والشعب"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "primary"
    },
    {
        "code": "REP-PRF-02",
        "name": "تحليل الأداء ومتوسطات درجات الصفوف",
        "category": "طلاب",
        "route_name": "reports.performance",
        "route_path": "/reports/performance",
        "icon": "fa-solid fa-chart-line",
        "description": "رسم وتتبع متوسط درجات الاختبارات حسب الصفوف والشعب الدراسية مع التحليل البياني للأداء الأكاديمي.",
        "tables": ["Student", "Classes", "Marks"],
        "modules": ["التقارير الأكاديمية", "الدرجات", "الصفوف"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "success"
    },
    {
        "code": "REP-TCH-03",
        "name": "تقرير نصاب وتوزيع المعلمين",
        "category": "معلمون",
        "route_name": "teacher.index",
        "route_path": "/teachers/",
        "icon": "fa-solid fa-chalkboard-user",
        "description": "بيانات التخصصات والساعات الأكاديمية والمواد المسندة للمعلمين وتوزيع النصاب التدريسي بالجدول.",
        "tables": ["Teacher", "User", "ClassSubject"],
        "modules": ["المعلمون", "المواد الدراسية", "الجدول الأسبوعي"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "success"
    },
    {
        "code": "REP-ATT-04",
        "name": "تقرير الحضور والغياب اليومي",
        "category": "حضور",
        "route_name": "attendance.index",
        "route_path": "/attendance/",
        "icon": "fa-solid fa-clipboard-user",
        "description": "متابعة سجلات الحضور والانضباط اليومي ونسب الحضور الشاملة واستخراج إحصائيات التغيّب.",
        "tables": ["Attendance", "Student", "Classes"],
        "modules": ["الحضور والغياب", "الانضباط المدرسي", "الطلاب"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "danger"
    },
    {
        "code": "REP-CLS-05",
        "name": "كشوفات توزيع الصفوف والشعب الدراسية",
        "category": "صفوف",
        "route_name": "academic.classes",
        "route_path": "/academic/classes",
        "icon": "fa-solid fa-school",
        "description": "قوائم أسماء الطلاب حسب الصفوف الدراسية والشعب المسجلة وتحديد الطاقة الاستيعابية الفعالة.",
        "tables": ["Classes", "Sections", "ClassesSections", "Student"],
        "modules": ["الصفوف والشعب", "الطلاب", "الشؤون الأكاديمية"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "info"
    },
    {
        "code": "REP-SUB-06",
        "name": "تقرير المواد الدراسية والمناهج",
        "category": "صفوف",
        "route_name": "academic.subjects",
        "route_path": "/academic/subjects",
        "icon": "fa-solid fa-book-open",
        "description": "خطة المناهج الدراسية، الساعات الأكاديمية المخصصة، والارتباط بالصفوف والشعب الكلية.",
        "tables": ["Subject", "ClassSubject", "Classes"],
        "modules": ["المواد الدراسية", "الصفوف", "الجدول الدراسي"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "secondary"
    },
    {
        "code": "REP-TTB-07",
        "name": "جدول الحصص والبرنامج الأسبوعي",
        "category": "صفوف",
        "route_name": "timetable.index",
        "route_path": "/timetable/",
        "icon": "fa-solid fa-calendar-days",
        "description": "جدول توزيع المعلمين والحصص الدراسية الأسبوعية لكافة الشعب والصفوف المعتمدة بالنظام.",
        "tables": ["SchoolTable", "Teacher", "Classes", "Sections", "Subject"],
        "modules": ["الجدول الدراسي", "المعلمون", "الصفوف"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "warning"
    },
    {
        "code": "REP-HWK-08",
        "name": "تقرير الواجبات والتسليمات والتكليفات",
        "category": "حضور",
        "route_name": "homework.index",
        "route_path": "/homework/",
        "icon": "fa-solid fa-book-bookmark",
        "description": "متابعة إسناد الواجبات المدرسية والتكليفات الأكاديمية ونسب التسليم والتقييم.",
        "tables": ["Homework", "Teacher", "Subject", "Classes"],
        "modules": ["الواجبات المنزلية", "المعلمون", "الطلاب"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "primary"
    },
    {
        "code": "REP-MSG-09",
        "name": "سجل الرسائل والمحادثات الأكاديمية",
        "category": "إدارة",
        "route_name": "messages.index",
        "route_path": "/messages/",
        "icon": "fa-solid fa-comments",
        "description": "سجلات المراسلات والتواصل الأكاديمي المباشر والجماعي بين الإدارة والمعلمين وأولياء الأمور.",
        "tables": ["Message", "User"],
        "modules": ["الرسائل والمحادثات", "الإشعارات", "المستخدمون"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "info"
    },
    {
        "code": "REP-FIN-10",
        "name": "تقرير الشؤون المالية والإيرادات",
        "category": "إدارة",
        "route_name": "dashboard.finance",
        "route_path": "/dashboard/finance",
        "icon": "fa-solid fa-file-invoice-dollar",
        "description": "ملخص المقبوضات والمصروفات الإدارية والمتحصلات المالية وسجلات الرسوم الأكاديمية.",
        "tables": ["Student", "Classes", "User"],
        "modules": ["الشؤون المالية", "إدارة النظام", "الطلاب"],
        "export_pdf": True,
        "export_excel": True,
        "printable": True,
        "status": "متاح وموثق",
        "color_class": "danger"
    }
]

def get_reports_registry():
    return REPORTS_REGISTRY
