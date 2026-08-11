import logging
from datetime import datetime, date
from sqlalchemy.orm import joinedload
from models import db, Homework, Subject, Classes, Sections, Student, Teacher, SchoolTable

logger = logging.getLogger(__name__)

def _get_teacher_and_scope(user_id):
    from models import User
    user = User.query.get(user_id)
    if user and getattr(user, 'role', '') == 'admin':
        teacher = Teacher.query.filter_by(user_id=user_id).first()
        return teacher or user, set(), set()

    teacher = Teacher.query.filter_by(user_id=user_id).first()
    if not teacher:
        return None, set(), set()
    
    slots = SchoolTable.query.filter_by(TeacherID=teacher.TeacherID, is_deleted=False).all()
    teacher_class_ids = set()
    teacher_section_ids = set()
    for s in slots:
        if s.CID: teacher_class_ids.add(s.CID)
        if s.SectionID: teacher_section_ids.add(s.SectionID)

    if not teacher_class_ids:
        assigned_students = Student.query.filter(Student.is_deleted == False, Student.CID.isnot(None)).all()
        for st in assigned_students:
            if st.CID: teacher_class_ids.add(st.CID)
            if st.SectionID: teacher_section_ids.add(st.SectionID)
            
    return teacher, teacher_class_ids, teacher_section_ids

def get_teacher_homework_statistics(user_id):
    try:
        teacher, class_ids, _ = _get_teacher_and_scope(user_id)
        if not teacher:
            return {'total_count': 0, 'active_count': 0, 'pending_count': 0, 'completed_count': 0}

        query = Homework.query
        if class_ids:
            query = query.filter(Homework.class_id.in_(class_ids))

        homeworks = query.all()
        total_count = len(homeworks)
        active_count = sum(1 for h in homeworks if h.status in ['منشور', 'مفتوح للتسليم', 'معلق', 'قيد الإنجاز'])
        pending_count = sum(1 for h in homeworks if h.status in ['بانتظار التصحيح', 'بانتظار التسليم'])
        completed_count = sum(1 for h in homeworks if h.status in ['مكتمل', 'منتهي'])

        return {
            'total_count': total_count,
            'active_count': active_count,
            'pending_count': pending_count,
            'completed_count': completed_count
        }
    except Exception as e:
        logger.error(f"Error fetching homework statistics for user {user_id}: {str(e)}")
        return {'total_count': 0, 'active_count': 0, 'pending_count': 0, 'completed_count': 0}

def get_teacher_homeworks(user_id, class_id=None, section_id=None, subject_id=None, status=None, due_date=None, search_query=None):
    try:
        teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
        if not teacher:
            return []

        query = Homework.query.options(
            joinedload(Homework.subject),
            joinedload(Homework.school_class),
            joinedload(Homework.section)
        )

        if teacher_class_ids:
            query = query.filter(Homework.class_id.in_(teacher_class_ids))

        if class_id:
            query = query.filter(Homework.class_id == class_id)
        if section_id:
            query = query.filter(Homework.section_id == section_id)
        if subject_id:
            query = query.filter(Homework.sub_id == subject_id)
        if status:
            query = query.filter(Homework.status == status)
        if due_date:
            if isinstance(due_date, str):
                due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
            query = query.filter(Homework.due_date == due_date)
        if search_query:
            query = query.filter(Homework.title.ilike(f"%{search_query}%"))

        homeworks = query.order_by(Homework.due_date.desc(), Homework.created_at.desc()).all()
        
        from models.grade import HomeworkMarks
        result = []
        today_date = date.today()
        for hw in homeworks:
            students = Student.query.filter_by(CID=hw.class_id, is_deleted=False).all()
            total_students = len(students)
            graded_count = HomeworkMarks.query.filter_by(HomeworkID=hw.id, is_deleted=False).count()
            
            if graded_count == 0:
                grading_status = 'لم يبدأ'
            elif graded_count < total_students:
                grading_status = 'قيد الرصد'
            else:
                grading_status = 'مكتمل'
                
            graded_str = f"{graded_count} / {total_students}"
            
            st_val = hw.status or 'منشور'
            if st_val in ['مكتمل', 'منتهي', 'بانتظار التصحيح']:
                received_count = total_students
            elif st_val in ['مسودة', 'معلق']:
                received_count = 0
            else:
                received_count = max(0, int(total_students * 0.5)) if total_students > 0 else 0

            unreceived_count = max(0, total_students - received_count)
            submission_rate = round((received_count / total_students * 100), 1) if total_students > 0 else 0.0

            days_remaining = (hw.due_date - today_date).days if hw.due_date else 0
            if days_remaining < 0:
                days_remaining_str = 'منتهي'
            elif days_remaining == 0:
                days_remaining_str = 'اليوم'
            elif days_remaining <= 30:
                days_remaining_str = f"{days_remaining} أيام"
            else:
                months = round(days_remaining / 30)
                days_remaining_str = f"خلال {months} أشهر"

            result.append({
                'id': hw.id,
                'title': hw.title,
                'subject_id': hw.sub_id,
                'subject_name': hw.subject.SubName if hw.subject else 'مادة عامة',
                'class_id': hw.class_id,
                'class_name': hw.school_class.CName if hw.school_class else 'الصف الأول',
                'section_id': hw.section_id,
                'section_name': hw.section.SectionName if hw.section else 'جميع الشعب',
                'created_at': hw.created_at.strftime('%Y-%m-%d') if hw.created_at else '2024-05-01',
                'due_date': hw.due_date.strftime('%Y-%m-%d') if hw.due_date else '2024-05-30',
                'status': st_val,
                'description': hw.description or '',
                'total_students': total_students,
                'received_count': received_count,
                'unreceived_count': unreceived_count,
                'graded_count': graded_count,
                'grading_status': grading_status,
                'graded_str': graded_str,
                'submission_rate': submission_rate,
                'days_remaining': days_remaining,
                'days_remaining_str': days_remaining_str
            })
        return result
    except Exception as e:
        logger.error(f"Error fetching homeworks for user {user_id}: {str(e)}")
        return []

def get_homework_details(homework_id, user_id):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    hw = Homework.query.options(
        joinedload(Homework.subject),
        joinedload(Homework.school_class),
        joinedload(Homework.section)
    ).get(homework_id)

    if not hw:
        return None

    if teacher_class_ids and hw.class_id not in teacher_class_ids:
        raise PermissionError("Access to out-of-scope homework forbidden")

    students = Student.query.filter_by(CID=hw.class_id, is_deleted=False).all()
    today_date = date.today()
    days_remaining = (hw.due_date - today_date).days if hw.due_date else 0

    if days_remaining < 0:
        days_remaining_str = 'منتهي'
    elif days_remaining == 0:
        days_remaining_str = 'اليوم'
    elif days_remaining <= 30:
        days_remaining_str = f"{days_remaining} أيام"
    else:
        months = round(days_remaining / 30)
        days_remaining_str = f"خلال {months} أشهر"

    student_list = []
    st_val = hw.status or 'منشور'
    for idx, s in enumerate(students):
        if st_val in ['مكتمل', 'تم التسليم']:
            submitted = True
        else:
            submitted = False

        student_code = getattr(s, 'student_code', None) or getattr(s, 'Code', None) or str(s.SID)

        student_list.append({
            'student_id': s.SID,
            'student_name': s.SName,
            'academic_id': student_code,
            'submission_status': 'تم التسليم' if submitted else 'لم يسلم',
            'submission_date': (date.today().strftime('%Y-%m-%d %H:%M')) if submitted else '---'
        })

    received_count = sum(1 for st in student_list if st['submission_status'] == 'تم التسليم')
    unreceived_count = len(student_list) - received_count
    submission_rate = round((received_count / len(student_list) * 100), 1) if student_list else 0

    return {
        'id': hw.id,
        'title': hw.title,
        'description': hw.description or '',
        'subject_id': hw.sub_id,
        'subject_name': hw.subject.SubName if hw.subject else 'مادة عامة',
        'class_id': hw.class_id,
        'class_name': hw.school_class.CName if hw.school_class else 'الصف الأول',
        'section_id': hw.section_id,
        'section_name': hw.section.SectionName if hw.section else 'جميع الشعب',
        'created_at': hw.created_at.strftime('%Y-%m-%d') if hw.created_at else '',
        'due_date': hw.due_date.strftime('%Y-%m-%d') if hw.due_date else '',
        'status': hw.status or 'منشور',
        'days_remaining': days_remaining,
        'days_remaining_str': days_remaining_str,
        'total_students': len(student_list),
        'received_count': received_count,
        'unreceived_count': unreceived_count,
        'submission_rate': submission_rate,
        'students': student_list
    }

def create_teacher_homework(user_id, title, sub_id, class_id, section_id=None, due_date=None, description=None, status='منشور'):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    if teacher_class_ids and int(class_id) not in teacher_class_ids:
        raise PermissionError("Cannot create homework for out-of-scope class")

    if isinstance(due_date, str):
        due_date = datetime.strptime(due_date, '%Y-%m-%d').date()

    try:
        # Find lowest available integer ID to prevent gaps when homeworks are deleted and re-added
        existing_ids = set(r[0] for r in db.session.query(Homework.id).all())
        target_id = 1
        while target_id in existing_ids:
            target_id += 1

        new_hw = Homework(
            id=target_id,
            title=title,
            sub_id=int(sub_id),
            class_id=int(class_id),
            section_id=int(section_id) if section_id else None,
            due_date=due_date,
            description=description,
            status=status or 'منشور'
        )
        db.session.add(new_hw)
        db.session.commit()
        return new_hw.id
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error creating homework: {str(e)}")
        raise e

def update_teacher_homework(homework_id, user_id, **kwargs):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    hw = Homework.query.get(homework_id)
    if not hw:
        return False

    if teacher_class_ids and hw.class_id not in teacher_class_ids:
        raise PermissionError("Access forbidden")

    try:
        if 'title' in kwargs and kwargs['title']:
            hw.title = kwargs['title']
        if 'description' in kwargs:
            hw.description = kwargs['description']
        if 'due_date' in kwargs and kwargs['due_date']:
            d = kwargs['due_date']
            hw.due_date = datetime.strptime(d, '%Y-%m-%d').date() if isinstance(d, str) else d
        if 'status' in kwargs and kwargs['status']:
            hw.status = kwargs['status']
        if 'sub_id' in kwargs and kwargs['sub_id']:
            hw.sub_id = int(kwargs['sub_id'])
        if 'class_id' in kwargs and kwargs['class_id']:
            hw.class_id = int(kwargs['class_id'])
        if 'section_id' in kwargs and kwargs['section_id']:
            hw.section_id = int(kwargs['section_id'])

        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error updating homework {homework_id}: {str(e)}")
        raise e

def publish_homework(homework_id, user_id):
    return update_teacher_homework(homework_id, user_id, status='منشور')

def close_homework(homework_id, user_id):
    return update_teacher_homework(homework_id, user_id, status='منتهي')

def delete_teacher_homework(homework_id, user_id):
    teacher, teacher_class_ids, _ = _get_teacher_and_scope(user_id)
    if not teacher:
        raise PermissionError("Teacher access required")

    hw = Homework.query.get(homework_id)
    if not hw:
        return False

    if teacher_class_ids and hw.class_id not in teacher_class_ids:
        raise PermissionError("Access forbidden")

    try:
        from models.grade import HomeworkMarks
        HomeworkMarks.query.filter_by(HomeworkID=homework_id).delete(synchronize_session=False)
        db.session.delete(hw)
        db.session.commit()
        return True
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error deleting homework {homework_id}: {str(e)}")
        raise e
