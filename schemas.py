from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List
from datetime import datetime


class BaseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class UserResponse(BaseResponse):
    id: int
    email: str
    username: str
    is_active: bool
    is_verified: bool
    created_at: datetime
    disciplines: Optional[List["DisciplineResponse"]] = []
    
    model_config = ConfigDict(from_attributes=True, arbitrary_types_allowed=True)


class NewsResponse(BaseResponse):
    id: int
    title: str
    content: str
    excerpt: Optional[str] = None
    image_url: Optional[str] = None
    author_id: Optional[int] = None
    is_published: bool
    created_at: datetime
    updated_at: datetime


class NewsListResponse(BaseModel):
    items: List[NewsResponse]
    total: int
    page: int
    limit: int
    pages: int


class DisciplineResponse(BaseResponse):
    id: int
    name: str
    slug: str
    description: Optional[str] = None
    icon: Optional[str] = None
    is_active: bool
    created_at: datetime


class DisciplineListResponse(BaseModel):
    items: List[DisciplineResponse]
    total: int


class TeamResponse(BaseResponse):
    id: int
    name: str
    discipline_id: int
    captain_id: Optional[int] = None
    description: Optional[str] = None
    logo_url: Optional[str] = None
    wins: int
    losses: int
    rating: float
    is_active: bool
    created_at: datetime
    win_rate: float


class TeamListResponse(BaseModel):
    items: List[TeamResponse]
    total: int
    page: int
    limit: int


class TournamentResponse(BaseResponse):
    id: int
    name: str
    discipline_id: int
    description: Optional[str] = None
    prize_pool: Optional[str] = None
    max_teams: int
    registration_deadline: Optional[datetime] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    status: str
    format: str
    is_online: bool
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    registered_teams_count: int


class TournamentListResponse(BaseModel):
    items: List[TournamentResponse]
    total: int
    page: int
    limit: int


class HealthResponse(BaseModel):
    status: str
    service: str
    version: Optional[str] = None


class UserRegister(BaseModel):
    email: EmailStr
    username: str
    password: str


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr


class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


class Token(BaseModel):
    access_token: str
    token_type: str


class VerifyEmail(BaseModel):
    token: str


# ==================== СИСТЕМА РЕЙТИНГА ELO ====================

class PlayerRatingResponse(BaseResponse):
    """Ответ с рейтингом игрока"""
    id: int
    user_id: int
    discipline_id: int
    elo: int
    level: int
    games_played: int
    wins: int
    losses: int
    draws: int
    peak_elo: int
    last_game_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime
    win_rate: float
    progress_to_next_level: float
    
    model_config = ConfigDict(from_attributes=True)


class RatingChangeResponse(BaseResponse):
    """Ответ с историей изменения рейтинга"""
    id: int
    user_id: int
    discipline_id: int
    match_id: Optional[int] = None
    elo_before: int
    elo_after: int
    elo_change: int
    reason: str
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)


class LeaderboardItem(BaseModel):
    """Элемент таблицы лидеров"""
    rank: int
    user_id: int
    username: str
    avatar_url: Optional[str] = None
    elo: int
    level: int
    games_played: int
    wins: int
    losses: int
    win_rate: float
    peak_elo: int


class LeaderboardResponse(BaseModel):
    """Ответ таблицы лидеров"""
    discipline: str
    discipline_name: str
    items: List[LeaderboardItem]
    total: int
    limit: int


class RatingHistoryResponse(BaseModel):
    """Ответ с историей рейтинга"""
    user_id: int
    discipline: str
    items: List[RatingChangeResponse]
    total: int


class UserRatingSummary(BaseModel):
    """Краткая информация о рейтинге пользователя"""
    discipline_id: int
    discipline_name: str
    discipline_slug: str
    discipline_icon: Optional[str] = None
    elo: int
    level: int
    games_played: int
    wins: int
    losses: int
    win_rate: float
    progress_to_next_level: float


class UserRatingsResponse(BaseModel):
    """Ответ со всеми рейтингами пользователя"""
    user_id: int
    username: str
    ratings: List[UserRatingSummary]
    total_ratings: int


# ==================== МАТЧМЕЙКИНГ ====================

class MatchmakingQueueResponse(BaseModel):
    """Ответ со статусом очереди матчмейкинга"""
    status: str  # waiting, found, cancelled, timeout
    game_type: str
    elo: int
    queued_at: datetime
    wait_time: int  # секунды
    estimated_time: Optional[int] = None  # предполагаемое время ожидания
