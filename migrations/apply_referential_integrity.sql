-- SQL Migration Script for School Management System
-- Purpose: Convert MyISAM tables to InnoDB and apply 52 Referential Integrity Foreign Key Constraints
-- Generated for environment reproducibility

-- 1. Convert all 29 tables to InnoDB
ALTER TABLE `attendance` ENGINE = InnoDB;
ALTER TABLE `audit_logs` ENGINE = InnoDB;
ALTER TABLE `classes` ENGINE = InnoDB;
ALTER TABLE `classessections` ENGINE = InnoDB;
ALTER TABLE `classsubject` ENGINE = InnoDB;
ALTER TABLE `country` ENGINE = InnoDB;
ALTER TABLE `days` ENGINE = InnoDB;
ALTER TABLE `detailmarks` ENGINE = InnoDB;
ALTER TABLE `directorate` ENGINE = InnoDB;
ALTER TABLE `examschedule` ENGINE = InnoDB;
ALTER TABLE `governorates` ENGINE = InnoDB;
ALTER TABLE `homework` ENGINE = InnoDB;
ALTER TABLE `homeworkmarks` ENGINE = InnoDB;
ALTER TABLE `lessons` ENGINE = InnoDB;
ALTER TABLE `marks` ENGINE = InnoDB;
ALTER TABLE `messages` ENGINE = InnoDB;
ALTER TABLE `notifications` ENGINE = InnoDB;
ALTER TABLE `qualifications` ENGINE = InnoDB;
ALTER TABLE `school` ENGINE = InnoDB;
ALTER TABLE `schooltable` ENGINE = InnoDB;
ALTER TABLE `schooltabletypeexam` ENGINE = InnoDB;
ALTER TABLE `sections` ENGINE = InnoDB;
ALTER TABLE `student` ENGINE = InnoDB;
ALTER TABLE `subject` ENGINE = InnoDB;
ALTER TABLE `teacher` ENGINE = InnoDB;
ALTER TABLE `teachersubject` ENGINE = InnoDB;
ALTER TABLE `terms` ENGINE = InnoDB;
ALTER TABLE `typeexams` ENGINE = InnoDB;
ALTER TABLE `users` ENGINE = InnoDB;

-- 2. Add required indexes
CREATE INDEX `idx_marks_HomeworkID` ON `marks` (`HomeworkID`);
CREATE INDEX `idx_detailmarks_HomeworkID` ON `detailmarks` (`HomeworkID`);

-- 3. Cleanup Orphan Test Data SID=7 (if exists)
DELETE FROM `student` WHERE `SID` = 7;

-- 4. Apply 52 Foreign Key Constraints
ALTER TABLE `teacher` ADD CONSTRAINT `fk_teacher_QID_qualifications_QID` FOREIGN KEY (`QID`) REFERENCES `qualifications` (`QID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `teacher` ADD CONSTRAINT `fk_teacher_user_id_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT;

ALTER TABLE `student` ADD CONSTRAINT `fk_student_CountryID_country_CountryID` FOREIGN KEY (`CountryID`) REFERENCES `country` (`CountryID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `student` ADD CONSTRAINT `fk_student_G_ID_governorates_G_ID` FOREIGN KEY (`G_ID`) REFERENCES `governorates` (`G_ID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `student` ADD CONSTRAINT `fk_student_DiscID_directorate_DiscID` FOREIGN KEY (`DiscID`) REFERENCES `directorate` (`DiscID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `student` ADD CONSTRAINT `fk_student_CID_classes_CID` FOREIGN KEY (`CID`) REFERENCES `classes` (`CID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `student` ADD CONSTRAINT `fk_student_SectionID_sections_SectionID` FOREIGN KEY (`SectionID`) REFERENCES `sections` (`SectionID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `attendance` ADD CONSTRAINT `fk_attendance_SID_student_SID` FOREIGN KEY (`SID`) REFERENCES `student` (`SID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `examschedule` ADD CONSTRAINT `fk_examschedule_SubID_subject_SubID` FOREIGN KEY (`SubID`) REFERENCES `subject` (`SubID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `examschedule` ADD CONSTRAINT `fk_examschedule_CID_classes_CID` FOREIGN KEY (`CID`) REFERENCES `classes` (`CID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `examschedule` ADD CONSTRAINT `fk_examschedule_SectionID_sections_SectionID` FOREIGN KEY (`SectionID`) REFERENCES `sections` (`SectionID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `examschedule` ADD CONSTRAINT `fk_examschedule_T_ID_terms_T_ID` FOREIGN KEY (`T_ID`) REFERENCES `terms` (`T_ID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `schooltable` ADD CONSTRAINT `fk_schooltable_CID_classes_CID` FOREIGN KEY (`CID`) REFERENCES `classes` (`CID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `schooltable` ADD CONSTRAINT `fk_schooltable_SectionID_sections_SectionID` FOREIGN KEY (`SectionID`) REFERENCES `sections` (`SectionID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `schooltable` ADD CONSTRAINT `fk_schooltable_DayID_days_DayID` FOREIGN KEY (`DayID`) REFERENCES `days` (`DayID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `schooltable` ADD CONSTRAINT `fk_schooltable_LessonID_lessons_LessonID` FOREIGN KEY (`LessonID`) REFERENCES `lessons` (`LessonID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `schooltable` ADD CONSTRAINT `fk_schooltable_TeacherID_teacher_TeacherID` FOREIGN KEY (`TeacherID`) REFERENCES `teacher` (`TeacherID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `schooltable` ADD CONSTRAINT `fk_schooltable_SubID_subject_SubID` FOREIGN KEY (`SubID`) REFERENCES `subject` (`SubID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `schooltable` ADD CONSTRAINT `fk_schooltable_T_ID_terms_T_ID` FOREIGN KEY (`T_ID`) REFERENCES `terms` (`T_ID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `schooltabletypeexam` ADD CONSTRAINT `fk_schooltabletypeexam_ExamID_typeexams_ExamID` FOREIGN KEY (`ExamID`) REFERENCES `typeexams` (`ExamID`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `schooltabletypeexam` ADD CONSTRAINT `fk_schooltabletypeexam_SchoolTableID_schooltable_SchoolTableID` FOREIGN KEY (`SchoolTableID`) REFERENCES `schooltable` (`SchoolTableID`) ON DELETE CASCADE ON UPDATE RESTRICT;

ALTER TABLE `marks` ADD CONSTRAINT `fk_marks_SID_student_SID` FOREIGN KEY (`SID`) REFERENCES `student` (`SID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `marks` ADD CONSTRAINT `fk_marks_SubID_subject_SubID` FOREIGN KEY (`SubID`) REFERENCES `subject` (`SubID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `marks` ADD CONSTRAINT `fk_marks_ExamID_typeexams_ExamID` FOREIGN KEY (`ExamID`) REFERENCES `typeexams` (`ExamID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `marks` ADD CONSTRAINT `fk_marks_HomeworkID_homework_id` FOREIGN KEY (`HomeworkID`) REFERENCES `homework` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `marks` ADD CONSTRAINT `fk_marks_TeacherID_teacher_TeacherID` FOREIGN KEY (`TeacherID`) REFERENCES `teacher` (`TeacherID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `marks` ADD CONSTRAINT `fk_marks_T_ID_terms_T_ID` FOREIGN KEY (`T_ID`) REFERENCES `terms` (`T_ID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `detailmarks` ADD CONSTRAINT `fk_detailmarks_SID_student_SID` FOREIGN KEY (`SID`) REFERENCES `student` (`SID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `detailmarks` ADD CONSTRAINT `fk_detailmarks_ExamID_typeexams_ExamID` FOREIGN KEY (`ExamID`) REFERENCES `typeexams` (`ExamID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `detailmarks` ADD CONSTRAINT `fk_detailmarks_HomeworkID_homework_id` FOREIGN KEY (`HomeworkID`) REFERENCES `homework` (`id`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `detailmarks` ADD CONSTRAINT `fk_detailmarks_SubID_subject_SubID` FOREIGN KEY (`SubID`) REFERENCES `subject` (`SubID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `detailmarks` ADD CONSTRAINT `fk_detailmarks_TeacherID_teacher_TeacherID` FOREIGN KEY (`TeacherID`) REFERENCES `teacher` (`TeacherID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `detailmarks` ADD CONSTRAINT `fk_detailmarks_T_ID_terms_T_ID` FOREIGN KEY (`T_ID`) REFERENCES `terms` (`T_ID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `homeworkmarks` ADD CONSTRAINT `fk_homeworkmarks_SID_student_SID` FOREIGN KEY (`SID`) REFERENCES `student` (`SID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `homeworkmarks` ADD CONSTRAINT `fk_homeworkmarks_SubID_subject_SubID` FOREIGN KEY (`SubID`) REFERENCES `subject` (`SubID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `homeworkmarks` ADD CONSTRAINT `fk_homeworkmarks_HomeworkID_homework_id` FOREIGN KEY (`HomeworkID`) REFERENCES `homework` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `homeworkmarks` ADD CONSTRAINT `fk_homeworkmarks_TeacherID_teacher_TeacherID` FOREIGN KEY (`TeacherID`) REFERENCES `teacher` (`TeacherID`) ON DELETE SET NULL ON UPDATE RESTRICT;
ALTER TABLE `homeworkmarks` ADD CONSTRAINT `fk_homeworkmarks_T_ID_terms_T_ID` FOREIGN KEY (`T_ID`) REFERENCES `terms` (`T_ID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `homework` ADD CONSTRAINT `fk_homework_sub_id_subject_SubID` FOREIGN KEY (`sub_id`) REFERENCES `subject` (`SubID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `homework` ADD CONSTRAINT `fk_homework_class_id_classes_CID` FOREIGN KEY (`class_id`) REFERENCES `classes` (`CID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `homework` ADD CONSTRAINT `fk_homework_section_id_sections_SectionID` FOREIGN KEY (`section_id`) REFERENCES `sections` (`SectionID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `messages` ADD CONSTRAINT `fk_messages_sender_id_users_id` FOREIGN KEY (`sender_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `messages` ADD CONSTRAINT `fk_messages_recipient_id_users_id` FOREIGN KEY (`recipient_id`) REFERENCES `users` (`id`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `notifications` ADD CONSTRAINT `fk_notifications_user_id_users_id` FOREIGN KEY (`user_id`) REFERENCES `users` (`id`) ON DELETE CASCADE ON UPDATE RESTRICT;

ALTER TABLE `governorates` ADD CONSTRAINT `fk_governorates_CountryID_country_CountryID` FOREIGN KEY (`CountryID`) REFERENCES `country` (`CountryID`) ON DELETE RESTRICT ON UPDATE RESTRICT;
ALTER TABLE `directorate` ADD CONSTRAINT `fk_directorate_G_ID_governorates_G_ID` FOREIGN KEY (`G_ID`) REFERENCES `governorates` (`G_ID`) ON DELETE RESTRICT ON UPDATE RESTRICT;

ALTER TABLE `classessections` ADD CONSTRAINT `fk_classessections_CID_classes_CID` FOREIGN KEY (`CID`) REFERENCES `classes` (`CID`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `classessections` ADD CONSTRAINT `fk_classessections_SectionID_sections_SectionID` FOREIGN KEY (`SectionID`) REFERENCES `sections` (`SectionID`) ON DELETE CASCADE ON UPDATE RESTRICT;

ALTER TABLE `classsubject` ADD CONSTRAINT `fk_classsubject_SubID_subject_SubID` FOREIGN KEY (`SubID`) REFERENCES `subject` (`SubID`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `classsubject` ADD CONSTRAINT `fk_classsubject_CID_classes_CID` FOREIGN KEY (`CID`) REFERENCES `classes` (`CID`) ON DELETE CASCADE ON UPDATE RESTRICT;

ALTER TABLE `teachersubject` ADD CONSTRAINT `fk_teachersubject_SubID_subject_SubID` FOREIGN KEY (`SubID`) REFERENCES `subject` (`SubID`) ON DELETE CASCADE ON UPDATE RESTRICT;
ALTER TABLE `teachersubject` ADD CONSTRAINT `fk_teachersubject_TeacherID_teacher_TeacherID` FOREIGN KEY (`TeacherID`) REFERENCES `teacher` (`TeacherID`) ON DELETE CASCADE ON UPDATE RESTRICT;
