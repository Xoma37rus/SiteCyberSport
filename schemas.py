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


class Token(BaseModel):
    access_token: str
    token_type: str


class VerifyEmail(BaseModel):
    token: str
