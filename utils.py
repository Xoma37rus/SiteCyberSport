import logging
from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional, Tuple, List
from jose import jwt
from config import settings
import secrets
import base64
import json
import bcrypt

logger = logging.getLogger(__name__)

# Используем bcrypt напрямую для совместимости
def verify_password(plain_password: str, hashed_password: str) -> bool:
    try:
        return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
    except Exception:
        return False


def get_password_hash(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=settings.access_token_expire_minutes)

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, settings.secret_key, algorithm=settings.algorithm)
    return encoded_jwt


def create_verification_token(email: str) -> str:
    return create_access_token(
        data={"sub": email, "type": "verification"},
        expires_delta=timedelta(hours=24)
    )


def create_reset_token() -> str:
    """Генерация случайного токена для сброса пароля"""
    return secrets.token_urlsafe(32)


# ==================== CSRF Protection ====================

def generate_csrf_token() -> str:
    """Генерация CSRF токена"""
    return secrets.token_urlsafe(32)


def validate_csrf_token(token: str, session_token: str) -> bool:
    """Проверка CSRF токена"""
    if not token or not session_token:
        return False
    return secrets.compare_digest(token, session_token)


# ==================== Flash Messages ====================

def create_flash_message(message: str, message_type: str = "info") -> str:
    """Создание flash-сообщения (для cookie)"""
    import base64
    import json
    data = {"message": message, "type": message_type}
    return base64.b64encode(json.dumps(data).encode()).decode()


def parse_flash_message(encoded: str) -> Optional[dict]:
    """Парсинг flash-сообщения"""
    try:
        data = base64.b64decode(encoded).decode()
        return json.loads(data)
    except Exception as e:
        print(f"Flash parse error: {e}")
        return None


# ==================== СИСТЕМА РЕЙТИНГА ELO ====================

# Уровни рейтинга по аналогии с FACEIT (10 уровней)
ELO_LEVELS = {
    1: (0, 199),
    2: (200, 399),
    3: (400, 599),
    4: (600, 799),
    5: (800, 999),
    6: (1000, 1199),
    7: (1200, 1399),
    8: (1400, 1699),
    9: (1700, 1999),
    10: (2000, float('inf'))
}

# K-факторы для расчёта изменения ELO
K_FACTOR_NEW = 48       # Для новых игроков (< 10 игр)
K_FACTOR_BASE = 32      # Базовый K-фактор (10-100 игр)
K_FACTOR_VETERAN = 16   # Для опытных игроков (> 100 игр)

# Стартовый рейтинг
BASE_ELO = 1000


def get_level_by_elo(elo: int) -> int:
    """
    Определить уровень игрока по его ELO.
    
    Уровни:
    - Level 1: 0-199 ELO
    - Level 2: 200-399 ELO
    - ...
    - Level 10: 2000+ ELO
    """
    for level, (min_elo, max_elo) in ELO_LEVELS.items():
        if min_elo <= elo <= max_elo:
            return level
    return 1


def get_k_factor(games_played: int) -> int:
    """
    Определить K-фактор по количеству сыгранных игр.
    
    K-фактор влияет на скорость изменения рейтинга:
    - Новые игроки быстрее набирают/теряют рейтинг
    - Опытные игроки стабильнее
    """
    if games_played < 10:
        return K_FACTOR_NEW
    elif games_played > 100:
        return K_FACTOR_VETERAN
    return K_FACTOR_BASE


def calculate_expected_score(player_elo: int, opponent_elo: int) -> float:
    """
    Рассчитать ожидаемый счёт матча по формуле ELO.
    
    Формула: E = 1 / (1 + 10 ^ ((R_opponent - R_player) / 400))
    
    Возвращает значение от 0 до 1:
    - 0.5 = равные шансы
    - > 0.5 = игрок фаворит
    - < 0.5 = игрок андердог
    """
    return 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))


def calculate_elo_change(
    player_elo: int,
    opponent_elo: int,
    won: bool,
    is_draw: bool = False,
    games_played: int = 0,
    is_team_game: bool = False
) -> int:
    """
    Рассчитать изменение ELO после матча.
    
    Формула: ΔR = K * (S - E)
    где:
    - K = K-фактор
    - S = фактический счёт (1=победа, 0=поражение, 0.5=ничья)
    - E = ожидаемый счёт
    
    Для командных игр изменение делится на количество игроков.
    """
    # Фактический счёт
    if is_draw:
        actual_score = 0.5
    elif won:
        actual_score = 1.0
    else:
        actual_score = 0.0
    
    # Ожидаемый счёт
    expected_score = calculate_expected_score(player_elo, opponent_elo)
    
    # K-фактор
    k = get_k_factor(games_played)
    
    # Базовое изменение
    change = k * (actual_score - expected_score)
    
    # Бонус за победу над более сильным соперником
    if won and opponent_elo > player_elo + 200:
        change += 5
    
    # Для командных игр уменьшаем влияние
    if is_team_game:
        change = change / 5  # 5 игроков в команде
    
    return int(round(change))


def calculate_team_elo_change(
    team_avg_elo: int,
    opponent_avg_elo: int,
    won: bool,
    is_draw: bool = False,
    team_games_avg: int = 0
) -> int:
    """
    Рассчитать изменение ELO для командного матча (5v5).
    
    Усредняет ELO команды и делит изменение на 5.
    """
    base_change = calculate_elo_change(
        team_avg_elo,
        opponent_avg_elo,
        won,
        is_draw,
        team_games_avg,
        is_team_game=True
    )
    return base_change


def get_or_create_rating(db, user_id: int, discipline_id: int):
    """Получить или создать рейтинг игрока"""
    from models import PlayerRating
    
    rating = db.query(PlayerRating).filter(
        PlayerRating.user_id == user_id,
        PlayerRating.discipline_id == discipline_id
    ).first()
    
    if not rating:
        rating = PlayerRating(
            user_id=user_id,
            discipline_id=discipline_id,
            elo=BASE_ELO,
            level=1
        )
        db.add(rating)
        db.flush()
    
    return rating


def update_player_rating(
    db,
    user_id: int,
    discipline_id: int,
    elo_change: int,
    won: bool,
    is_draw: bool = False,
    match_id: int = None
) -> 'PlayerRating':
    """
    Обновить рейтинг игрока после матча.
    
    Args:
        db: Сессия базы данных
        user_id: ID пользователя
        discipline_id: ID дисциплины
        elo_change: Изменение ELO (+/-)
        won: True если победа
        is_draw: True если ничья
        match_id: ID матча (опционально)
    
    Returns:
        Обновлённый объект PlayerRating
    """
    from models import PlayerRating, RatingChange
    
    rating = get_or_create_rating(db, user_id, discipline_id)
    
    # Сохраняем состояние до изменения
    elo_before = rating.elo
    old_level = rating.level
    
    # Обновляем ELO (не ниже 0)
    rating.elo = max(0, rating.elo + elo_change)
    rating.level = get_level_by_elo(rating.elo)
    rating.games_played += 1
    rating.last_game_at = datetime.utcnow()
    
    # Обновляем статистику
    if won:
        rating.wins += 1
        rating.peak_elo = max(rating.peak_elo, rating.elo)
    elif is_draw:
        rating.draws += 1
    else:
        rating.losses += 1
    
    # Создаём запись истории изменений
    change_record = RatingChange(
        user_id=user_id,
        discipline_id=discipline_id,
        match_id=match_id,
        elo_before=elo_before,
        elo_after=rating.elo,
        elo_change=elo_change,
        reason="draw" if is_draw else ("win" if won else "loss")
    )
    db.add(change_record)
    
    # Логирование повышения уровня
    if rating.level > old_level:
        logger.info(f"Player {user_id} leveled up: {old_level} -> {rating.level} (ELO: {elo_before} -> {rating.elo})")
    
    return rating


def get_opponent_rating_for_match(db, user_id: int, discipline_id: int, exclude_user_ids: List[int] = None) -> int:
    """
    Получить средний рейтинг потенциальных соперников для расчёта изменения ELO.
    
    Используется когда точный соперник неизвестен (например, в матчмейкинге).
    """
    from models import PlayerRating
    
    query = db.query(PlayerRating).filter(
        PlayerRating.discipline_id == discipline_id,
        PlayerRating.user_id != user_id
    )
    
    if exclude_user_ids:
        query = query.filter(~PlayerRating.user_id.in_(exclude_user_ids))
    
    # Получаем средний ELO игроков близкого уровня
    avg_rating = query.order_by(PlayerRating.elo).limit(10).all()
    
    if not avg_rating:
        return BASE_ELO
    
    return int(sum(r.elo for r in avg_rating) / len(avg_rating))
