"""
Глубокое тестирование функционала платформы
"""
import sys
sys.path.insert(0, '.')

from main import app
from fastapi.testclient import TestClient
from models import SessionLocal, User, CoachStudent, TrainingSession, Discipline
from utils import get_password_hash
import json

client = TestClient(app)

def get_csrf_token(response):
    """Извлечение CSRF токена из cookie"""
    for cookie in response.cookies:
        if cookie.name == 'csrf_token':
            return cookie.value
    return None

def get_flash_message(response):
    """Извлечение flash сообщения из cookie"""
    for cookie in response.cookies:
        if cookie.name == 'flash_message':
            return cookie.value
    return None

print("=" * 70)
print("ГЛУБОКОЕ ТЕСТИРОВАНИЕ ФУНКЦИОНАЛА")
print("=" * 70)

# ==================== ТЕСТ 1: Регистрация и вход ====================

print("\n[TEST 1] Регистрация и вход пользователя...")

# Регистрация нового пользователя
register_data = {
    'username': 'test_user_123',
    'email': 'test_user_123@example.com',
    'password': 'testpass123'
}

r = client.post('/register', data=register_data, follow_redirects=False)
print(f"  Регистрация: {r.status_code}")

# Вход
login_data = {
    'email': 'test_user_123@example.com',
    'password': 'testpass123'
}

r = client.post('/login', data=login_data, follow_redirects=False)
print(f"  Вход: {r.status_code} (redirect на /dashboard)")

if r.status_code == 303:
    # Проверяем cookie
    has_token = any(c.name == 'access_token' for c in r.cookies)
    print(f"  Access token в cookie: {'✓' if has_token else '✗'}")

# ==================== ТЕСТ 2: Создание тренера через админку ====================

print("\n[TEST 2] Создание тренера через админку...")

# Сначала входим как админ
admin_login = {
    'email': 'admin@test.com',
    'password': 'admin123'
}

r = client.post('/admin/login', data=admin_login, follow_redirects=False)
print(f"  Вход админа: {r.status_code}")

if r.status_code == 303:
    # Получаем CSRF токен
    csrf_token = get_csrf_token(r)
    
    # Создание тренера
    coach_data = {
        'username': 'new_coach_test',
        'email': 'new_coach_test@example.com',
        'password': 'coachpass123',
        'is_active': 'true',
        'is_verified': 'true',
        'csrf_token': csrf_token or ''
    }
    
    r = client.post('/admin/coaches/create', data=coach_data, follow_redirects=False)
    print(f"  Создание тренера: {r.status_code}")
    
    if r.status_code == 303:
        flash = get_flash_message(r)
        if flash:
            print(f"  Flash сообщение: {flash[:50]}...")

# ==================== ТЕСТ 3: Личный кабинет тренера ====================

print("\n[TEST 3] Личный кабинет тренера...")

# Вход как тренер
coach_login = {
    'email': 'coach@test.com',
    'password': 'coach123'
}

# Создаём новый клиент для чистых cookie
coach_client = TestClient(app)
r = coach_client.post('/login', data=coach_login, follow_redirects=False)
print(f"  Вход тренера: {r.status_code}")

if r.status_code == 303:
    # Доступ к dashboard тренера
    r = coach_client.get('/coach/dashboard')
    print(f"  GET /coach/dashboard: {r.status_code}")
    
    # Доступ к ученикам
    r = coach_client.get('/coach/students')
    print(f"  GET /coach/students: {r.status_code}")
    
    # Доступ к добавлению ученика
    r = coach_client.get('/coach/students/add')
    print(f"  GET /coach/students/add: {r.status_code}")
    
    # Доступ к тренировкам
    r = coach_client.get('/coach/sessions')
    print(f"  GET /coach/sessions: {r.status_code}")
    
    # Создание тренировки (страница)
    r = coach_client.get('/coach/sessions/create')
    print(f"  GET /coach/sessions/create: {r.status_code}")

# ==================== ТЕСТ 4: Добавление ученика тренеру ====================

print("\n[TEST 4] Добавление ученика тренеру...")

db = SessionLocal()
try:
    coach = db.query(User).filter(User.email == 'coach@test.com').first()
    student = db.query(User).filter(User.email == 'student@test.com').first()
    
    if coach and student:
        # Проверяем существующую связь
        existing = db.query(CoachStudent).filter(
            CoachStudent.coach_id == coach.id,
            CoachStudent.student_id == student.id
        ).first()
        
        if not existing:
            # Создаём связь
            relation = CoachStudent(
                coach_id=coach.id,
                student_id=student.id,
                notes="Тестовая связь"
            )
            db.add(relation)
            db.commit()
            print(f"  ✓ Связь тренер-ученик создана")
        else:
            print(f"  ✓ Связь тренер-ученик уже существует")
        
        # Проверка через API
        r = coach_client.get('/coach/students')
        if r.status_code == 200:
            print(f"  ✓ Страница учеников доступна")
            if student.username in r.text:
                print(f"  ✓ Ученик {student.username} отображается в списке")
            else:
                print(f"  ✗ Ученик {student.username} НЕ отображается")
finally:
    db.close()

# ==================== ТЕСТ 5: Создание тренировки ====================

print("\n[TEST 5] Создание тренировки...")

db = SessionLocal()
try:
    coach = db.query(User).filter(User.email == 'coach@test.com').first()
    discipline = db.query(Discipline).first()
    
    if coach:
        # Создаём тестовую тренировку
        session = TrainingSession(
            coach_id=coach.id,
            discipline_id=discipline.id if discipline else None,
            title="Тестовая тренировка",
            description="Описание тестовой тренировки",
            status="scheduled"
        )
        db.add(session)
        db.commit()
        print(f"  ✓ Тренировка создана (id={session.id})")
        
        # Проверка через API
        r = coach_client.get('/coach/sessions')
        if r.status_code == 200 and "Тестовая тренировка" in r.text:
            print(f"  ✓ Тренировка отображается в списке")
finally:
    db.close()

# ==================== ТЕСТ 6: Админка - управление тренерами ====================

print("\n[TEST 6] Админка - управление тренерами...")

admin_client = TestClient(app)
admin_login = {
    'email': 'admin@test.com',
    'password': 'admin123'
}

r = admin_client.post('/admin/login', data=admin_login, follow_redirects=False)
if r.status_code == 303:
    # Доступ к списку тренеров
    r = admin_client.get('/admin/coaches')
    print(f"  GET /admin/coaches: {r.status_code}")
    
    if r.status_code == 200:
        if 'coach_test' in r.text or 'new_coach_test' in r.text:
            print(f"  ✓ Тренеры отображаются в списке")
        else:
            print(f"  ? Тренеры не найдены в списке")
    
    # Доступ к созданию тренера
    r = admin_client.get('/admin/coaches/create')
    print(f"  GET /admin/coaches/create: {r.status_code}")

# ==================== ТЕСТ 7: Проверка прав доступа ====================

print("\n[TEST 7] Проверка прав доступа...")

# Анонимный пользователь пытается доступ к coach dashboard
anon_client = TestClient(app)
r = anon_client.get('/coach/dashboard', follow_redirects=False)
print(f"  Аноним /coach/dashboard: {r.status_code} (ожидался 307/403)")

# Анонимный доступ к админке
r = anon_client.get('/admin', follow_redirects=False)
print(f"  Аноним /admin: {r.status_code} (ожидался 307)")

# Студент пытается доступ к coach dashboard
student_client = TestClient(app)
student_login = {
    'email': 'student@test.com',
    'password': 'student123'
}
r = student_client.post('/login', data=student_login, follow_redirects=False)
if r.status_code == 303:
    r = student_client.get('/coach/dashboard', follow_redirects=False)
    print(f"  Студент /coach/dashboard: {r.status_code} (ожидался 403)")

# ==================== ИТОГИ ====================

print("\n" + "=" * 70)
print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
print("=" * 70)
