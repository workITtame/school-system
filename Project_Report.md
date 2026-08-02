# تقرير مشروع نظام إدارة المدرسة الاحترافي

## 1. المقدمة (Introduction)
يعتبر قطاع التعليم من أهم القطاعات التي تتطلب تنظيماً عالياً ودقة في إدارة البيانات. تم تطوير **نظام الإدارة المدرسية الاحترافي** لتوفير منصة ويب متكاملة تسهّل على المدارس إدارة كافة شؤونها الأكاديمية والإدارية. تم بناء النظام باستخدام إطار عمل Flask (Python) وقاعدة بيانات علائقية، مع واجهات مستخدم عصرية (Bootstrap 5) وميزات متقدمة.

## 2. المشكلة (Problem Statement)
تعاني العديد من المدارس من:
- صعوبة في إدارة بيانات الطلاب والمعلمين بشكل يدوي ومشتت.
- غياب آلية ذكية لاكتشاف وتجنب تعارض الحصص للمعلمين في الجدول الدراسي.
- صعوبة في تتبع درجات الطلاب وإنشاء تقارير أكاديمية دورية بشكل سريع ومنظم.
- بطء في الوصول إلى الإحصائيات العامة للمدرسة.

## 3. أهداف النظام (System Objectives)
تم تصميم هذا النظام لتحقيق الأهداف التالية:
1. **إدارة المستخدمين والصلاحيات**: توفير نظام دخول آمن للإدارة والمعلمين.
2. **إدارة الطلاب والمعلمين**: القدرة الكاملة على إضافة وتعديل وحذف بيانات الطلاب والمعلمين بدقة.
3. **التنظيم الأكاديمي**: بناء هيكل مترابط للصفوف، الشعب، والمواد الدراسية.
4. **الجدول الدراسي الذكي**: ميزة فريدة لاكتشاف وتنبيه المستخدم عند وجود تعارض في حصص المعلم (Conflict Detection).
5. **إدارة الاختبارات والدرجات**: إدخال درجات الطلاب وتقييمها آلياً.
6. **التقارير والإحصائيات**: توفير لوحة تحكم سريعة (Dashboard) مع بحث فوري، وطباعة كشوفات الدرجات.

## 4. مخطط الكيانات والعلاقات (ERD)
فيما يلي الهيكل المصحح لقاعدة البيانات الذي يوضح الروابط (Many-to-Many و One-to-Many) بشكل دقيق:

```mermaid
erDiagram
    USERS {
        int id PK
        string username
        string password_hash
        string name
        string role "admin, teacher"
    }
    
    TEACHERS {
        int id PK
        int user_id FK
        string phone
        string specialty
    }
    
    STUDENTS {
        int id PK
        string name
        string gender
        string parent_name
        string parent_number
        string photo_path
        int class_id FK
        int section_id FK
    }
    
    CLASSES {
        int id PK
        string name
    }
    
    SECTIONS {
        int id PK
        string name
        int class_id FK
    }
    
    SUBJECTS {
        int id PK
        string name
    }
    
    EXAMS {
        int id PK
        string name
        date date
    }
    
    GRADES {
        int id PK
        float score
        int student_id FK
        int subject_id FK
        int exam_id FK
    }
    
    TIMETABLES {
        int id PK
        string day_of_week
        int period_number
        int class_id FK
        int section_id FK
        int subject_id FK
        int teacher_id FK
    }

    TEACHER_SUBJECT {
        int teacher_id FK
        int subject_id FK
    }

    USERS ||--o| TEACHERS : "has profile"
    CLASSES ||--o{ SECTIONS : "has"
    CLASSES ||--o{ STUDENTS : "contains"
    SECTIONS ||--o{ STUDENTS : "contains"
    
    TEACHERS ||--o{ TEACHER_SUBJECT : "teaches"
    SUBJECTS ||--o{ TEACHER_SUBJECT : "taught by"
    
    STUDENTS ||--o{ GRADES : "receives"
    SUBJECTS ||--o{ GRADES : "for"
    EXAMS ||--o{ GRADES : "includes"
    
    CLASSES ||--o{ TIMETABLES : "scheduled"
    SECTIONS ||--o{ TIMETABLES : "scheduled"
    SUBJECTS ||--o{ TIMETABLES : "scheduled"
    TEACHERS ||--o{ TIMETABLES : "teaches"
```

## 5. التقنيات المستخدمة
- **الخلفية (Backend):** Python, Flask, SQLAlchemy.
- **قاعدة البيانات (Database):** MySQL (pymysql) بدلاً من SQLite كما تم التعديل مؤخراً.
- **الواجهة الأمامية (Frontend):** HTML5, CSS3, Bootstrap 5 RTL, JavaScript.
- **الهيكلة:** بنية Modular باستخدام Flask Blueprints لضمان نظافة الكود (Clean Architecture).

---
*تم إنشاء هذا التقرير كجزء من توثيق نهاية مرحلة التطوير للمشروع.*
