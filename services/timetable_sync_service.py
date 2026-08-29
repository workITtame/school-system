from models import db, Subject, Classes, Sections, SchoolTable

def sync_subject_timetable_slots(subject_id):
    """
    Synchronizes SchoolTable entries for a subject matching its assigned classes, sections, and WeeklyHours.
    """
    subject = Subject.query.get(subject_id)
    if not subject or getattr(subject, 'is_deleted', False):
        SchoolTable.query.filter_by(SubID=subject_id).update({'is_deleted': True})
        db.session.commit()
        return

    weekly_hours = getattr(subject, 'WeeklyHours', 4) or 4
    linked_classes = [c for c in (subject.classes or []) if not getattr(c, 'is_deleted', False)]
    linked_class_ids = [c.CID for c in linked_classes]

    # Soft-delete slots for classes no longer linked to this subject
    if linked_class_ids:
        SchoolTable.query.filter(
            SchoolTable.SubID == subject_id,
            SchoolTable.CID.not_in(linked_class_ids)
        ).update({'is_deleted': True}, synchronize_session=False)
    else:
        SchoolTable.query.filter_by(SubID=subject_id).update({'is_deleted': True})

    db.session.flush()

    # Assigned teacher if any (subject.teachers is AppenderQuery)
    assigned_teacher = None
    if hasattr(subject, 'teachers'):
        try:
            assigned_teacher = subject.teachers.first()
        except Exception:
            assigned_teacher = None
    teacher_id = assigned_teacher.TeacherID if assigned_teacher else None

    for cls in linked_classes:
        sections = [s for s in (cls.sections or []) if not getattr(s, 'is_deleted', False)]
        if not sections:
            sec = Sections.query.filter_by(is_deleted=False).first()
            sections = [sec] if sec else []

        for sec in sections:
            if not sec:
                continue
            sec_id = sec.SectionID
            
            # Existing active slots for this subject & class/section
            existing_active = SchoolTable.query.filter_by(
                CID=cls.CID,
                SectionID=sec_id,
                SubID=subject.SubID,
                is_deleted=False
            ).order_by(SchoolTable.SchoolTableID.asc()).all()

            for slot in existing_active:
                if teacher_id and slot.TeacherID != teacher_id:
                    # Verify no teacher conflict before updating
                    conflict = SchoolTable.query.filter(
                        SchoolTable.TeacherID == teacher_id,
                        SchoolTable.DayID == slot.DayID,
                        SchoolTable.LessonID == slot.LessonID,
                        SchoolTable.SchoolTableID != slot.SchoolTableID,
                        SchoolTable.is_deleted == False
                    ).first()
                    if not conflict:
                        slot.TeacherID = teacher_id
                    else:
                        slot.TeacherID = None

            if len(existing_active) > weekly_hours:
                for slot in existing_active[weekly_hours:]:
                    slot.is_deleted = True
            elif len(existing_active) < weekly_hours:
                slots_needed = weekly_hours - len(existing_active)
                
                # Distribute slots evenly (1 slot per day across Days 1..5)
                for pass_num in range(1, 6):
                    if slots_needed <= 0:
                        break
                    for day_id in range(1, 6):
                        if slots_needed <= 0:
                            break
                        
                        preferred_lesson_id = ((day_id - 1) % 5) + 1
                        lesson_candidates = [preferred_lesson_id] + [l for l in range(1, 6) if l != preferred_lesson_id]
                        
                        placed_today = False
                        for lesson_id in lesson_candidates:
                            # Check class slot collision
                            cls_slot = SchoolTable.query.filter_by(
                                CID=cls.CID,
                                SectionID=sec_id,
                                DayID=day_id,
                                LessonID=lesson_id
                            ).first()

                            # Check teacher slot collision
                            tch_slot = None
                            if teacher_id:
                                tch_slot = SchoolTable.query.filter_by(
                                    TeacherID=teacher_id,
                                    DayID=day_id,
                                    LessonID=lesson_id
                                ).first()

                            # If teacher has an active slot elsewhere, skip
                            if tch_slot and tch_slot != cls_slot and not tch_slot.is_deleted:
                                continue

                            if cls_slot:
                                if cls_slot.is_deleted or cls_slot.SubID == subject.SubID:
                                    cls_slot.is_deleted = False
                                    cls_slot.SubID = subject.SubID
                                    cls_slot.TeacherID = teacher_id if (not tch_slot or tch_slot == cls_slot) else None
                                    cls_slot.T_ID = 1
                                    slots_needed -= 1
                                    placed_today = True
                                    break
                                else:
                                    continue
                            else:
                                if tch_slot and not tch_slot.is_deleted:
                                    continue
                                    
                                effective_teacher = teacher_id if (not tch_slot or tch_slot.is_deleted) else None
                                if tch_slot and tch_slot.is_deleted:
                                    tch_slot.TeacherID = None
                                    db.session.flush()

                                new_slot = SchoolTable(
                                    CID=cls.CID,
                                    SectionID=sec_id,
                                    DayID=day_id,
                                    LessonID=lesson_id,
                                    SubID=subject.SubID,
                                    TeacherID=effective_teacher,
                                    T_ID=1,
                                    is_deleted=False
                                )
                                db.session.add(new_slot)
                                slots_needed -= 1
                                placed_today = True
                                break
                        
                        if placed_today and slots_needed <= 0:
                            break
                            
    db.session.commit()

def sync_all_active_subject_timetable_slots():
    """
    Synchronizes SchoolTable for all active subjects in the database.
    """
    active_subjects = Subject.query.filter_by(is_deleted=False).all()
    for s in active_subjects:
        sync_subject_timetable_slots(s.SubID)
