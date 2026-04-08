"""
Миграция БД - добавление новых колонок и таблиц
"""
import sqlite3
import sys

conn = sqlite3.connect('app.db')
cursor = conn.cursor()

# 1. Добавляем steam_id_64 в users
cursor.execute('PRAGMA table_info(users)')
columns = [col[1] for col in cursor.fetchall()]
print(f'Columns in users: {columns}')
if 'steam_id_64' not in columns:
    cursor.execute('ALTER TABLE users ADD COLUMN steam_id_64 VARCHAR(20)')
    conn.commit()
    print('OK: Added steam_id_64')
else:
    print('OK: steam_id_64 already exists')

# 2. Создаём все новые таблицы через SQLAlchemy
from models import Base, engine
from extended_models import (
    MatchReport, Achievement, UserAchievement,
    Ladder, LadderParticipant, LadderMatch,
    Subscription, MatchHistoryItem, SteamUser,
    create_extended_tables, init_default_achievements
)

print('Creating extended tables...')
try:
    create_extended_tables()
    print('OK: Extended tables created')
except Exception as e:
    print(f'Extended tables: {e}')

# 3. Инициализация достижений
try:
    init_default_achievements()
    print('OK: Achievements initialized')
except Exception as e:
    print(f'Achievements: {e}')

# Проверяем таблицы
cursor.execute('SELECT name FROM sqlite_master WHERE type="table"')
tables = sorted([t[0] for t in cursor.fetchall()])
print(f'\nAll tables ({len(tables)}):')
for t in tables:
    print(f'  - {t}')

conn.close()
print('\nMigration complete!')
