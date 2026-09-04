import os
import re
import sys
import glob

sys.path.insert(0, r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system')

def analyze_codebase():
    base_dir = r'c:\Users\Lenovo\OneDrive\Desktop\school-system\school-system\school-system'
    
    findings = {
        'legacy_query_get': [],
        'missing_error_handlers': [],
        'hardcoded_endpoints': [],
        'potential_n_plus_one': [],
        'todo_fixme_comments': [],
        'model_inconsistencies': []
    }

    py_files = glob.glob(os.path.join(base_dir, '**', '*.py'), recursive=True)
    html_files = glob.glob(os.path.join(base_dir, '**', '*.html'), recursive=True)

    # 1. Scan Python files for Legacy Query.get() and TODOs
    for file_path in py_files:
        if 'venv' in file_path or '.gemini' in file_path:
            continue
        rel_path = os.path.relpath(file_path, base_dir)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                for idx, line in enumerate(lines, 1):
                    # Check for Query.get()
                    if '.query.get(' in line:
                        findings['legacy_query_get'].append({
                            'file': rel_path,
                            'line': idx,
                            'content': line.strip()
                        })
                    # Check for TODO / FIXME
                    if 'TODO' in line or 'FIXME' in line or 'HACK' in line:
                        findings['todo_fixme_comments'].append({
                            'file': rel_path,
                            'line': idx,
                            'content': line.strip()
                        })
        except Exception as e:
            pass

    # 2. Scan HTML files for potential template bugs or inline scripts
    for file_path in html_files:
        if '.gemini' in file_path:
            continue
        rel_path = os.path.relpath(file_path, base_dir)
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
                # Check for hardcoded URLs like href="/..." instead of url_for
                hardcoded = re.findall(r'href=["\'](/[^"\'\s{}]*)["\']', content)
                for h in hardcoded:
                    if not h.startswith('/static') and not h.startswith('http'):
                        findings['hardcoded_endpoints'].append({
                            'file': rel_path,
                            'url': h
                        })
        except Exception as e:
            pass

    print("==================================================")
    print("PROJECT COMPREHENSIVE ANALYSIS RESULTS")
    print("==================================================")
    print(f"1. Legacy Query.get() instances (SQLAlchemy 2.0 Warning): {len(findings['legacy_query_get'])}")
    print(f"2. TODO/FIXME comments found: {len(findings['todo_fixme_comments'])}")
    print(f"3. Hardcoded HTML href endpoints: {len(findings['hardcoded_endpoints'])}")

    return findings

if __name__ == '__main__':
    analyze_codebase()
