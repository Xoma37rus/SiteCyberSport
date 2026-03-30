from main import app
from fastapi.testclient import TestClient
from models import SessionLocal, User, Discipline

client = TestClient(app)

print("=== ТЕСТ ВЫБОРА ДИСЦИПЛИН ===\n")

# Вход как тренер
login_data = {'email': 'coach@test.com', 'password': 'coach123'}
r = client.post('/login', data=login_data, follow_redirects=False)
print(f"1. Вход тренера: {r.status_code}")

if r.status_code == 303:
    # Проверка страницы профиля
    r = client.get('/profile')
    print(f"2. GET /profile: {r.status_code}")
    
    if r.status_code == 200:
        has_disciplines = 'discipline_ids' in r.text
        print(f"3. Выбор дисциплин на странице: {'✓' if has_disciplines else '✗'}")
        
        has_dota = 'Dota 2' in r.text
        has_cs2 = 'Counter-Strike' in r.text
        print(f"4. Дисциплины отображаются: {'✓' if has_dota or has_cs2 else '✗'}")
    
    # Тест обновления профиля с дисциплинами
    r = client.post('/profile/update', data={
        'username': 'coach_test',
        'bio': '',
        'country': '',
        'city': '',
        'social_vk': '',
        'social_telegram': '',
        'social_discord': '',
        'discipline_ids': ['1', '2']
    }, follow_redirects=False)
    print(f"5. POST /profile/update с дисциплинами: {r.status_code}")
    
    # Проверяем в БД
    db = SessionLocal()
    try:
        coach = db.query(User).filter(User.email == 'coach@test.com').first()
        if coach:
            disc_count = len(coach.disciplines)
            disc_names = [d.name for d in coach.disciplines]
            print(f"6. Дисциплин у тренера: {disc_count}")
            print(f"   Список: {disc_names}")
    finally:
        db.close()

print("\n=== ТЕСТ ЗАВЕРШЁН ===")
