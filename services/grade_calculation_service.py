"""
Central Academic Grade Calculation Service
Single source of truth for grade calculations, averages, formulas, and pass/fail rules.
Preserves existing empirical business rules 100%.
"""
import logging

logger = logging.getLogger(__name__)

PASSING_SCORE_THRESHOLD = 60.0

EXAM_WEIGHT = 0.60
HOMEWORK_WEIGHT = 2.0  # Scale 0-10 -> max 20 points
PARTICIPATION_WEIGHT = 0.10
ATTENDANCE_WEIGHT = 0.10

def calculate_exam_average(scores):
    """
    Calculate average exam score on 0-100 scale.
    Omits None scores. Includes 0.0 scores.
    """
    valid_scores = [float(s) for s in scores if s is not None]
    if not valid_scores:
        return None
    return round(sum(valid_scores) / len(valid_scores), 1)

def calculate_homework_average(scores):
    """
    Calculate average homework score on 0-10 scale.
    Omits None scores. Includes 0.0 scores.
    """
    valid_scores = [float(s) for s in scores if s is not None]
    if not valid_scores:
        return None
    return round(sum(valid_scores) / len(valid_scores), 1)

def calculate_attendance_percentage(statuses):
    """
    Calculate attendance percentage from status list.
    Status 'حاضر' or 'present' counts as present.
    """
    if not statuses:
        return None
    present_cnt = sum(1 for s in statuses if s in ['حاضر', 'present'])
    return round((present_cnt / len(statuses)) * 100.0, 1)

def calculate_participation(attendance_pct):
    """
    Calculate participation score.
    If attendance_pct >= 90.0%, participation is 100.0%.
    Otherwise equals attendance_pct or 0.0 if None.
    """
    if attendance_pct is None:
        return 0.0
    if attendance_pct >= 90.0:
        return 100.0
    return float(attendance_pct)

def calculate_final_grade(exam_avg, hw_avg, participation, attendance_pct):
    """
    Synthesize Final Grade according to current business formula:
    Final Grade = round((hw_val * 2.0) + (exam_val * 0.6) + (part_val * 0.1) + (att_val * 0.1), 1)
    """
    hw_val = hw_avg if hw_avg is not None else 0.0
    exam_val = exam_avg if exam_avg is not None else 0.0
    part_val = participation if participation is not None else 0.0
    att_val = attendance_pct if attendance_pct is not None else 0.0

    if hw_avg is not None or exam_avg is not None:
        return round((hw_val * HOMEWORK_WEIGHT) + (exam_val * EXAM_WEIGHT) + (part_val * PARTICIPATION_WEIGHT) + (att_val * ATTENDANCE_WEIGHT), 1)
    return 0.0

def is_passing(score, threshold=PASSING_SCORE_THRESHOLD):
    """Check if score meets passing threshold (default 60.0%)."""
    if score is None:
        return False
    return float(score) >= threshold

def get_letter_grade_badge(final_grade):
    """Determine letter grade symbol and growth badge from final grade."""
    if final_grade is None:
        return "—", "غير مدخل", "غير مدخل"

    score = float(final_grade)
    if score >= 90.0:
        return f"🟢 ممتاز ({score}%)", "مستقر في التقييم الأكاديمي", 'ممتاز'
    elif score >= 80.0:
        return f"🟢 جيد جداً ({score}%)", "أداء جيد مستقر", 'جيد جداً'
    elif score >= 70.0:
        return f"🟡 جيد ({score}%)", "أداء جيد", 'جيد'
    elif score >= 60.0:
        return f"🟠 يحتاج متابعة ({score}%)", "يتطلب متابعة", 'يحتاج متابعة'
    else:
        return f"🔴 متعثر ({score}%)", "متعثر أكاديمياً", 'متعثر'
