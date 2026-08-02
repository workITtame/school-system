import time
from utils.pdf_generator import generate_student_pdf

class DummyStudent:
    SID = 123
    SName = "أحمد محمد"
    class_rel = None
    section_rel = None

class DummyMark:
    SubID = 1
    subject = None
    Score = 95
    Grade = "A"

def test():
    print("Starting generation...")
    t0 = time.time()
    student = DummyStudent()
    report_data = {"امتحان النصف الأول": [DummyMark(), DummyMark()]}
    
    generate_student_pdf(student, report_data)
    t1 = time.time()
    
    print(f"Generated in {t1 - t0:.2f} seconds")

if __name__ == "__main__":
    test()
