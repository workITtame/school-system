from models.extensions import ma
from models.student import Student
from models.teacher import Teacher
from models.academic import Classes
from models.timetable import SchoolTable

class SchoolTableSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = SchoolTable
        load_instance = True
        include_fk = True

school_table_schema = SchoolTableSchema()
school_tables_schema = SchoolTableSchema(many=True)

class StudentSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Student
        load_instance = True
        include_fk = True

student_schema = StudentSchema()
students_schema = StudentSchema(many=True)

class TeacherSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Teacher
        load_instance = True
        include_fk = True

teacher_schema = TeacherSchema()
teachers_schema = TeacherSchema(many=True)

class ClassesSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Classes
        load_instance = True
        include_fk = True

class_schema = ClassesSchema()
classes_schema = ClassesSchema(many=True)
