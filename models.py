from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float, Table, UniqueConstraint
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Таблица связи многие-ко-многим для пользователей и дисциплин
user_disciplines = Table(
    'user_disciplines',
    Base.metadata,
    Column('user_id', Integer, ForeignKey('users.id'), primary_key=True),
    Column('discipline_id', Integer, ForeignKey('disciplines.id'), primary_key=True),
    Column('created_at', DateTime, default=datetime.utcnow),
    Column('skill_level', String(20), default='beginner')  # beginner, intermediate, advanced, pro
)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False, index=True)
    is_verified = Column(Boolean, default=False, index=True)
    is_admin = Column(Boolean, default=False, index=True)
    role = Column(String(20), default="user", index=True)  # admin, trainer, student, student_pro, student_ult, user
    verification_token = Column(String, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    # Профиль пользователя
    avatar_url = Column(String(500), nullable=True)
    bio = Column(Text, nullable=True)  # Краткая информация о себе
    date_of_birth = Column(DateTime, nullable=True)
    country = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)
    social_vk = Column(String(200), nullable=True)
    social_telegram = Column(String(100), nullable=True)
    social_discord = Column(String(100), nullable=True)
    
    # Настройки
    notify_email_tournaments = Column(Boolean, default=True)
    notify_email_news = Column(Boolean, default=False)
    is_profile_public = Column(Boolean, default=True)
    
    # Статистика
    total_matches = Column(Integer, default=0)
    total_wins = Column(Integer, default=0)
    total_losses = Column(Integer, default=0)

    # Steam интеграция
    steam_id_64 = Column(String(20), nullable=True, unique=True, index=True)

    news_posts = relationship("News", back_populates="author", foreign_keys="News.author_id")
    teams = relationship("Team", back_populates="captain", foreign_keys="Team.captain_id")
    participations = relationship("TournamentParticipation", back_populates="user")
    admin_logs = relationship("AdminLog", back_populates="admin")
    # Связь с дисциплинами (многие-ко-многим)
    disciplines = relationship("Discipline", secondary=user_disciplines, back_populates="users",
                               lazy="selectin", cascade="all, delete")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False, index=True)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_published = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)

    author = relationship("User", back_populates="news_posts")

    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', created_at={self.created_at})>"


class Discipline(Base):
    __tablename__ = "disciplines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(50), nullable=False, unique=True, index=True)
    description = Column(Text, nullable=True)
    icon = Column(String(500), nullable=True)  # URL иконки/изображения
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    teams = relationship("Team", back_populates="discipline")
    tournaments = relationship("Tournament", back_populates="discipline")
    users = relationship("User", secondary=user_disciplines, back_populates="disciplines")

    def __repr__(self):
        return f"<Discipline(id={self.id}, name='{self.name}')>"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)
    captain_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    rating = Column(Float, default=0.0, index=True)
    is_active = Column(Boolean, default=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    discipline = relationship("Discipline", back_populates="teams")
    captain = relationship("User", back_populates="teams")
    members = relationship("TeamMember", back_populates="team")
    tournament_participations = relationship("TournamentParticipation", back_populates="team")

    @property
    def win_rate(self):
        total = self.wins + self.losses
        if total == 0:
            return 0.0
        return (self.wins / total) * 100

    def __repr__(self):
        return f"<Team(id={self.id}, name='{self.name}')>"


class TeamMember(Base):
    __tablename__ = "team_members"

    id = Column(Integer, primary_key=True, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    player_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow, index=True)

    team = relationship("Team", back_populates="members")
    user = relationship("User")

    def __repr__(self):
        return f"<TeamMember(id={self.id}, team_id={self.team_id})>"


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)
    description = Column(Text, nullable=True)
    prize_pool = Column(String(100), nullable=True)
    max_teams = Column(Integer, default=16)
    registration_deadline = Column(DateTime, nullable=True, index=True)
    start_date = Column(DateTime, nullable=True, index=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="upcoming", index=True)
    format = Column(String(30), default="single_elimination")
    is_online = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    discipline = relationship("Discipline", back_populates="tournaments")
    participations = relationship("TournamentParticipation", back_populates="tournament")
    matches = relationship("Match", back_populates="tournament", cascade="all, delete-orphan")

    @property
    def registered_teams_count(self):
        return len([p for p in self.participations if p.is_confirmed])

    def __repr__(self):
        return f"<Tournament(id={self.id}, name='{self.name}')>"


class TournamentParticipation(Base):
    __tablename__ = "tournament_participations"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False, index=True)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    is_confirmed = Column(Boolean, default=False, index=True)
    registered_at = Column(DateTime, default=datetime.utcnow, index=True)

    tournament = relationship("Tournament", back_populates="participations")
    team = relationship("Team", back_populates="tournament_participations")
    user = relationship("User", back_populates="participations")
    matches_team1 = relationship("Match", foreign_keys="Match.team1_id", back_populates="team1")
    matches_team2 = relationship("Match", foreign_keys="Match.team2_id", back_populates="team2")

    def __repr__(self):
        return f"<TournamentParticipation(id={self.id}, tournament_id={self.tournament_id})>"


class Match(Base):
    """Модель для хранения матчей турнирной сетки"""
    __tablename__ = "matches"

    id = Column(Integer, primary_key=True, index=True)
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False, index=True)
    team1_id = Column(Integer, ForeignKey("tournament_participations.id"), nullable=True, index=True)
    team2_id = Column(Integer, ForeignKey("tournament_participations.id"), nullable=True, index=True)
    winner_id = Column(Integer, ForeignKey("tournament_participations.id"), nullable=True, index=True)
    next_match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)

    # Счёт
    team1_score = Column(Integer, default=0)
    team2_score = Column(Integer, default=0)

    # Раунд (например, "1/8 финала", "Полуфинал", "Финал")
    round = Column(String(50), nullable=True, index=True)
    # Порядок матча в раунде
    match_order = Column(Integer, default=0)

    status = Column(String(20), default="pending", index=True)  # pending, completed, cancelled
    scheduled_at = Column(DateTime, nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    tournament = relationship("Tournament", back_populates="matches")
    team1 = relationship("TournamentParticipation", foreign_keys=[team1_id], back_populates="matches_team1")
    team2 = relationship("TournamentParticipation", foreign_keys=[team2_id], back_populates="matches_team2")
    winner = relationship("TournamentParticipation", foreign_keys=[winner_id])
    next_match = relationship("Match", foreign_keys=[next_match_id], remote_side=[id])

    def __repr__(self):
        return f"<Match(id={self.id}, tournament_id={self.tournament_id}, round={self.round})>"


class AdminLog(Base):
    """Модель для логирования действий администратора"""
    __tablename__ = "admin_logs"

    id = Column(Integer, primary_key=True, index=True)
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(50), nullable=False, index=True)
    target_type = Column(String(50), index=True)
    target_id = Column(Integer, nullable=True, index=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    admin = relationship("User", back_populates="admin_logs")

    def __repr__(self):
        return f"<AdminLog(id={self.id}, action={self.action}, admin_id={self.admin_id})>"


class PasswordResetToken(Base):
    """Модель для токенов сброса пароля"""
    __tablename__ = "password_reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    token = Column(String, nullable=False, unique=True, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False)
    is_used = Column(Boolean, default=False, index=True)

    user = relationship("User", backref="reset_tokens")

    def __repr__(self):
        return f"<PasswordResetToken(id={self.id}, user_id={self.user_id})>"


class CoachStudent(Base):
    """Модель связи тренер-ученик"""
    __tablename__ = "coach_students"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    notes = Column(Text, nullable=True)  # Заметки тренера об ученике

    coach = relationship("User", foreign_keys=[coach_id], backref="coached_students")
    student = relationship("User", foreign_keys=[student_id], backref="coaches")

    def __repr__(self):
        return f"<CoachStudent(coach_id={self.coach_id}, student_id={self.student_id})>"


class TrainingSession(Base):
    """Модель для тренировок тренера с учениками"""
    __tablename__ = "training_sessions"

    id = Column(Integer, primary_key=True, index=True)
    coach_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=True, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    scheduled_at = Column(DateTime, nullable=True, index=True)
    duration_minutes = Column(Integer, default=60)
    status = Column(String(20), default="scheduled", index=True)  # scheduled, completed, cancelled
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    coach = relationship("User", foreign_keys=[coach_id], backref="training_sessions")
    discipline = relationship("Discipline", backref="training_sessions")
    attendees = relationship("TrainingAttendance", back_populates="session")

    def __repr__(self):
        return f"<TrainingSession(id={self.id}, title='{self.title}')>"


class TrainingAttendance(Base):
    """Посещаемость тренировок"""
    __tablename__ = "training_attendance"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("training_sessions.id"), nullable=False, index=True)
    student_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    status = Column(String(20), default="pending", index=True)  # pending, attended, missed
    notes = Column(Text, nullable=True)

    session = relationship("TrainingSession", back_populates="attendees")
    student = relationship("User")

    def __repr__(self):
        return f"<TrainingAttendance(session_id={self.session_id}, student_id={self.student_id})>"


# ==================== СИСТЕМА РЕЙТИНГА ELO ====================

class PlayerRating(Base):
    """Рейтинг игрока по дисциплинам (аналог FACEIT Levels 1-10)"""
    __tablename__ = "player_ratings"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)

    # Рейтинг
    elo = Column(Integer, default=1000, index=True)  # Стартовый ELO
    level = Column(Integer, default=1, index=True)   # Уровень 1-10
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)

    # Прогресс
    peak_elo = Column(Integer, default=1000)
    last_game_at = Column(DateTime, nullable=True)

    # Мета
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="ratings", lazy="joined")
    discipline = relationship("Discipline", back_populates="ratings", lazy="joined")

    __table_args__ = (
        UniqueConstraint('user_id', 'discipline_id', name='uq_user_discipline_rating'),
    )

    @property
    def win_rate(self) -> float:
        """Процент побед"""
        if self.games_played == 0:
            return 0.0
        return (self.wins / self.games_played) * 100

    @property
    def progress_to_next_level(self) -> float:
        """Прогресс до следующего уровня (0-100%)"""
        # Каждый уровень = 200 ELO
        elo_in_level = self.elo % 200
        return (elo_in_level / 200) * 100

    def __repr__(self):
        return f"<PlayerRating(user_id={self.user_id}, discipline_id={self.discipline_id}, elo={self.elo}, level={self.level})>"


class RatingChange(Base):
    """История изменений рейтинга игрока"""
    __tablename__ = "rating_changes"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True, index=True)

    elo_before = Column(Integer, nullable=False)
    elo_after = Column(Integer, nullable=False)
    elo_change = Column(Integer, nullable=False)  # +32, -15, etc.

    reason = Column(String(50), default="match")  # win, loss, draw, penalty, bonus

    created_at = Column(DateTime, default=datetime.utcnow, index=True)

    user = relationship("User", back_populates="rating_changes")
    discipline = relationship("Discipline", back_populates="rating_changes")
    match = relationship("Match", back_populates="rating_changes")

    def __repr__(self):
        return f"<RatingChange(user_id={self.user_id}, elo_change={self.elo_change})>"


class MatchmakingQueue(Base):
    """Очередь матчмейкинга для автоматического подбора игр"""
    __tablename__ = "matchmaking_queue"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)

    # Параметры поиска
    game_type = Column(String(20), default="1v1")  # 1v1, 2v2, 5v5
    elo = Column(Integer, nullable=False)
    elo_min = Column(Integer, nullable=True)  # Минимальный ELO для поиска
    elo_max = Column(Integer, nullable=True)  # Максимальный ELO для поиска

    # Статус
    status = Column(String(20), default="waiting", index=True)  # waiting, found, cancelled, timeout
    queued_at = Column(DateTime, default=datetime.utcnow, index=True)
    found_at = Column(DateTime, nullable=True)

    # Ссылка на созданный матч
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)

    user = relationship("User", back_populates="mm_queues")
    discipline = relationship("Discipline", back_populates="mm_queues")
    match = relationship("Match", back_populates="mm_queue")

    def __repr__(self):
        return f"<MatchmakingQueue(user_id={self.user_id}, game_type={self.game_type}, status={self.status})>"


# Добавляем обратные связи в существующие модели
User.ratings = relationship("PlayerRating", order_by=PlayerRating.elo.desc(), back_populates="user")
User.rating_changes = relationship("RatingChange", order_by=RatingChange.created_at.desc(), back_populates="user")
User.mm_queues = relationship("MatchmakingQueue", order_by=MatchmakingQueue.queued_at.desc(), back_populates="user")

Discipline.ratings = relationship("PlayerRating", order_by=PlayerRating.elo.desc(), back_populates="discipline")
Discipline.rating_changes = relationship("RatingChange", order_by=RatingChange.created_at.desc(), back_populates="discipline")
Discipline.mm_queues = relationship("MatchmakingQueue", order_by=MatchmakingQueue.queued_at.desc(), back_populates="discipline")

Match.rating_changes = relationship("RatingChange", order_by=RatingChange.created_at.desc(), back_populates="match")
Match.mm_queue = relationship("MatchmakingQueue", back_populates="match")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def create_tables():
    Base.metadata.create_all(bind=engine)


def init_disciplines():
    """Инициализация дисциплин по умолчанию"""
    db = SessionLocal()
    try:
        disciplines_data = [
            {"name": "Dota 2", "slug": "dota2", "icon": "/static/images/disciplines/dota2.png", "description": "Многопользовательская онлайн-игра в жанре MOBA"},
            {"name": "Counter-Strike 2", "slug": "cs2", "icon": "/static/images/disciplines/cs2.png", "description": "Тактический шутер от первого лица"},
            {"name": "Мир танков", "slug": "tanks", "icon": "/static/images/disciplines/tanks.png", "description": "Многопользовательская онлайн-игра про танковые сражения"},
        ]
        for disc_data in disciplines_data:
            existing = db.query(Discipline).filter(Discipline.slug == disc_data["slug"]).first()
            if not existing:
                discipline = Discipline(**disc_data)
                db.add(discipline)
            else:
                # Обновляем иконки для существующих дисциплин
                existing.icon = disc_data["icon"]
        db.commit()
    finally:
        db.close()
