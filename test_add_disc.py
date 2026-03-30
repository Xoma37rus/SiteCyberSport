from sqlalchemy import text
from models import SessionLocal, User

db = SessionLocal()
try:
    # Добавляем связи
    db.execute(text('INSERT INTO user_disciplines (user_id, discipline_id) VALUES (7, 1), (7, 2)'))
    db.commit()
    print('Added relations')
    
    # Проверяем
    result = db.execute(text('SELECT * FROM user_disciplines'))
    rows = result.fetchall()
    print(f'Rows: {len(rows)}')
    for r in rows:
        print(f'  {r}')
    
    # Проверяем через ORM
    coach = db.query(User).filter(User.id == 7).first()
    print(f'\nCoach: {coach.username}')
    print(f'Disciplines: {[d.name for d in coach.disciplines]}')
finally:
    db.close()
