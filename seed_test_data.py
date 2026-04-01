"""
Скрипт для создания тестовых данных EasyCyberPro

Создаёт:
- Тестовых пользователей (админ, игроки, тренеры)
- Тестовые команды
- Тестовые турниры
- Тестовые рейтинги ELO
"""

import sys
from datetime import datetime, timedelta

# Добавляем путь к проекту
sys.path.insert(0, '.')

from models import (
    User, Discipline, Team, Tournament, TournamentParticipation,
    PlayerRating, CoachStudent, TrainingSession, get_db, SessionLocal
)
from utils import get_password_hash, get_or_create_rating, update_player_rating, BASE_ELO


def create_test_data():
    """Создание тестовых данных"""
    db = SessionLocal()
    
    try:
        print("🔧 Начало создания тестовых данных...")
        
        # ==================== ПОЛЬЗОВАТЕЛИ ====================
        print("\n👥 Создание пользователей...")
        
        # Проверяем существование пользователей
        existing_users = db.query(User).count()
        if existing_users > 10:
            print(f"  ⚠️ Пользователи уже существуют ({existing_users} шт.)")
            users = db.query(User).filter(User.is_admin == False).all()
        else:
            # Администратор
            admin = User(
                email="admin@easycyberpro.ru",
                username="Admin",
                hashed_password=get_password_hash("admin123"),
                is_active=True,
                is_verified=True,
                is_admin=True,
                role="admin"
            )
            db.add(admin)
            print("  ✅ Администратор: admin@easycyberpro.ru / admin123")
            
            # Тестовые игроки
            test_users_data = [
                {"email": "player1@test.com", "username": "ProGamer2026", "role": "user", "elo": 1850},
                {"email": "player2@test.com", "username": "ShadowNinja", "role": "user", "elo": 1650},
                {"email": "player3@test.com", "username": "DragonSlayer", "role": "user", "elo": 1450},
                {"email": "player4@test.com", "username": "CyberWarrior", "role": "user", "elo": 1250},
                {"email": "player5@test.com", "username": "NightHawk", "role": "user", "elo": 1050},
                {"email": "player6@test.com", "username": "StormBreaker", "role": "user", "elo": 950},
                {"email": "player7@test.com", "username": "IronFist", "role": "user", "elo": 1150},
                {"email": "player8@test.com", "username": "ThunderStrike", "role": "user", "elo": 1350},
                {"email": "player9@test.com", "username": "VenomSnake", "role": "user", "elo": 1550},
                {"email": "player10@test.com", "username": "BlazeFalcon", "role": "user", "elo": 1750},
            ]
            
            users = []
            for user_data in test_users_data:
                user = User(
                    email=user_data["email"],
                    username=user_data["username"],
                    hashed_password=get_password_hash("password123"),
                    is_active=True,
                    is_verified=True,
                    is_admin=False,
                    role=user_data["role"],
                    avatar_url=f"/static/images/avatars/default_{hash(user_data['username']) % 5 + 1}.png"
                )
                db.add(user)
                users.append(user)
                print(f"  ✅ {user_data['username']}: {user_data['email']} / password123 (ELO: {user_data['elo']})")
            
            db.commit()
            
            # Тренер
            trainer = User(
                email="coach@easycyberpro.ru",
                username="CoachMaster",
                hashed_password=get_password_hash("coach123"),
                is_active=True,
                is_verified=True,
                is_admin=False,
                role="trainer"
            )
            db.add(trainer)
            db.commit()
            print(f"  ✅ Тренер: coach@easycyberpro.ru / coach123")
        
        # ==================== РЕЙТИНГИ ====================
        print("\n📊 Создание рейтингов ELO...")
        
        disciplines = db.query(Discipline).all()
        
        for i, user in enumerate(users):
            for disc in disciplines:
                # Проверяем существование рейтинга
                existing_rating = db.query(PlayerRating).filter(
                    PlayerRating.user_id == user.id,
                    PlayerRating.discipline_id == disc.id
                ).first()
                
                if existing_rating:
                    continue  # Рейтинг уже существует
                
                # Создаём рейтинг
                rating = get_or_create_rating(db, user.id, disc.id)
                
                # Устанавливаем разный ELO для разных дисциплин
                base_elo = 1000 + (hash(f"{user.username}{disc.slug}") % 1000)
                rating.elo = max(0, base_elo)
                rating.level = get_level_by_elo(rating.elo)
                rating.games_played = 50 + (hash(user.username) % 100)
                rating.wins = int(rating.games_played * (0.4 + (hash(user.username) % 30) / 100))
                rating.losses = rating.games_played - rating.wins
                rating.peak_elo = rating.elo + (hash(user.username) % 150)
                
                db.add(rating)
        
        db.commit()
        print("  ✅ Рейтинги созданы/обновлены для всех игроков")
        
        # ==================== КОМАНДЫ ====================
        print("\n🏆 Создание команд...")
        
        existing_teams = db.query(Team).count()
        if existing_teams > 0:
            print(f"  ⚠️ Команды уже существуют ({existing_teams} шт.)")
        else:
            teams_data = [
                {"name": "CyberDragons", "discipline": "dota2", "captain": "ProGamer2026"},
                {"name": "Shadow Warriors", "discipline": "cs2", "captain": "ShadowNinja"},
                {"name": "Thunder Bolts", "discipline": "dota2", "captain": "ThunderStrike"},
                {"name": "Iron Legion", "discipline": "tanks", "captain": "IronFist"},
                {"name": "Night Hunters", "discipline": "cs2", "captain": "NightHawk"},
            ]
            
            teams = []
            for team_data in teams_data:
                captain = db.query(User).filter(User.username == team_data["captain"]).first()
                discipline = db.query(Discipline).filter(Discipline.slug == team_data["discipline"]).first()
                
                if captain and discipline:
                    team = Team(
                        name=team_data["name"],
                        discipline_id=discipline.id,
                        captain_id=captain.id,
                        description=f"Профессиональная команда по {discipline.name}",
                        rating=1000 + (hash(team_data["name"]) % 500),
                        wins=hash(team_data["name"]) % 50,
                        losses=hash(team_data["name"]) % 30,
                        is_active=True
                    )
                    db.add(team)
                    teams.append(team)
                    print(f"  ✅ Команда: {team_data['name']} ({discipline.name}) - Капитан: {captain.username}")
            
            db.commit()
        
        # ==================== ТУРНИРЫ ====================
        print("\n🎮 Создание турниров...")
        
        existing_tournaments = db.query(Tournament).count()
        if existing_tournaments > 0:
            print(f"  ⚠️ Турниры уже существуют ({existing_tournaments} шт.)")
        else:
            tournaments_data = [
                {
                    "name": "EasyCyberPro Championship 2026",
                    "discipline": "dota2",
                    "status": "registration",
                    "prize_pool": "100 000 руб.",
                    "max_teams": 16,
                    "start_date": datetime.utcnow() + timedelta(days=30),
                    "format": "single_elimination"
                },
                {
                    "name": "CS2 Spring Cup",
                    "discipline": "cs2",
                    "status": "active",
                    "prize_pool": "50 000 руб.",
                    "max_teams": 8,
                    "start_date": datetime.utcnow() - timedelta(days=5),
                    "format": "double_elimination"
                },
                {
                    "name": "Танковый Биатлон",
                    "discipline": "tanks",
                    "status": "upcoming",
                    "prize_pool": "30 000 руб.",
                    "max_teams": 12,
                    "start_date": datetime.utcnow() + timedelta(days=15),
                    "format": "round_robin"
                },
                {
                    "name": "Winter Tournament 2025",
                    "discipline": "dota2",
                    "status": "completed",
                    "prize_pool": "75 000 руб.",
                    "max_teams": 8,
                    "start_date": datetime.utcnow() - timedelta(days=60),
                    "format": "single_elimination"
                }
            ]
            
            tournaments = []
            for tour_data in tournaments_data:
                discipline = db.query(Discipline).filter(Discipline.slug == tour_data["discipline"]).first()
                
                if discipline:
                    tournament = Tournament(
                        name=tour_data["name"],
                        discipline_id=discipline.id,
                        description=f"Турнир по {discipline.name} для всех желающих",
                        prize_pool=tour_data["prize_pool"],
                        max_teams=tour_data["max_teams"],
                        registration_deadline=tour_data["start_date"] - timedelta(days=7),
                        start_date=tour_data["start_date"],
                        status=tour_data["status"],
                        format=tour_data["format"],
                        is_online=True
                    )
                    db.add(tournament)
                    tournaments.append(tournament)
                    print(f"  ✅ Турнир: {tour_data['name']} ({discipline.name}) - Статус: {tour_data['status']}")
            
            db.commit()
        
        # ==================== УЧЕНИКИ ТРЕНЕРА ====================
        print("\n🎓 Добавление учеников тренеру...")
        
        # Добавляем нескольких игроков как учеников тренера
        for i in range(3):
            coach_student = CoachStudent(
                coach_id=trainer.id,
                student_id=users[i].id,
                notes=f"Перспективный игрок, уровень {get_level_by_elo(int(test_users_data[i]['elo']))}"
            )
            db.add(coach_student)
        
        db.commit()
        print(f"  ✅ Добавлено 3 ученика тренеру {trainer.username}")
        
        # ==================== ТРЕНИРОВКИ ====================
        print("\n📅 Создание тренировок...")
        
        dota_discipline = db.query(Discipline).filter(Discipline.slug == "dota2").first()
        
        sessions_data = [
            {
                "title": "Индивидуальная тренировка: Last hitting",
                "scheduled_at": datetime.utcnow() + timedelta(days=2, hours=10),
                "duration": 90
            },
            {
                "title": "Командная практика: Draft phase",
                "scheduled_at": datetime.utcnow() + timedelta(days=3, hours=18),
                "duration": 120
            },
            {
                "title": "Разбор реплеев",
                "scheduled_at": datetime.utcnow() + timedelta(days=5, hours=15),
                "duration": 60
            }
        ]
        
        for session_data in sessions_data:
            session = TrainingSession(
                coach_id=trainer.id,
                discipline_id=dota_discipline.id if dota_discipline else None,
                title=session_data["title"],
                description="Плановая тренировка с разбором ошибок",
                scheduled_at=session_data["scheduled_at"],
                duration_minutes=session_data["duration"],
                status="scheduled"
            )
            db.add(session)
        
        db.commit()
        print(f"  ✅ Создано {len(sessions_data)} тренировок")
        
        # ==================== ИТОГИ ====================
        print("\n" + "="*50)
        print("✅ ТЕСТОВЫЕ ДАННЫЕ СОЗДАНЫ УСПЕШНО!")
        print("="*50)
        print(f"\n📊 Итого создано:")
        print(f"  • Пользователей: {len(users) + 2} (1 админ, 1 тренер, {len(users)} игроков)")
        print(f"  • Команд: {len(teams)}")
        print(f"  • Турниров: {len(tournaments)}")
        print(f"  • Рейтингов: {len(users) * len(disciplines)}")
        print(f"  • Учеников тренера: 3")
        print(f"  • Тренировок: {len(sessions_data)}")
        
        print("\n🔐 Учётные данные для входа:")
        print("  👨‍💼 Администратор:")
        print("     Email: admin@easycyberpro.ru")
        print("     Пароль: admin123")
        print("  🎮 Игроки:")
        print("     Email: player1@test.com ... player10@test.com")
        print("     Пароль: password123")
        print("  🎓 Тренер:")
        print("     Email: coach@easycyberpro.ru")
        print("     Пароль: coach123")
        
        print("\n🌐 Сайт доступен: http://localhost:8000")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        raise
    finally:
        db.close()


def get_level_by_elo(elo: int) -> int:
    """Определить уровень по ELO"""
    ELO_LEVELS = {
        1: (0, 199), 2: (200, 399), 3: (400, 599), 4: (600, 799), 5: (800, 999),
        6: (1000, 1199), 7: (1200, 1399), 8: (1400, 1699), 9: (1700, 1999), 10: (2000, float('inf'))
    }
    for level, (min_elo, max_elo) in ELO_LEVELS.items():
        if min_elo <= elo <= max_elo:
            return level
    return 1


if __name__ == "__main__":
    create_test_data()
