import re

file_path = r'c:\Users\Owner\school-system\school-system\templates\academic\index.html'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Replace all occurrences of the icons with icon + text
content = content.replace('<i class="fa-solid fa-plus"></i>', '<i class="fa-solid fa-plus"></i> إضافة')
content = content.replace('<i class="fa-solid fa-pen"></i>', '<i class="fa-solid fa-pen"></i> تعديل')
content = content.replace('<i class="fa-solid fa-trash"></i>', '<i class="fa-solid fa-trash"></i> حذف')

with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)
print("Replaced successfully!")
