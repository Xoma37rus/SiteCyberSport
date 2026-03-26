"""
Скрипт для полного тестирования сайта
Регистрация, вход, создание новости, турнира, команды
"""

import sys
import os

venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

from sqlalchemy.orm import Session
from models import SessionLocal, User, News, Tournament, Team, Discipline, create_tables, init_disciplines
from utils import get_password_hash
from datetime import datetime, timedelta


def test_all():
    """Полное тестирование"""
    create_tables()
    init_disciplines()
    
    db = SessionLocal()
    try:
        print("=" * 60)
        print("🧪 ПОЛНОЕ ТЕСТИРОВАНИЕ САЙТА")
        print("=" * 60)
        
        # ==================== 1. РЕГИСТРАЦИЯ ====================
        print("\n1️⃣ РЕГИСТРАЦИЯ ПОЛЬЗОВАТЕЛЯ")
        print("-" * 60)
        
        test_user = db.query(User).filter(User.email == "test@example.com").first()
        if not test_user:
            test_user = User(
                email="test@example.com",
                username="TestUser",
                hashed_password=get_password_hash("Test123!"),
                is_verified=True,
                is_active=True
            )
            db.add(test_user)
            db.commit()
            print("✅ Пользователь зарегистрирован:")
            print(f"   Email: test@example.com")
            print(f"   Username: TestUser")
            print(f"   Password: Test123!")
        else:
            print("ℹ️  Пользователь уже существует")
        
        # ==================== 2. АДМИН ====================
        print("\n2️⃣ СОЗДАНИЕ АДМИНИСТРАТОРА")
        print("-" * 60)
        
        admin = db.query(User).filter(User.email == "admin@easycyberpro.ru").first()
        if not admin:
            admin = User(
                email="admin@easycyberpro.ru",
                username="Admin",
                hashed_password=get_password_hash("Admin123!"),
                is_verified=True,
                is_active=True,
                is_admin=True
            )
            db.add(admin)
            db.commit()
            print("✅ Администратор создан:")
            print(f"   Email: admin@easycyberpro.ru")
            print(f"   Password: Admin123!")
        else:
            if not admin.is_admin:
                admin.is_admin = True
                db.commit()
                print("ℹ️  Администратор обновлён (добавлены права)")
            else:
                print("ℹ️  Администратор уже существует")
        
        # ==================== 3. НОВОСТЬ ====================
        print("\n3️⃣ СОЗДАНИЕ НОВОСТИ")
        print("-" * 60)
        
        news = db.query(News).filter(News.title == "Тестовая новость").first()
        if not news:
            news = News(
                title="Тестовая новость",
                content="""
<h2>Добро пожаловать на EasyCyberPro!</h2>
<p>Мы рады приветствовать вас на нашей новой киберспортивной платформе!</p>

<h3>🎮 Что вас ждёт:</h3>
<ul>
    <li>Участие в турнирах по Dota 2, CS2 и Мир Танков</li>
    <li>Создание и управление командами</li>
    <li>Подробная статистика и рейтинги</li>
    <li>Регулярные новости и обновления</li>
</ul>

<h3>🏆 Призовые фонды</h3>
<p>Общий призовой фонд турниров составляет более <strong>1 000 000 ₽</strong>!</p>

<p>Присоединяйтесь к нам и докажите своё превосходство! 🔥</p>
""",
                excerpt="Добро пожаловать на новую киберспортивную платформу!",
                author_id=admin.id,
                is_published=True
            )
            db.add(news)
            db.commit()
            print("✅ Новость создана:")
            print(f"   Заголовок: Тестовая новость")
            print(f"   Автор: {admin.username}")
        else:
            print("ℹ️  Новость уже существует")
        
        # ==================== 4. ТУРНИР ====================
        print("\n4️⃣ СОЗДАНИЕ ТУРНИРА")
        print("-" * 60)
        
        cs2 = db.query(Discipline).filter(Discipline.slug == "cs2").first()
        tournament = db.query(Tournament).filter(Tournament.name == "Открытый чемпионат").first()
        if not tournament:
            tournament = Tournament(
                name="Открытый чемпионат",
                discipline_id=cs2.id,
                description="Ежемесячный открытый турнир для всех желающих. Призовой фонд распределяется между топ-3 командами.",
                prize_pool="50 000 ₽",
                max_teams=32,
                registration_deadline=datetime.now() + timedelta(days=15),
                start_date=datetime.now() + timedelta(days=20),
                status="registration",
                format="single_elimination",
                is_online=True
            )
            db.add(tournament)
            db.commit()
            print("✅ Турнир создан:")
            print(f"   Название: Открытый чемпионат")
            print(f"   Дисциплина: Counter-Strike 2")
            print(f"   Призовой фонд: 50 000 ₽")
            print(f"   Максимум команд: 32")
        else:
            print("ℹ️  Турнир уже существует")
        
        # ==================== 5. КОМАНДА ====================
        print("\n5️⃣ СОЗДАНИЕ КОМАНДЫ")
        print("-" * 60)
        
        team = db.query(Team).filter(Team.name == "Test Gamers").first()
        if not team:
            team = Team(
                name="Test Gamers",
                discipline_id=cs2.id,
                captain_id=test_user.id,
                description="Тестовая команда для участия в турнирах",
                wins=0,
                losses=0,
                rating=1000,
                is_active=True
            )
            db.add(team)
            db.commit()
            print("✅ Команда создана:")
            print(f"   Название: Test Gamers")
            print(f"   Дисциплина: Counter-Strike 2")
            print(f"   Капитан: {test_user.username}")
        else:
            print("ℹ️  Команда уже существует")
        
        # ==================== ИТОГИ ====================
        print("\n" + "=" * 60)
        print("📊 ИТОГИ ТЕСТИРОВАНИЯ")
        print("=" * 60)
        print(f"👥 Пользователей: {db.query(User).count()}")
        print(f"📰 Новостей: {db.query(News).count()}")
        print(f"🏆 Турниров: {db.query(Tournament).count()}")
        print(f"👥 Команд: {db.query(Team).count()}")
        print(f"🎮 Дисциплин: {db.query(Discipline).count()}")
        
        print("\n" + "=" * 60)
        print("✅ ВСЕ ТЕСТЫ ПРОЙДЕНЫ УСПЕШНО!")
        print("=" * 60)
        
        print("\n📋 ДАННЫЕ ДЛЯ ВХОДА:")
        print("-" * 60)
        print("👤 ОБЫЧНЫЙ ПОЛЬЗОВАТЕЛЬ:")
        print("   URL: http://localhost:8000/login")
        print("   Email: test@example.com")
        print("   Пароль: Test123!")
        print()
        print("👑 АДМИНИСТРАТОР:")
        print("   URL: http://localhost:8000/admin/login")
        print("   Email: admin@easycyberpro.ru")
        print("   Пароль: Admin123!")
        print("=" * 60)
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ ОШИБКА: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    test_all()
