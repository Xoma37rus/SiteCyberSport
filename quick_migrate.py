"""Быстрая миграция — добавление таблиц student_ratings"""
import sqlite3
from models import Base, engine
from extended_models import create_extended_tables

# 1. Добавляем steam_id_64
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('PRAGMA table_info(users)')
columns = [col[1] for col in cursor.fetchall()]
if 'steam_id_64' not in columns:
    cursor.execute('ALTER TABLE users ADD COLUMN steam_id_64 VARCHAR(20)')
    conn.commit()
    print('Added steam_id_64')
conn.close()

# 2. Создаём все расширенные таблицы
create_extended_tables()
print('All extended tables created')

# 3. Проверяем
conn = sqlite3.connect('app.db')
cursor = conn.cursor()
cursor.execute('SELECT name FROM sqlite_master WHERE type="table" ORDER BY name')
tables = [t[0] for t in cursor.fetchall()]
print(f'Tables ({len(tables)}): {", ".join(tables)}')

# Проверяем наличие student_ratings
if 'student_ratings' in tables:
    cursor.execute('PRAGMA table_info(student_ratings)')
    cols = [col[1] for col in cursor.fetchall()]
    print(f'student_ratings columns: {cols}')
if 'student_rating_changes' in tables:
    cursor.execute('PRAGMA table_info(student_rating_changes)')
    cols = [col[1] for col in cursor.fetchall()]
    print(f'student_rating_changes columns: {cols}')
conn.close()
print('Migration complete!')
