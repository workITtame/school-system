"""
Database Backup Script for school_system_db (MySQL)
Phase 1 - HomeworkMarks Migration Safety
"""
import os
import sys
import json
from datetime import datetime

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from models import db
from sqlalchemy import text

def backup_database():
    app = create_app()
    backup_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../backups'))
    os.makedirs(backup_dir, exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(backup_dir, f"school_system_db_backup_{timestamp}.json")

    print("==================================================")
    print("BACKUP DATABASE START")
    print(f"Target Backup File: {backup_file}")
    print("==================================================")

    try:
        with app.app_context():
            with db.engine.connect() as conn:
                backup_data = {}
                tables = conn.execute(text("SHOW TABLES")).fetchall()
                for (table_name,) in tables:
                    rows = conn.execute(text(f"SELECT * FROM `{table_name}`")).fetchall()
                    serialized_rows = []
                    for row in rows:
                        serialized_row = {}
                        for k, v in row._mapping.items():
                            if isinstance(v, (datetime,)):
                                serialized_row[k] = v.isoformat()
                            elif hasattr(v, '__str__') and not isinstance(v, (int, float, str, bool, type(None))):
                                serialized_row[k] = str(v)
                            else:
                                serialized_row[k] = v
                        serialized_rows.append(serialized_row)
                    backup_data[table_name] = serialized_rows

                with open(backup_file, 'w', encoding='utf-8') as f:
                    json.dump(backup_data, f, ensure_ascii=False, indent=2)

                print(f"Backup created successfully: {backup_file}")
                print(f"Total Tables Backed Up: {len(backup_data)}")
                print("Backup status: SUCCESS")
                return True, backup_file
    except Exception as e:
        print(f"Backup failed — migration stopped. Error: {e}")
        return False, None

if __name__ == '__main__':
    success, filepath = backup_database()
    if not success:
        sys.exit(1)
