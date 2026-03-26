from sqlalchemy import create_engine, Column, Integer, String, Boolean, DateTime, Text, ForeignKey, Float
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
from config import settings

engine = create_engine(settings.database_url, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    is_active = Column(Boolean, default=False)
    is_verified = Column(Boolean, default=False)
    is_admin = Column(Boolean, default=False)
    role = Column(String(20), default="user")  # admin, trainer, student, student_pro, student_ult, user
    verification_token = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    news_posts = relationship("News", back_populates="author", foreign_keys="News.author_id")
    teams = relationship("Team", back_populates="captain", foreign_keys="Team.captain_id")
    participations = relationship("TournamentParticipation", back_populates="user")
    admin_logs = relationship("AdminLog", back_populates="admin")

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username})>"


class News(Base):
    __tablename__ = "news"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(200), nullable=False)
    content = Column(Text, nullable=False)
    excerpt = Column(String(500), nullable=True)
    image_url = Column(String(500), nullable=True)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_published = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    author = relationship("User", back_populates="news_posts")

    def __repr__(self):
        return f"<News(id={self.id}, title='{self.title}', created_at={self.created_at})>"


class Discipline(Base):
    __tablename__ = "disciplines"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False, unique=True)
    slug = Column(String(50), nullable=False, unique=True)
    description = Column(Text, nullable=True)
    icon = Column(String(500), nullable=True)  # URL иконки/изображения
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    teams = relationship("Team", back_populates="discipline")
    tournaments = relationship("Tournament", back_populates="discipline")

    def __repr__(self):
        return f"<Discipline(id={self.id}, name='{self.name}')>"


class Team(Base):
    __tablename__ = "teams"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False)
    captain_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    description = Column(Text, nullable=True)
    logo_url = Column(String(500), nullable=True)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    rating = Column(Float, default=0.0)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    player_name = Column(String(100), nullable=True)
    role = Column(String(50), nullable=True)
    joined_at = Column(DateTime, default=datetime.utcnow)

    team = relationship("Team", back_populates="members")
    user = relationship("User")

    def __repr__(self):
        return f"<TeamMember(id={self.id}, team_id={self.team_id})>"


class Tournament(Base):
    __tablename__ = "tournaments"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(200), nullable=False)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False)
    description = Column(Text, nullable=True)
    prize_pool = Column(String(100), nullable=True)
    max_teams = Column(Integer, default=16)
    registration_deadline = Column(DateTime, nullable=True)
    start_date = Column(DateTime, nullable=True)
    end_date = Column(DateTime, nullable=True)
    status = Column(String(20), default="upcoming")
    format = Column(String(30), default="single_elimination")
    is_online = Column(Boolean, default=True)
    image_url = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
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
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    team_id = Column(Integer, ForeignKey("teams.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    is_confirmed = Column(Boolean, default=False)
    registered_at = Column(DateTime, default=datetime.utcnow)

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
    tournament_id = Column(Integer, ForeignKey("tournaments.id"), nullable=False)
    team1_id = Column(Integer, ForeignKey("tournament_participations.id"), nullable=True)
    team2_id = Column(Integer, ForeignKey("tournament_participations.id"), nullable=True)
    winner_id = Column(Integer, ForeignKey("tournament_participations.id"), nullable=True)
    next_match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    
    # Счёт
    team1_score = Column(Integer, default=0)
    team2_score = Column(Integer, default=0)
    
    # Раунд (например, "1/8 финала", "Полуфинал", "Финал")
    round = Column(String(50), nullable=True)
    # Порядок матча в раунде
    match_order = Column(Integer, default=0)
    
    status = Column(String(20), default="pending")  # pending, completed, cancelled
    scheduled_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

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
    admin_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String(50), nullable=False)
    target_type = Column(String(50))
    target_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    admin = relationship("User", back_populates="admin_logs")

    def __repr__(self):
        return f"<AdminLog(id={self.id}, action={self.action}, admin_id={self.admin_id})>"


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
