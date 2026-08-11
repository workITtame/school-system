from .extensions import db
from .user import User
from .school import School
from .teacher import Teacher, Qualifications
from .geographic import Country, Governorates, Directorate
from .academic import Classes, Sections, ClassesSections, Subject, ClassSubject, Days, Lessons, Terms, ExamSchedule
from .student import Student, Attendance
from .timetable import SchoolTable, TypeExams, SchoolTableTypeExam
from .grade import Marks, DetailMarks, HomeworkMarks
from .message import Message
from .homework import Homework
from .notification import Notification

__all__ = [
    'User',
    'School',
    'Teacher',
    'Qualifications',
    'Country',
    'Governorates',
    'Directorate',
    'Classes',
    'Sections',
    'ClassesSections',
    'Subject',
    'ClassSubject',
    'Days',
    'Lessons',
    'Terms',
    'Student',
    'Attendance',
    'SchoolTable',
    'TypeExams',
    'SchoolTableTypeExam',
    'Marks',
    'DetailMarks',
    'HomeworkMarks',
    'ExamSchedule',
    'Message',
    'Homework',
    'Notification'
]
