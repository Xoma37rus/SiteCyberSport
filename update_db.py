"""
Скрипт для обновления базы данных после добавления новых полей в User
Запустите: python update_db.py
"""

import sys
import os

venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

from sqlalchemy import inspect, text
from models import SessionLocal, engine, Base

def update_database():
    """Добавление новых колонок в таблицу users через ALTER TABLE"""
    
    db = SessionLocal()
    try:
        # Проверяем существующие колонки
        inspector = inspect(engine)
        columns = [col['name'] for col in inspector.get_columns('users')]
        
        # Новые колонки которые нужно добавить с типами и значениями по умолчанию
        new_columns = {
            'avatar_url': 'VARCHAR(500)',
            'bio': 'TEXT',
            'date_of_birth': 'DATETIME',
            'country': 'VARCHAR(100)',
            'city': 'VARCHAR(100)',
            'social_vk': 'VARCHAR(200)',
            'social_telegram': 'VARCHAR(100)',
            'social_discord': 'VARCHAR(100)',
            'notify_email_tournaments': 'BOOLEAN DEFAULT 1',
            'notify_email_news': 'BOOLEAN DEFAULT 0',
            'is_profile_public': 'BOOLEAN DEFAULT 1',
            'total_matches': 'INTEGER DEFAULT 0',
            'total_wins': 'INTEGER DEFAULT 0',
            'total_losses': 'INTEGER DEFAULT 0'
        }
        
        added = []
        for col_name, col_type in new_columns.items():
            if col_name not in columns:
                print(f"➕ Добавляем колонку: {col_name} ({col_type})")
                try:
                    db.execute(text(f"ALTER TABLE users ADD COLUMN {col_name} {col_type}"))
                    db.commit()
                    added.append(col_name)
                    print(f"   ✓ Добавлено")
                except Exception as e:
                    print(f"   ⚠️ Ошибка: {e}")
            else:
                print(f"✓ Колонка {col_name} уже существует")
        
        if added:
            print(f"\n📊 Обновление завершено! Добавлено колонок: {len(added)}")
        else:
            print("\n✅ Все колонки уже существуют. Обновление не требуется.")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    update_database()
