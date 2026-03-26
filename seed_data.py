"""
Скрипт для создания тестовых данных (команды и турниры)
Запустите: python seed_data.py
"""

import sys
import os

# Добавляем путь к venv если скрипт запущен без активации
venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

from sqlalchemy.orm import Session
from models import SessionLocal, Discipline, Team, Tournament, TeamMember, create_tables, init_disciplines
from datetime import datetime, timedelta


def seed_data():
    """Создание тестовых данных"""
    create_tables()
    init_disciplines()
    
    db = SessionLocal()
    try:
        print("=== Создание тестовых данных ===\n")
        
        # Получаем дисциплины
        dota2 = db.query(Discipline).filter(Discipline.slug == "dota2").first()
        cs2 = db.query(Discipline).filter(Discipline.slug == "cs2").first()
        tanks = db.query(Discipline).filter(Discipline.slug == "tanks").first()
        
        # ==================== КОМАНДЫ ====================
        print("📦 Создание команд...")
        
        # Dota 2 команды
        dota2_teams = [
            {"name": "Ancient Defenders", "wins": 45, "losses": 12, "rating": 2850},
            {"name": "Radiant Kings", "wins": 38, "losses": 15, "rating": 2720},
            {"name": "Dire Legends", "wins": 32, "losses": 18, "rating": 2580},
            {"name": "Aegis Warriors", "wins": 28, "losses": 20, "rating": 2450},
            {"name": "Roshan Slayers", "wins": 25, "losses": 22, "rating": 2320},
        ]
        
        for team_data in dota2_teams:
            existing = db.query(Team).filter(Team.name == team_data["name"]).first()
            if not existing:
                team = Team(
                    name=team_data["name"],
                    discipline_id=dota2.id,
                    wins=team_data["wins"],
                    losses=team_data["losses"],
                    rating=team_data["rating"],
                    description=f"Профессиональная команда по Dota 2",
                    is_active=True
                )
                db.add(team)
                print(f"  ✓ Создана команда: {team.name}")
        
        # CS2 команды
        cs2_teams = [
            {"name": "Team Alpha", "wins": 52, "losses": 8, "rating": 3100},
            {"name": "Cyber Warriors", "wins": 45, "losses": 12, "rating": 2950},
            {"name": "Digital Storm", "wins": 40, "losses": 15, "rating": 2800},
            {"name": "Headshot Elite", "wins": 35, "losses": 18, "rating": 2650},
            {"name": "Bomb Defusers", "wins": 30, "losses": 22, "rating": 2500},
        ]
        
        for team_data in cs2_teams:
            existing = db.query(Team).filter(Team.name == team_data["name"]).first()
            if not existing:
                team = Team(
                    name=team_data["name"],
                    discipline_id=cs2.id,
                    wins=team_data["wins"],
                    losses=team_data["losses"],
                    rating=team_data["rating"],
                    description=f"Профессиональная команда по Counter-Strike 2",
                    is_active=True
                )
                db.add(team)
                print(f"  ✓ Создана команда: {team.name}")
        
        # Tanks команды
        tanks_teams = [
            {"name": "Steel Titans", "wins": 68, "losses": 15, "rating": 3200},
            {"name": "Armor Breakers", "wins": 55, "losses": 20, "rating": 2980},
            {"name": "Iron Fortress", "wins": 48, "losses": 25, "rating": 2750},
            {"name": "Blitz Warriors", "wins": 42, "losses": 28, "rating": 2600},
            {"name": "Tank Commanders", "wins": 38, "losses": 30, "rating": 2450},
        ]
        
        for team_data in tanks_teams:
            existing = db.query(Team).filter(Team.name == team_data["name"]).first()
            if not existing:
                team = Team(
                    name=team_data["name"],
                    discipline_id=tanks.id,
                    wins=team_data["wins"],
                    losses=team_data["losses"],
                    rating=team_data["rating"],
                    description=f"Профессиональная команда по Мир Танков",
                    is_active=True
                )
                db.add(team)
                print(f"  ✓ Создана команда: {team.name}")
        
        db.commit()
        print(f"\n✅ Всего создано команд: {len(dota2_teams) + len(cs2_teams) + len(tanks_teams)}")
        
        # ==================== ТУРНИРЫ ====================
        print("\n📦 Создание турниров...")
        
        tournaments = [
            {
                "name": "Весенний Кубок 2026",
                "discipline": cs2,
                "prize_pool": "100 000 ₽",
                "max_teams": 16,
                "start_date": datetime.now() + timedelta(days=10),
                "registration_deadline": datetime.now() + timedelta(days=5),
                "status": "registration",
                "format": "single_elimination",
                "is_online": True,
                "description": "Ежегодный турнир по Counter-Strike 2. Призовой фонд 100 000 рублей."
            },
            {
                "name": "Battle of Ancients",
                "discipline": dota2,
                "prize_pool": "250 000 ₽",
                "max_teams": 16,
                "start_date": datetime.now() + timedelta(days=20),
                "registration_deadline": datetime.now() + timedelta(days=12),
                "status": "registration",
                "format": "double_elimination",
                "is_online": True,
                "description": "Крупнейший турнир по Dota 2 этой весны. Двойная сетка плей-офф."
            },
            {
                "name": "Steel Thunder",
                "discipline": tanks,
                "prize_pool": "150 000 ₽",
                "max_teams": 8,
                "start_date": datetime.now() + timedelta(days=30),
                "registration_deadline": datetime.now() + timedelta(days=20),
                "status": "upcoming",
                "format": "round_robin",
                "is_online": False,
                "description": "Оффлайн турнир по Миру Танков. Финал состоится в Москве."
            },
            {
                "name": "CS2 Pro League",
                "discipline": cs2,
                "prize_pool": "500 000 ₽",
                "max_teams": 12,
                "start_date": datetime.now() + timedelta(days=45),
                "registration_deadline": datetime.now() + timedelta(days=30),
                "status": "upcoming",
                "format": "swiss",
                "is_online": True,
                "description": "Профессиональная лига Counter-Strike 2. Швейцарская система."
            },
        ]
        
        for tour_data in tournaments:
            existing = db.query(Tournament).filter(Tournament.name == tour_data["name"]).first()
            if not existing:
                tournament = Tournament(
                    name=tour_data["name"],
                    discipline_id=tour_data["discipline"].id,
                    prize_pool=tour_data["prize_pool"],
                    max_teams=tour_data["max_teams"],
                    start_date=tour_data["start_date"],
                    registration_deadline=tour_data["registration_deadline"],
                    status=tour_data["status"],
                    format=tour_data["format"],
                    is_online=tour_data["is_online"],
                    description=tour_data["description"]
                )
                db.add(tournament)
                print(f"  ✓ Создан турнир: {tournament.name}")
        
        db.commit()
        print(f"\n✅ Всего создано турниров: {len(tournaments)}")
        
        print("\n=== Готово! ===")
        print(f"📊 Дисциплин: {db.query(Discipline).count()}")
        print(f"👥 Команд: {db.query(Team).count()}")
        print(f"🏆 Турниров: {db.query(Tournament).count()}")
        
    except Exception as e:
        db.rollback()
        print(f"\n❌ Ошибка: {e}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_data()
