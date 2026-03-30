"""
Комплексное тестирование платформы EasyCyberPro
"""
import sys
sys.path.insert(0, '.')

from main import app
from fastapi.testclient import TestClient
from models import SessionLocal, User, Discipline, CoachStudent, TrainingSession
from utils import get_password_hash

client = TestClient(app)

def setup_test_data():
    """Создание тестовых данных"""
    db = SessionLocal()
    try:
        # Создаём тестового админа
        admin = db.query(User).filter(User.email == "admin@test.com").first()
        if not admin:
            admin = User(
                email="admin@test.com",
                username="admin_test",
                hashed_password=get_password_hash("admin123"),
                is_admin=True,
                is_verified=True,
                is_active=True,
                role="admin"
            )
            db.add(admin)
        
        # Создаём тестового тренера
        coach = db.query(User).filter(User.email == "coach@test.com").first()
        if not coach:
            coach = User(
                email="coach@test.com",
                username="coach_test",
                hashed_password=get_password_hash("coach123"),
                is_admin=False,
                is_verified=True,
                is_active=True,
                role="trainer"
            )
            db.add(coach)
        
        # Создаём тестового ученика
        student = db.query(User).filter(User.email == "student@test.com").first()
        if not student:
            student = User(
                email="student@test.com",
                username="student_test",
                hashed_password=get_password_hash("student123"),
                is_admin=False,
                is_verified=True,
                is_active=True,
                role="student"
            )
            db.add(student)
        
        db.commit()
        
        # Создаём связь тренер-ученик
        existing = db.query(CoachStudent).filter(
            CoachStudent.coach_id == coach.id,
            CoachStudent.student_id == student.id
        ).first()
        if not existing:
            relation = CoachStudent(
                coach_id=coach.id,
                student_id=student.id,
                notes="Тестовый ученик"
            )
            db.add(relation)
            db.commit()
        
        print(f"✓ Тестовые данные созданы")
        print(f"  Admin: admin@test.com / admin123 (id={admin.id})")
        print(f"  Coach: coach@test.com / coach123 (id={coach.id})")
        print(f"  Student: student@test.com / student123 (id={student.id})")
        
        return admin, coach, student
    finally:
        db.close()


def test_public_routes():
    """Тест публичных маршрутов"""
    print("\n=== Публичные маршруты ===")
    
    routes = [
        ('/', 'Главная'),
        ('/login', 'Вход'),
        ('/register', 'Регистрация'),
        ('/about', 'О проекте'),
        ('/news', 'Новости'),
        ('/tournaments', 'Турниры'),
        ('/health', 'Health check'),
    ]
    
    for path, name in routes:
        try:
            r = client.get(path)
            status = "✓" if r.status_code == 200 else "✗"
            print(f"{status} {name} ({path}): {r.status_code}")
        except Exception as e:
            print(f"✗ {name} ({path}): ERROR - {e}")


def test_auth_routes():
    """Тест маршрутов требующих авторизацию"""
    print("\n=== Маршруты требующие авторизацию ===")
    
    # Сначала логинимся
    r = client.post('/login', data={
        'email': 'coach@test.com',
        'password': 'coach123'
    }, follow_redirects=False)
    
    routes = [
        ('/dashboard', 'Дашборд'),
        ('/profile', 'Профиль'),
        ('/coach/dashboard', 'Кабинет тренера'),
        ('/coach/students', 'Ученики тренера'),
        ('/coach/sessions', 'Тренировки тренера'),
    ]
    
    for path, name in routes:
        try:
            r = client.get(path)
            status = "✓" if r.status_code == 200 else "✗"
            print(f"{status} {name} ({path}): {r.status_code}")
        except Exception as e:
            print(f"✗ {name} ({path}): ERROR - {e}")


def test_admin_routes():
    """Тест админских маршрутов"""
    print("\n=== Админские маршруты ===")
    
    routes = [
        ('/admin/login', 'Вход админа'),
        ('/admin', 'Админ панель'),
        ('/admin/users', 'Пользователи'),
        ('/admin/coaches', 'Тренеры'),
        ('/admin/news', 'Новости админ'),
        ('/admin/teams', 'Команды админ'),
        ('/admin/tournaments', 'Турниры админ'),
    ]
    
    for path, name in routes:
        try:
            r = client.get(path)
            # Для админки 303 redirect на login это нормально
            status = "✓" if r.status_code in [200, 303] else "✗"
            print(f"{status} {name} ({path}): {r.status_code}")
        except Exception as e:
            print(f"✗ {name} ({path}): ERROR - {e}")


def test_templates():
    """Проверка существования шаблонов"""
    print("\n=== Проверка шаблонов ===")
    import os
    
    templates_dir = 'templates'
    required_templates = [
        'index.html',
        'login.html',
        'register.html',
        'dashboard.html',
        'profile.html',
        'admin/dashboard.html',
        'admin/login.html',
        'admin/users.html',
        'admin/coaches_list.html',
        'admin/create_coach.html',
        'admin/coach_students.html',
        'coach/dashboard.html',
        'coach/students.html',
        'coach/add_student.html',
        'coach/student_detail.html',
        'coach/sessions.html',
        'coach/create_session.html',
        'coach/session_detail.html',
    ]
    
    for template in required_templates:
        path = os.path.join(templates_dir, *template.split('/'))
        exists = os.path.exists(path)
        status = "✓" if exists else "✗"
        print(f"{status} {template}: {'exists' if exists else 'MISSING'}")


def test_models():
    """Проверка моделей данных"""
    print("\n=== Проверка моделей ===")
    db = SessionLocal()
    try:
        # Проверка таблиц
        tables = ['users', 'news', 'disciplines', 'teams', 'tournaments', 
                  'coach_students', 'training_sessions', 'training_attendance']
        
        for table in tables:
            try:
                result = db.execute(f"SELECT COUNT(*) FROM {table}")
                count = result.scalar()
                print(f"✓ Таблица {table}: {count} записей")
            except Exception as e:
                print(f"✗ Таблица {table}: ERROR - {e}")
    finally:
        db.close()


def test_api_endpoints():
    """Тест API endpoints"""
    print("\n=== API Endpoints ===")
    
    endpoints = [
        ('GET', '/api/news'),
        ('GET', '/api/tournaments'),
        ('GET', '/api/disciplines'),
    ]
    
    for method, path in endpoints:
        try:
            if method == 'GET':
                r = client.get(path)
            status = "✓" if r.status_code == 200 else "✗"
            print(f"{status} {method} {path}: {r.status_code}")
        except Exception as e:
            print(f"✗ {method} {path}: ERROR - {e}")


if __name__ == '__main__':
    print("=" * 60)
    print("КОМПЛЕКСНОЕ ТЕСТИРОВАНИЕ ПЛАТФОРМЫ EasyCyberPro")
    print("=" * 60)
    
    # Инициализация
    print("\n[1/7] Инициализация тестовых данных...")
    setup_test_data()
    
    # Тесты
    print("\n[2/7] Проверка моделей данных...")
    test_models()
    
    print("\n[3/7] Проверка шаблонов...")
    test_templates()
    
    print("\n[4/7] Тест публичных маршрутов...")
    test_public_routes()
    
    print("\n[5/7] Тест маршрутов авторизации...")
    test_auth_routes()
    
    print("\n[6/7] Тест админских маршрутов...")
    test_admin_routes()
    
    print("\n[7/7] Тест API endpoints...")
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("ТЕСТИРОВАНИЕ ЗАВЕРШЕНО")
    print("=" * 60)
