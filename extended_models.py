"""
Модели для расширенной функциональности:
- MatchReport: Репорты матчей (античит/оспаривание)
- Achievement: Достижения и награды
- UserAchievement: Связь пользователь-достижение
- Ladder: Ладдеры (ежедневные соревнования)
- LadderParticipant: Участники ладдера
- Subscription: Подписки пользователей
- MatchHistoryItem: Детальная история матчей
- SteamUser: Привязка Steam аккаунта
"""
from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, UniqueConstraint, Enum as SAEnum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from models import Base, engine, SessionLocal
import enum


# ==================== АНТИЧИТ / РЕПОРТЫ ====================

class ReportType(str, enum.Enum):
    CHEAT = "cheat"              # Подозрение на читы
    THROW = "throw"              # Слив матча
    HARASSMENT = "harassment"    # Оскорбления
    BUG = "bug"                  # Использование бага
    OTHER = "other"              # Другое


class ReportStatus(str, enum.Enum):
    PENDING = "pending"          # На рассмотрении
    INVESTIGATING = "investigating"  # Расследуется
    RESOLVED = "resolved"        # Решено
    DISMISSED = "dismissed"      # Отклонено


class MatchReport(Base):
    """Жалоба на матч или игрока"""
    __tablename__ = "match_reports"

    id = Column(Integer, primary_key=True, index=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    reported_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=True, index=True)

    report_type = Column(SAEnum(ReportType), nullable=False, index=True)
    description = Column(Text, nullable=False)
    evidence_urls = Column(Text, nullable=True)  # JSON со ссылками на скриншоты
    status = Column(SAEnum(ReportStatus), default=ReportStatus.PENDING, index=True)

    admin_notes = Column(Text, nullable=True)  # Заметки администратора
    resolution = Column(Text, nullable=True)   # Решение

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    reporter = relationship("User", foreign_keys=[reporter_id])
    reported_user = relationship("User", foreign_keys=[reported_user_id])
    match = relationship("Match")
    tournament = relationship("Tournament")


# ==================== ДОСТИЖЕНИЯ ====================

class Achievement(Base):
    """Достижение/награда"""
    __tablename__ = "achievements"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    icon_url = Column(String(500), nullable=True)
    category = Column(String(50), default="general", index=True)  # general, tournament, rating, social

    # Условия получения
    condition_type = Column(String(50), nullable=True)  # wins, elo, games, tournaments, streak
    condition_value = Column(Integer, nullable=True)  # порог

    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user_achievements = relationship("UserAchievement", back_populates="achievement")

    def __repr__(self):
        return f"<Achievement(id={self.id}, name='{self.name}')>"


class UserAchievement(Base):
    """Полученное пользователем достижение"""
    __tablename__ = "user_achievements"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    achievement_id = Column(Integer, ForeignKey("achievements.id"), nullable=False, index=True)

    unlocked_at = Column(DateTime, default=datetime.utcnow, index=True)
    progress = Column(Integer, default=0)  # Текущий прогресс (если ещё не получено)
    is_unlocked = Column(Boolean, default=True, index=True)

    user = relationship("User", backref="user_achievements")
    achievement = relationship("Achievement", back_populates="user_achievements")

    __table_args__ = (
        UniqueConstraint('user_id', 'achievement_id', name='uq_user_achievement'),
    )


# ==================== ЛАДДЕРЫ ====================

class Ladder(Base):
    """Ладдер — ежедневное рейтинговое соревнование"""
    __tablename__ = "ladders"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)
    game_type = Column(String(20), default="1v1")  # 1v1, 2v2, 5v5

    start_date = Column(DateTime, nullable=False, index=True)
    end_date = Column(DateTime, nullable=False)
    status = Column(String(20), default="upcoming", index=True)  # upcoming, active, completed, cancelled

    max_participants = Column(Integer, default=64)
    entry_elo_min = Column(Integer, default=0)    # Мин. ELO для участия
    entry_elo_max = Column(Integer, default=9999) # Макс. ELO

    prize_description = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    discipline = relationship("Discipline")
    participants = relationship("LadderParticipant", back_populates="ladder")
    matches = relationship("LadderMatch", back_populates="ladder", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Ladder(id={self.id}, name='{self.name}', status='{self.status}')>"


class LadderParticipant(Base):
    """Участник ладдера"""
    __tablename__ = "ladder_participants"

    id = Column(Integer, primary_key=True, index=True)
    ladder_id = Column(Integer, ForeignKey("ladders.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)  # для командных

    elo_at_start = Column(Integer, default=1000)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    current_position = Column(Integer, default=0)  # Текущая позиция

    joined_at = Column(DateTime, default=datetime.utcnow)

    ladder = relationship("Ladder", back_populates="participants")
    user = relationship("User")
    team = relationship("Team")

    __table_args__ = (
        UniqueConstraint('ladder_id', 'user_id', name='uq_ladder_user'),
    )


class LadderMatch(Base):
    """Матч в рамках ладдера"""
    __tablename__ = "ladder_matches"

    id = Column(Integer, primary_key=True, index=True)
    ladder_id = Column(Integer, ForeignKey("ladders.id"), nullable=False, index=True)

    challenger_id = Column(Integer, ForeignKey("ladder_participants.id"), nullable=False, index=True)
    opponent_id = Column(Integer, ForeignKey("ladder_participants.id"), nullable=False, index=True)

    challenger_score = Column(Integer, default=0)
    opponent_score = Column(Integer, default=0)

    winner_id = Column(Integer, ForeignKey("ladder_participants.id"), nullable=True)
    status = Column(String(20), default="pending", index=True)  # pending, completed, disputed

    reported_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    verified = Column(Boolean, default=False, index=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    completed_at = Column(DateTime, nullable=True)

    ladder = relationship("Ladder", back_populates="matches")
    challenger = relationship("LadderParticipant", foreign_keys=[challenger_id])
    opponent = relationship("LadderParticipant", foreign_keys=[opponent_id])
    winner = relationship("LadderParticipant", foreign_keys=[winner_id])
    reporter = relationship("User")


# ==================== ПОДПИСКИ ====================

class Subscription(Base):
    """Подписка пользователя"""
    __tablename__ = "subscriptions"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    plan = Column(String(20), nullable=False, index=True)  # monthly, yearly
    status = Column(String(20), default="active", index=True)  # active, cancelled, expired

    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=False, index=True)
    cancelled_at = Column(DateTime, nullable=True)

    payment_provider = Column(String(50), nullable=True)  # yookassa, stripe
    payment_id = Column(String(200), nullable=True)

    auto_renew = Column(Boolean, default=True)

    user = relationship("User", backref="subscriptions")

    @property
    def is_active(self):
        return self.status == "active" and self.expires_at > datetime.utcnow()


# ==================== ИСТОРИЯ МАТЧЕЙ ====================

class MatchHistoryItem(Base):
    """Детальная запись в истории матча для статистики"""
    __tablename__ = "match_history"

    id = Column(Integer, primary_key=True, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    team_side = Column(String(10), nullable=True)  # team1, team2

    result = Column(String(10), nullable=True)  # win, loss, draw
    elo_change = Column(Integer, default=0)
    elo_after = Column(Integer, nullable=True)

    # Персональная статистика (для игр с авто-сбором)
    kills = Column(Integer, nullable=True)
    deaths = Column(Integer, nullable=True)
    assists = Column(Integer, nullable=True)
    cs = Column(Integer, nullable=True)  # Last hits
    gpm = Column(Integer, nullable=True)  # Gold per min
    xpm = Column(Integer, nullable=True)  # XP per min

    screenshot_url = Column(String(500), nullable=True)
    notes = Column(Text, nullable=True)

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    match = relationship("Match")
    user = relationship("User")


# ==================== STEAM ПРИВЯЗКА ====================

class SteamUser(Base):
    """Привязка Steam аккаунта к пользователю"""
    __tablename__ = "steam_users"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    steam_id_64 = Column(String(20), nullable=False, unique=True, index=True)
    persona_name = Column(String(100), nullable=True)
    avatar_url = Column(String(500), nullable=True)
    profile_url = Column(String(500), nullable=True)

    linked_at = Column(DateTime, default=datetime.utcnow)
    last_sync_at = Column(DateTime, nullable=True)

    user = relationship("User")


# ==================== РЕЙТИНГ УЧЕНИКОВ ====================

class StudentRating(Base):
    """Рейтинг ученика — оценивается тренерами и администраторами"""
    __tablename__ = "student_ratings"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)  # основной тренер

    # Рейтинг от 0 до 10000
    score = Column(Integer, default=1000, index=True)
    grade = Column(String(10), default="N")  # N, F, E, D, C, B, A, S, SS, SSS

    # Статистика
    training_completed = Column(Integer, default=0)
    training_missed = Column(Integer, default=0)
    behavior_score = Column(Integer, default=50)  # 0-100

    # Мета
    last_updated_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    notes = Column(Text, nullable=True)  # Заметки тренера об ученике
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    student = relationship("User", foreign_keys=[student_id])
    coach = relationship("User", foreign_keys=[coach_id])
    last_updated_user = relationship("User", foreign_keys=[last_updated_by])
    changes = relationship("StudentRatingChange", back_populates="rating", order_by="StudentRatingChange.created_at.desc()")

    @property
    def grade_color(self) -> str:
        colors = {
            "N": "#8b949e", "F": "#f87171", "E": "#f97316", "D": "#fbbf24",
            "C": "#84cc16", "B": "#22c55e", "A": "#06b6d4", "S": "#3b82f6",
            "SS": "#8b5cf6", "SSS": "#ec4899"
        }
        return colors.get(self.grade, "#8b949e")

    def recalculate_grade(self):
        """Пересчёт грейда на основе score"""
        if self.score >= 9500: self.grade = "SSS"
        elif self.score >= 8500: self.grade = "SS"
        elif self.score >= 7500: self.grade = "S"
        elif self.score >= 6500: self.grade = "A"
        elif self.score >= 5500: self.grade = "B"
        elif self.score >= 4500: self.grade = "C"
        elif self.score >= 3500: self.grade = "D"
        elif self.score >= 2500: self.grade = "E"
        elif self.score >= 1500: self.grade = "F"
        else: self.grade = "N"


class StudentRatingChange(Base):
    """История изменений рейтинга ученика"""
    __tablename__ = "student_rating_changes"

    id = Column(Integer, primary_key=True, index=True)
    rating_id = Column(Integer, ForeignKey("student_ratings.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)

    score_before = Column(Integer, nullable=False)
    score_after = Column(Integer, nullable=False)
    score_change = Column(Integer, nullable=False)

    reason = Column(String(100), nullable=True)  # Причина изменения
    changed_by_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)  # кто изменил

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    rating = relationship("StudentRating", back_populates="changes")
    student = relationship("User", foreign_keys=[student_id])
    changed_by = relationship("User", foreign_keys=[changed_by_id])


# ==================== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ ====================

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_extended_tables():
    """Создать все расширенные таблицы"""
    Base.metadata.create_all(bind=engine)


def init_default_achievements():
    """Инициализация достижений по умолчанию"""
    db = SessionLocal()
    try:
        achievements = [
            # Победы
            {"name": "Первая победа", "slug": "first_win", "description": "Одержите первую победу",
             "category": "tournament", "condition_type": "wins", "condition_value": 1,
             "icon_url": "/static/images/achievements/first_win.png"},
            {"name": "Серия из 5 побед", "slug": "win_streak_5", "description": "Выиграйте 5 матчей подряд",
             "category": "tournament", "condition_type": "streak", "condition_value": 5,
             "icon_url": "/static/images/achievements/streak_5.png"},
            {"name": "Серия из 10 побед", "slug": "win_streak_10", "description": "Выиграйте 10 матчей подряд",
             "category": "tournament", "condition_type": "streak", "condition_value": 10,
             "icon_url": "/static/images/achievements/streak_10.png"},

            # ELO
            {"name": "Новичок", "slug": "elo_400", "description": "Достигните 400 ELO",
             "category": "rating", "condition_type": "elo", "condition_value": 400,
             "icon_url": "/static/images/achievements/elo_400.png"},
            {"name": "Опытный", "slug": "elo_800", "description": "Достигните 800 ELO",
             "category": "rating", "condition_type": "elo", "condition_value": 800,
             "icon_url": "/static/images/achievements/elo_800.png"},
            {"name": "Элита", "slug": "elo_1400", "description": "Достигните 1400 ELO",
             "category": "rating", "condition_type": "elo", "condition_value": 1400,
             "icon_url": "/static/images/achievements/elo_1400.png"},
            {"name": "Легенда", "slug": "elo_2000", "description": "Достигните 2000 ELO",
             "category": "rating", "condition_type": "elo", "condition_value": 2000,
             "icon_url": "/static/images/achievements/elo_2000.png"},

            # Активность
            {"name": "Первый турнир", "slug": "first_tournament", "description": "Примите участие в первом турнире",
             "category": "tournament", "condition_type": "tournaments", "condition_value": 1,
             "icon_url": "/static/images/achievements/first_tournament.png"},
            {"name": "Ветеран", "slug": "games_100", "description": "Сыграйте 100 матчей",
             "category": "general", "condition_type": "games", "condition_value": 100,
             "icon_url": "/static/images/achievements/veteran.png"},

            # Социальные
            {"name": "Командный игрок", "slug": "team_player", "description": "Создайте свою первую команду",
             "category": "social", "condition_type": "teams", "condition_value": 1,
             "icon_url": "/static/images/achievements/team_player.png"},
        ]

        for ach_data in achievements:
            existing = db.query(Achievement).filter(Achievement.slug == ach_data["slug"]).first()
            if not existing:
                achievement = Achievement(**ach_data)
                db.add(achievement)

        db.commit()
    finally:
        db.close()
