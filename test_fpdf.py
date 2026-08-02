from fpdf import FPDF
import sys

def test():
    try:
        pdf = FPDF()
        pdf.add_font("Arial", fname="C:\\Windows\\Fonts\\arial.ttf")
        pdf.add_font("Arial", style="B", fname="C:\\Windows\\Fonts\\arialbd.ttf")
        pdf.set_font("Arial", size=14)
        pdf.set_text_shaping(True)
        pdf.add_page()
        pdf.cell(0, 10, text="مرحبا بك في مدرسة الأجيال", align="R", new_x="LMARGIN", new_y="NEXT")
        pdf.output("test_arabic.pdf")
        print("Success")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    test()
