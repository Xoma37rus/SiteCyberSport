from sqlalchemy import text
from models import SessionLocal, user_disciplines, engine, Base, User, Discipline

# Создаём все таблицы
Base.metadata.create_all(bind=engine)
print('Tables created')

db = SessionLocal()
try:
    # Проверяем таблицу
    result = db.execute(text('SELECT name FROM sqlite_master WHERE type="table" AND name="user_disciplines"'))
    row = result.fetchone()
    print(f'user_disciplines exists: {row is not None}')
    
    # Проверяем связи
    result = db.execute(text('SELECT * FROM user_disciplines'))
    rows = result.fetchall()
    print(f'Rows in user_disciplines: {len(rows)}')
    for r in rows:
        print(f'  {r}')
    
    # Проверяем тренера
    coach = db.query(User).filter(User.id == 7).first()
    if coach:
        print(f'\nCoach: {coach.username}')
        print(f'Disciplines (lazy): {len(coach.disciplines)}')
        
        # Пробуем загрузить явно
        from sqlalchemy.orm import selectinload
        coach_loaded = db.query(User).options(selectinload(User.disciplines)).filter(User.id == 7).first()
        print(f'Disciplines (selectinload): {[d.name for d in coach_loaded.disciplines]}')
finally:
    db.close()

print('\nDone')
