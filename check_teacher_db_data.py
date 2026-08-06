from app import create_app
from models import Teacher, User, SchoolTable, Student, Homework, ExamSchedule, Message
from services.teacher_dashboard_service import get_teacher_by_user_id, get_dashboard_statistics, get_today_classes

app = create_app()
with app.app_context():
    print("--- TEACHERS IN DATABASE ---")
    teachers = Teacher.query.filter_by(is_deleted=False).all()
    for t in teachers[:5]:
        print(f"ID: {t.TeacherID}, Name: {t.TeacherName}, UserID: {t.user_id}, Email: {t.Email}")

    print("\n--- CHECKING CURRENT LOGGED IN TEACHER (سمير غانم علي حاتم) ---")
    samir = Teacher.query.filter(Teacher.TeacherName.like('%سمير%')).first()
    if samir:
        print(f"Found Teacher: {samir.TeacherName} (ID: {samir.TeacherID}, UserID: {samir.user_id})")
        stats = get_dashboard_statistics(samir)
        print("Stats:", stats)
        today_cls = get_today_classes(samir.TeacherID)
        print("Today's Classes Count:", len(today_cls))

    print("\n--- TIMETABLE SLOTS IN DATABASE ---")
    slots_count = SchoolTable.query.filter_by(is_deleted=False).count()
    print("Total timetable slots in SchoolTable:", slots_count)

    print("\n--- HOMEWORKS IN DATABASE ---")
    hw_count = Homework.query.count()
    print("Total homeworks in database:", hw_count)

    print("\n--- EXAMS IN DATABASE ---")
    exam_count = ExamSchedule.query.filter_by(is_deleted=False).count()
    print("Total exams in database:", exam_count)
