from fpdf import FPDF
import io

class StudentReportPDF(FPDF):
    def __init__(self, student, report_data):
        # Landscape A4 for certificate look
        super().__init__(orientation="L", unit="mm", format="A4")
        self.student = student
        self.report_data = report_data
        
        # Add fonts
        font_path = r"C:\Windows\Fonts\arial.ttf"
        font_path_b = r"C:\Windows\Fonts\arialbd.ttf"
        try:
            self.add_font("Arial", fname=font_path)
            self.add_font("Arial", style="B", fname=font_path_b)
            self.set_text_shaping(True)
        except Exception as e:
            print("Font error:", e)
        
    def header(self):
        # Draw Certificate Borders
        self.set_line_width(1.5)
        self.set_draw_color(25, 135, 84) # Success green
        self.rect(10, 10, 277, 190)
        self.set_line_width(0.5)
        self.set_draw_color(0, 0, 0)
        self.rect(12, 12, 273, 186)
        
        self.set_y(20)
        self.set_font("Arial", style="B", size=24)
        self.set_text_color(25, 135, 84)
        self.cell(0, 10, text="مدرسة الأجيال المبدعة", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.set_font("Arial", size=16)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, text="إدارة التقييم والاختبارات", align="C", new_x="LMARGIN", new_y="NEXT")
        
        self.ln(5)
        self.set_font("Arial", style="B", size=32)
        self.set_text_color(0, 0, 0)
        self.cell(0, 20, text="شــهـادة إشـعــار درجــات", align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(5)
        
    def footer(self):
        self.set_y(-25)
        self.set_font("Arial", size=10)
        self.set_text_color(150, 150, 150)
        self.cell(0, 10, text="هذه الشهادة معتمدة من إدارة المدرسة ولا تحتاج إلى توقيع إضافي إلا إذا طلب ذلك.", align="C")

def generate_student_pdf(student, report_data):
    pdf = StudentReportPDF(student, report_data)
    pdf.add_page()
    pdf.set_font("Arial", size=16)
    pdf.set_text_color(0, 0, 0)
    
    cname = student.school_class.CName if student.school_class else "غير محدد"
    sname = student.section.SectionName if student.section else "غير محدد"
    
    # Intro text
    intro_text = f"تشهد إدارة المدرسة بأن الطالب/ـة: {student.SName}"
    pdf.set_font("Arial", style="B", size=18)
    pdf.cell(0, 12, text=intro_text, align="C", new_x="LMARGIN", new_y="NEXT")
    
    pdf.set_font("Arial", size=16)
    details_text = f"المقيد بالرقم: {student.SID} | الصف: {cname} | الشعبة: {sname}"
    pdf.cell(0, 12, text=details_text, align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(10)
    
    # Calculate total marks to center the table
    # Landscape width = 297mm. Available width ~ 277mm.
    # We will make table width = 200mm and center it. (297 - 200) / 2 = 48.5 margin
    left_margin = 48.5
    col_w = [40, 40, 80, 40] # Total 200
    
    # Headers
    pdf.set_x(left_margin)
    pdf.set_font("Arial", style="B", size=14)
    pdf.set_fill_color(25, 135, 84) # Green
    pdf.set_text_color(255, 255, 255) # White text
    
    headers = ["التقدير", "الدرجة", "المادة الدراسية", "رقم المادة"]
    for i, h in enumerate(headers):
        pdf.cell(col_w[i], 12, text=h, border=1, align="C", fill=True)
    pdf.ln(12)
    
    pdf.set_text_color(0, 0, 0)
    
    for exam_name, marks in report_data.items():
        pdf.set_font("Arial", style="B", size=16)
        pdf.set_x(left_margin)
        pdf.cell(200, 12, text=f"--- {exam_name} ---", align="C", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("Arial", size=14)
        
        total = 0
        count = 0
        for m in marks:
            pdf.set_x(left_margin)
            sub_name = m.subject.SubName if m.subject else "غير محدد"
            pdf.cell(col_w[0], 12, text=str(m.Grade or '-'), border=1, align="C")
            pdf.cell(col_w[1], 12, text=str(m.Score if m.Score is not None else '-'), border=1, align="C")
            pdf.cell(col_w[2], 12, text=sub_name, border=1, align="C")
            pdf.cell(col_w[3], 12, text=str(m.SubID), border=1, align="C", new_x="LMARGIN", new_y="NEXT")
            if m.Score is not None:
                total += float(m.Score)
                count += 1
                
        if count > 0:
            pdf.set_x(left_margin)
            pdf.set_font("Arial", style="B", size=14)
            pdf.set_fill_color(240, 240, 240)
            avg = round(total / count, 2)
            pdf.cell(col_w[0], 12, text=f"{avg}%", border=1, align="C", fill=True)
            pdf.cell(col_w[1], 12, text=str(total), border=1, align="C", fill=True)
            pdf.cell(col_w[2] + col_w[3], 12, text="المجموع الكلي والمتوسط:", border=1, align="R", fill=True, new_x="LMARGIN", new_y="NEXT")
    
    pdf.ln(20)
    # Signatures
    pdf.set_font("Arial", style="B", size=16)
    pdf.set_x(left_margin)
    pdf.cell(66, 10, text="توقيع المعلم", align="C")
    pdf.cell(66, 10, text="توقيع الولي", align="C")
    pdf.cell(66, 10, text="ختم المدرسة", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_x(left_margin)
    pdf.cell(66, 10, text="...................", align="C")
    pdf.cell(66, 10, text="...................", align="C")
    pdf.cell(66, 10, text="...................", align="C", new_x="LMARGIN", new_y="NEXT")
            
    return pdf.output()
