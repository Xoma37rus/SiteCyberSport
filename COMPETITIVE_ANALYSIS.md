# 🔍 Полный анализ EasyCyberPro: Сравнение с конкурентами и стратегия развития

**Дата анализа:** 1 апреля 2026 г.  
**Аналитик:** AI Assistant  
**Статус платформы:** MVP с базовым функционалом

---

## 📊 ЧАСТЬ 1: ТЕКУЩЕЕ СОСТОЯНИЕ EASYCYBERPRO

### 1.1 Технический аудит

| Компонент | Статус | Оценка |
|-----------|--------|--------|
| **Backend Framework** | FastAPI (Python) | ✅ Отлично |
| **База данных** | SQLite (dev) | ⚠️ Только для разработки |
| **ORM** | SQLAlchemy 2.0 | ✅ Отлично |
| **Аутентификация** | JWT + bcrypt | ✅ Хорошо |
| **Frontend** | Jinja2 + HTML/CSS | ⚠️ Базовый уровень |
| **API** | REST API v1 | ✅ Хорошо |
| **Тесты** | pytest (есть файлы) | ⚠️ Требуются данные |
| **Миграции** | Alembic настроен | ✅ Хорошо |
| **Email-рассылка** | FastAPI-Mail | ✅ Реализовано |
| **Rate Limiting** | SlowAPI | ✅ Реализовано |

### 1.2 Функциональный аудит

#### ✅ Реализованный функционал

| Модуль | Функции | Готовность |
|--------|---------|------------|
| **Аутентификация** | Регистрация, вход, logout, восстановление пароля, email-верификация | 100% |
| **Профиль пользователя** | Аватар, био, соцсети, дисциплины, настройки приватности | 100% |
| **Настройки** | Смена пароля, email-уведомления, приватность | 100% |
| **Команды** | Создание, редактирование, список команд капитана | 80% |
| **Турниры** | Каталог, фильтрация, поиск, регистрация команд | 85% |
| **Заявки на турниры** | Подача заявок, статусы, подтверждения | 75% |
| **Новости** | Просмотр, категории | 70% |
| **Дисциплины** | Dota 2, CS2, Мир танков (иконки, описания) | 100% |
| **Тренерская система** | Ученики, тренировки, посещаемость, заметки | 90% |
| **Админ-панель** | Пользователи, логи, роли, CSRF-защита | 85% |
| **REST API** | Базовые endpoints для всех сущностей | 80% |

#### ⚠️ Частично реализованный функционал

| Модуль | Проблема | Статус |
|--------|----------|--------|
| **Турнирная сетка** | Модель `Match` есть, но нет UI для bracket | 30% |
| **Рейтинг игроков** | Поля `total_matches`, `total_wins`, `total_losses` в User, но нет расчёта | 20% |
| **Рейтинг команд** | Поле `rating` в Team, но нет формулы расчёта | 25% |
| **Матчи** | Модель есть, но нет создания/обновления результатов | 40% |
| **Уведомления** | Email есть, но нет push/Discord | 50% |

#### ❌ Отсутствующий функционал

| Модуль | Критичность | Влияние |
|--------|-------------|---------|
| **Матчмейкинг** | 🔴 Критично | Невозможен быстрый поиск игр |
| **Система ELO** | 🔴 Критично | Нет прогрессии игроков |
| **Leaderboard** | 🔴 Критично | Нет таблицы лидеров |
| **Визуализация bracket** | 🔴 Критично | Невозможно следить за турниром |
| **Античит** | 🔴 Критично | Нет доверия к результатам |
| **Интеграция с играми** | 🟡 Средне | Ручной ввод результатов |
| **Статистика игроков** | 🟡 Средне | Нет аналитики |
| **Ладдеры** | 🟡 Средне | Нет ежедневных соревнований |
| **Стриминг** | 🟢 Низко | Нет трансляций матчей |
| **Мобильное приложение** | 🟢 Низко | Нет доступа с телефона |

---

## 🏆 ЧАСТЬ 2: АНАЛИЗ КОНКУРЕНТОВ

### 2.1 FACEIT — Мировой лидер

**Год основания:** 2012 | **Аудитория:** 10+ млн | **Штаб-квартира:** Лондон

#### Ключевые возможности

| Функция | Описание | Технология |
|---------|----------|------------|
| **Приватные серверы** | 128-tick серверы для CS2 | Собственная инфраструктура |
| **Античит** | Kernel-level детект | FACEIT AC (собственная разработка) |
| **Рейтинг ELO** | 10 уровней (1-10), Challenger топ-1000 | Glicko-2 |
| **Матчмейкинг** | Подбор за 2-5 минут по ELO ±200 | Real-time алгоритм |
| **Турниры** | Daily, weekly, monthly, FPL квалификации | Автоматизация |
| **Верификация** | Passport System (ID + селфи) | Jumio API |
| **Premium** | Вето карт, Super Match, миссии | Платная подписка |
| **Статистика** | K/D/A, HS%, winrate, графики | Steam API + свои данные |

#### Бизнес-модель
- **Premium:** $5.99/месяц
- **Призы:** Турниры с призовыми фондами
- **Партнёрства:** Спонсоры (Intel, Dell, HyperX)

---

### 2.2 Battlefy — Платформа для организаторов

**Год основания:** 2012 | **Аудитория:** 5+ млн | **Штаб-квартира:** Канада

#### Ключевые возможности

| Функция | Описание |
|---------|----------|
| **Типы сеток** | Single/Double Elimination, Round Robin, Swiss, Groups |
| **Масштаб** | Поддержка 30,000+ игроков в одном турнире |
| **Check-in** | Обязательная регистрация за 30 мин до матча |
| **Планирование** | Расписание, таймзоны, напоминания |
| **Трансляции** | Twitch embed на странице турнира |
| **Брендинг** | Кастомизация страницы турнира |
| **Экспорт** | CSV, API для статистики |

#### Бизнес-модель
- **Freemium:** Базовые функции бесплатно
- **Premium:** $99-499/месяц для организаторов
- **Enterprise:** Индивидуальные цены

---

### 2.3 ESL Play — Европейская лига

**Год основания:** 2000 | **Аудитория:** 2+ млн | **Штаб-квартира:** Германия

#### Ключевые возможности

| Функция | Описание |
|---------|----------|
| **Лиги** | Дивизионы с продвижением/вылетом |
| **Кубки** | Ежедневные/еженедельные с призами |
| **Рейтинг команд** | Глобальный рейтинг |
| **Античит** | ESL Wire Anti-Cheat |
| **Призовые** | Реальные денежные призы |

#### Бизнес-модель
- **Взносы:** Платное участие в турнирах
- **Спонсоры:** DHL, Mercedes, Intel
- **Медиаправа:** Трансляции на Twitch/YouTube

---

### 2.4 Toornament — Европейский конкурент

**Год основания:** 2007 | **Аудитория:** 1+ млн | **Штаб-квартира:** Франция

#### Ключевые возможности

| Функция | Описание |
|---------|----------|
| **Турниры** | Любой формат и масштаб |
| **Регистрация** | Индивидуальная и командная |
| **Жеребьёвка** | Автоматическая генерация сеток |
| **Результаты** | Онлайн-отчётность |

---

### 2.5 PlayVS — Американский стартап

**Год основания:** 2018 | **Аудитория:** 500K+ | **Штаб-квартира:** США

#### Уникальность
- **Фокус:** Школьные и университетские лиги
- **Партнёрства:** NASEF, штаты США
- **Игры:** Rocket League, LoL, NBA 2K

---

## 📈 ЧАСТЬ 3: СРАВНИТЕЛЬНАЯ ТАБЛИЦА

| Функция | EasyCyberPro | FACEIT | Battlefy | ESL Play | Toornament |
|---------|--------------|--------|----------|----------|------------|
| **Аутентификация** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Профили игроков** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Команды** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Турниры** | ✅ Базовые | ✅ | ✅ Продвинутые | ✅ | ✅ |
| **Турнирные сетки** | ⚠️ Модель | ✅ | ✅ Все типы | ✅ | ✅ |
| **Рейтинг ELO** | ❌ | ✅ 1-10 | ✅ | ✅ Дивизионы | ⚠️ |
| **Матчмейкинг** | ❌ | ✅ | ❌ | ✅ | ❌ |
| **Античит** | ❌ | ✅ Kernel | ❌ | ✅ ESL Wire | ❌ |
| **Приватные серверы** | ❌ | ✅ | ❌ | ✅ | ❌ |
| **Ладдеры** | ❌ | ✅ | ⚠️ | ✅ | ⚠️ |
| **Статистика** | ⚠️ Базовая | ✅ | ✅ | ✅ | ✅ |
| **Стриминг** | ❌ | ✅ | ✅ Twitch | ✅ | ✅ |
| **Призовые фонды** | ⚠️ Поле в БД | ✅ | ✅ | ✅ Деньги | ✅ |
| **Тренерская система** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Email-уведомления** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **REST API** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Админ-панель** | ✅ | ✅ | ✅ | ✅ | ✅ |
| **Мобильное приложение** | ❌ | ✅ | ❌ | ❌ | ❌ |
| **Premium-подписка** | ❌ | ✅ | ⚠️ | ✅ | ⚠️ |
| **Discord-интеграция** | ❌ | ✅ | ✅ | ✅ | ✅ |
| **Steam-интеграция** | ❌ | ✅ | ⚠️ | ✅ | ❌ |
| **Локализация** | ✅ RU | ❌ EN | ❌ EN | ❌ EN | ⚠️ Мульти |

---

## 🎯 ЧАСТЬ 4: SWOT-АНАЛИЗ EASYCYBERPRO

### Strengths (Сильные стороны)

1. **Тренерская система** — Единственная платформа с встроенной системой тренер-ученик
   - Управление учениками
   - Планирование тренировок
   - Посещаемость и заметки
   - **Уникальное преимущество!**

2. **Локализация** — Русский интерфейс (конкуренты преимущественно на английском)
   - Фокус на СНГ-регион
   - Культурная близость

3. **Простота развёртывания** — SQLite + FastAPI
   - Работает на любом VPS за $5/месяц
   - Нет сложных зависимостей

4. **Открытая архитектура** — Возможность кастомизации
   - Легко добавить функции
   - Прозрачный код

5. **Современный стек** — FastAPI, SQLAlchemy 2.0, Pydantic 2.0
   - Высокая производительность
   - Асинхронность
   - Автоматическая документация

### Weaknesses (Слабые стороны)

1. **Нет матчмейкинга** — Критический недостаток
   - Пользователи не могут быстро найти игру
   - Ручное создание матчей

2. **Нет визуализации турнирных сеток** — Bracket UI отсутствует
   - Невозможно следить за ходом турнира
   - Устаревший UX

3. **Нет системы рейтинга** — ELO/уровни не реализованы
   - Нет прогрессии для игроков
   - Нет мотивации развиваться

4. **Нет интеграции с играми** — Ручной ввод результатов
   - Возможны фейки
   - Недоверие к платформе

5. **SQLite для production** — Не подходит для нагрузки
   - Нет масштабируемости
   - Риск потери данных

6. **Базовая статистика** — Нет аналитики
   - Игроки не видят прогресс
   - Нет экспорта данных

### Opportunities (Возможности)

1. **Рынок СНГ** — 10+ млн геймеров в регионе
   - Нет доминирующей локальной платформы
   - FACEIT не локализован

2. **Образовательный фокус** — Тренерская система
   - Партнёрства с киберспортивными школами
   - Сертифицированные тренеры

3. **Мобильное приложение** — React Native/Flutter
   - Доступ с телефона
   - Push-уведомления

4. **Discord-интеграция** — Бот для уведомлений
   - 80% геймеров используют Discord
   - Бесплатная интеграция

5. **Монетизация** — Premium-подписка
   - $3-5/месяц для региона
   - Расширенные функции

6. **Партнёрства** — Киберспортивные организации
   - Команды, турниры, спонсоры

### Threats (Угрозы)

1. **Конкуренция** — FACEIT, Battlefy, ESL
   - Огромные бюджеты
   - Устоявшаяся аудитория

2. **Античит** — Сложность разработки
   - Требует экспертных знаний
   - Юридические риски

3. **Лицензирование** — Права на игры
   - Valve, Riot, Blizzard
   - Юридические ограничения

4. **Масштабирование** — Инфраструктура
   - Серверы, CDN, нагрузка
   - Высокие затраты

5. **Регулирование** — Законодательство
   - Персональные данные
   - Возрастные ограничения

---

## 🚀 ЧАСТЬ 5: ПЛАН РАЗВИТИЯ

### Приоритизация по матрице Impact/Effort

```
                    ВЫСОКИЙ IMPACT
                    ┌─────────┬─────────┐
                    │  Фаза 1 │  Фаза 2 │
                    │ Критично │ Важно  │
                    │ ELO      │ Стат   │
                    │ Bracket  │ Discord│
                    ├─────────┼─────────┤
                    │  Фаза 3 │  Фаза 4 │
                    │ Долгосрок│ Мелочи │
                    │ Mobile   │ Награды│
                    │ Premium  │ UI     │
                    └─────────┴─────────┘
                    НИЗКИЙ        ВЫСОКИЙ
                         EFFORT
```

---

## 🔥 ФАЗА 1: КРИТИЧЕСКИЕ УЛУЧШЕНИЯ (4-6 недель)

### 1.1 Система рейтинга ELO (Недели 1-2)

**Цель:** Внедрить рейтинговую систему по аналогии с FACEIT (10 уровней, ELO 0-2500+)

#### Задачи

**День 1-3: Модель данных**

```python
# models.py — новая модель
class PlayerRating(Base):
    __tablename__ = "player_ratings"

    id = Column(Integer, primary_key=True)
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
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="ratings", lazy="joined")
    discipline = relationship("Discipline", backref="ratings", lazy="joined")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'discipline_id', name='uq_user_discipline'),
    )


class RatingChange(Base):
    """История изменений рейтинга"""
    __tablename__ = "rating_changes"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    
    elo_before = Column(Integer, nullable=False)
    elo_after = Column(Integer, nullable=False)
    elo_change = Column(Integer, nullable=False)  # +32, -15, etc.
    
    reason = Column(String(50))  # win, loss, draw, penalty, bonus
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", backref="rating_changes")
    discipline = relationship("Discipline", backref="rating_changes")
    match = relationship("Match", backref="rating_changes")
```

**День 4-5: Формула расчёта ELO**

```python
# utils.py — функции расчёта рейтинга
from typing import Tuple

# Коэффициенты
K_FACTOR_BASE = 32  # Базовый K-фактор
K_FACTOR_VETERAN = 16  # Для игроков с 100+ играми
K_FACTOR_NEW = 48  # Для новых игроков (< 10 игр)

# Уровни по аналогии с FACEIT
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


def get_level_by_elo(elo: int) -> int:
    """Определить уровень по ELO"""
    for level, (min_elo, max_elo) in ELO_LEVELS.items():
        if min_elo <= elo <= max_elo:
            return level
    return 1


def get_k_factor(games_played: int) -> int:
    """Определить K-фактор по опыту игрока"""
    if games_played < 10:
        return K_FACTOR_NEW
    elif games_played > 100:
        return K_FACTOR_VETERAN
    return K_FACTOR_BASE


def calculate_elo_change(
    player_elo: int,
    opponent_elo: int,
    won: bool,
    is_draw: bool = False,
    games_played: int = 0
) -> int:
    """
    Расчёт изменения ELO после матча 1v1
    
    Формула: ELO_new = ELO_old + K * (Actual - Expected)
    Expected = 1 / (1 + 10 ^ ((Opponent_ELO - Player_ELO) / 400))
    """
    if is_draw:
        actual_score = 0.5
    elif won:
        actual_score = 1.0
    else:
        actual_score = 0.0
    
    # Ожидаемый счёт
    expected_score = 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))
    
    # K-фактор
    k = get_k_factor(games_played)
    
    # Изменение
    change = k * (actual_score - expected_score)
    
    # Бонус за победу против более сильного
    if won and opponent_elo > player_elo + 200:
        change += 5
    
    return int(round(change))


def calculate_team_elo_change(
    team_avg_elo: int,
    opponent_avg_elo: int,
    won: bool,
    is_draw: bool = False,
    team_games_avg: int = 0
) -> int:
    """Расчёт изменения ELO для командных игр (5v5)"""
    # Для командных игр уменьшаем влияние одного матча
    base_change = calculate_elo_change(
        team_avg_elo, opponent_avg_elo, won, is_draw, team_games_avg
    )
    # Делим на количество игроков (5)
    return base_change // 5


def update_player_rating(
    db: Session,
    user_id: int,
    discipline_id: int,
    elo_change: int,
    won: bool,
    is_draw: bool = False,
    match_id: int = None
) -> PlayerRating:
    """Обновление рейтинга игрока после матча"""
    from sqlalchemy import func
    
    rating = db.query(PlayerRating).filter(
        PlayerRating.user_id == user_id,
        PlayerRating.discipline_id == discipline_id
    ).first()
    
    if not rating:
        rating = PlayerRating(
            user_id=user_id,
            discipline_id=discipline_id,
            elo=1000,
            level=1
        )
        db.add(rating)
        db.flush()  # Чтобы получить ID
    
    # Сохраняем состояние до изменения
    elo_before = rating.elo
    
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
    
    # Создаём запись истории
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
    
    db.commit()
    db.refresh(rating)
    return rating
```

**День 6-7: API endpoints**

```python
# api.py — новые endpoints для рейтинга
from fastapi import Query
from schemas import LeaderboardResponse, RatingHistoryResponse

@router.get("/leaderboard", response_model=LeaderboardResponse)
async def get_leaderboard(
    discipline: str,
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """Таблица лидеров по дисциплине"""
    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(404, "Дисциплина не найдена")
    
    ratings = db.query(PlayerRating).filter(
        PlayerRating.discipline_id == disc.id
    ).order_by(PlayerRating.elo.desc()).limit(limit).all()
    
    return {
        "items": ratings,
        "total": len(ratings),
        "discipline": discipline
    }


@router.get("/users/{user_id}/rating", response_model=List[PlayerRating])
async def get_user_rating(
    user_id: int,
    discipline: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Рейтинг пользователя по дисциплинам"""
    query = db.query(PlayerRating).filter(PlayerRating.user_id == user_id)
    
    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(PlayerRating.discipline_id == disc.id)
    
    return query.all()


@router.get("/users/{user_id}/rating/history", response_model=RatingHistoryResponse)
async def get_rating_history(
    user_id: int,
    discipline: str,
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    """История изменений рейтинга"""
    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(404, "Дисциплина не найдена")
    
    changes = db.query(RatingChange).filter(
        RatingChange.user_id == user_id,
        RatingChange.discipline_id == disc.id
    ).order_by(RatingChange.created_at.desc()).limit(limit).all()
    
    return {
        "items": changes,
        "total": len(changes)
    }
```

**День 8-10: Интеграция в турниры**

```python
# tournaments.py — обновление рейтинга после матча
def process_match_result(
    db: Session,
    match: Match,
    winner_id: int
):
    """Обработка результатов матча и обновление рейтинга"""
    from utils import update_player_rating, calculate_elo_change
    
    tournament = match.tournament
    team1 = match.team1
    team2 = match.team2
    
    if not team1 or not team2:
        return  # Матч с bye
    
    # Получаем игроков команд
    team1_players = db.query(TeamMember).filter(
        TeamMember.team_id == team1.team.id
    ).all()
    team2_players = db.query(TeamMember).filter(
        TeamMember.team_id == team2.team.id
    ).all()
    
    # Определяем победителя
    won_team1 = winner_id == team1.id
    
    # Для каждого игрока обновляем рейтинг
    for member in team1_players:
        if member.user_id:
            # Получаем текущий рейтинг
            rating = db.query(PlayerRating).filter(
                PlayerRating.user_id == member.user_id,
                PlayerRating.discipline_id == tournament.discipline_id
            ).first()
            
            if rating:
                # Получаем рейтинг соперника
                opponent_rating = db.query(PlayerRating).filter(
                    PlayerRating.user_id == team2_players[0].user_id if team2_players else None,
                    PlayerRating.discipline_id == tournament.discipline_id
                ).first()
                
                if opponent_rating:
                    elo_change = calculate_elo_change(
                        rating.elo,
                        opponent_rating.elo,
                        won=won_team1,
                        games_played=rating.games_played
                    )
                    update_player_rating(
                        db, member.user_id, tournament.discipline_id,
                        elo_change, won=won_team1, match_id=match.id
                    )
    
    # Аналогично для team2
    for member in team2_players:
        if member.user_id:
            rating = db.query(PlayerRating).filter(
                PlayerRating.user_id == member.user_id,
                PlayerRating.discipline_id == tournament.discipline_id
            ).first()
            
            if rating:
                opponent_rating = db.query(PlayerRating).filter(
                    PlayerRating.user_id == team1_players[0].user_id if team1_players else None,
                    PlayerRating.discipline_id == tournament.discipline_id
                ).first()
                
                if opponent_rating:
                    elo_change = calculate_elo_change(
                        rating.elo,
                        opponent_rating.elo,
                        won=not won_team1,
                        games_played=rating.games_played
                    )
                    update_player_rating(
                        db, member.user_id, tournament.discipline_id,
                        elo_change, won=not won_team1, match_id=match.id
                    )
```

**День 11-14: UI для рейтинга**

```html
<!-- templates/includes/rating_card.html -->
<div class="rating-card">
    <h3>📊 Рейтинг</h3>
    
    {% for rating in user.ratings %}
    <div class="discipline-rating">
        <div class="discipline-header">
            <img src="{{ rating.discipline.icon }}" alt="{{ rating.discipline.name }}">
            <span>{{ rating.discipline.name }}</span>
        </div>
        
        <div class="rating-main">
            <div class="elo-display">
                <span class="elo-value">{{ rating.elo }}</span>
                <span class="level-badge level-{{ rating.level }}">
                    Lvl {{ rating.level }}
                </span>
            </div>
            
            <div class="rating-progress">
                <div class="progress-bar" 
                     style="width: {{ (rating.elo % 200) / 2 }}%">
                </div>
            </div>
        </div>
        
        <div class="rating-stats">
            <span>{{ rating.wins }}W - {{ rating.losses }}L</span>
            <span>{{ "%.1f"|format(rating.wins / rating.games_played * 100 if rating.games_played > 0 else 0) }}% WR</span>
        </div>
        
        <a href="/leaderboard/{{ rating.discipline.slug }}" class="view-leaderboard">
            Таблица лидеров →
        </a>
    </div>
    {% endfor %}
</div>
```

```css
/* static/style.css — стили для рейтинга */
.rating-card {
    background: var(--bg-card);
    border-radius: 12px;
    padding: 24px;
    margin-bottom: 24px;
}

.discipline-rating {
    background: var(--bg-secondary);
    border-radius: 8px;
    padding: 16px;
    margin-bottom: 16px;
}

.discipline-header {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 12px;
}

.discipline-header img {
    width: 32px;
    height: 32px;
}

.elo-display {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-bottom: 8px;
}

.elo-value {
    font-size: 32px;
    font-weight: 700;
    color: var(--accent-cyan);
}

.level-badge {
    background: linear-gradient(135deg, #00f0ff, #3a86ff);
    color: var(--bg-primary);
    padding: 4px 12px;
    border-radius: 16px;
    font-weight: 700;
    font-size: 14px;
}

.rating-progress {
    background: var(--bg-secondary);
    height: 8px;
    border-radius: 4px;
    overflow: hidden;
    margin-bottom: 12px;
}

.progress-bar {
    background: linear-gradient(90deg, #00f0ff, #3a86ff);
    height: 100%;
    transition: width 0.3s;
}

.rating-stats {
    display: flex;
    gap: 16px;
    font-size: 14px;
    color: var(--text-secondary);
}

.view-leaderboard {
    display: block;
    margin-top: 12px;
    color: var(--accent-cyan);
    text-decoration: none;
    font-size: 14px;
}
```

#### Критерии завершения

- [ ] Модель `PlayerRating` создана и мигрирована
- [ ] Модель `RatingChange` для истории
- [ ] Формула ELO работает корректно
- [ ] API `/api/v1/leaderboard` возвращает топ-50
- [ ] API `/api/v1/users/{id}/rating` работает
- [ ] Страница `/leaderboard/{discipline}` отображает таблицу
- [ ] В профиле виден рейтинг по дисциплинам
- [ ] Рейтинг обновляется после матчей

---

### 1.2 Визуализация турнирных сеток (Недели 3-4)

**Цель:** Создать интерактивный Bracket UI для Single/Double Elimination

#### Задачи

**День 1-3: API для bracket данных**

```python
# api.py — endpoint для данных сетки
from typing import List, Dict, Any

@router.get("/tournaments/{tournament_id}/bracket")
async def get_tournament_bracket(
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """Получить данные для отрисовки турнирной сетки"""
    tournament = db.query(Tournament).filter(
        Tournament.id == tournament_id
    ).options(
        joinedload(Tournament.discipline),
        joinedload(Tournament.participations).joinedload(TournamentParticipation.team)
    ).first()
    
    if not tournament:
        raise HTTPException(404, "Турнир не найден")
    
    # Получаем матчи
    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id
    ).options(
        joinedload(Match.team1).joinedload(TournamentParticipation.team),
        joinedload(Match.team2).joinedload(TournamentParticipation.team),
        joinedload(Match.winner).joinedload(TournamentParticipation.team)
    ).order_by(Match.round, Match.match_order).all()
    
    # Формируем структуру для frontend
    bracket_data = {
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "format": tournament.format,
            "status": tournament.status,
            "discipline": tournament.discipline.name if tournament.discipline else None
        },
        "rounds": []
    }
    
    # Группируем матчи по раундам
    current_round = None
    round_data = None
    
    for match in matches:
        if match.round != current_round:
            if round_data:
                bracket_data["rounds"].append(round_data)
            
            current_round = match.round
            round_data = {
                "name": current_round,
                "matches": []
            }
        
        round_data["matches"].append({
            "id": match.id,
            "team1": {
                "id": match.team1.id if match.team1 else None,
                "name": match.team1.team.name if match.team1 and match.team1.team else "TBD",
                "score": match.team1_score,
                "logo": match.team1.team.logo_url if match.team1 and match.team1.team else None
            } if match.team1 else None,
            "team2": {
                "id": match.team2.id if match.team2 else None,
                "name": match.team2.team.name if match.team2 and match.team2.team else "TBD",
                "score": match.team2_score,
                "logo": match.team2.team.logo_url if match.team2 and match.team2.team else None
            } if match.team2 else None,
            "winner_id": match.winner.id if match.winner else None,
            "status": match.status,
            "next_match_id": match.next_match_id,
            "scheduled_at": match.scheduled_at.isoformat() if match.scheduled_at else None
        })
    
    if round_data:
        bracket_data["rounds"].append(round_data)
    
    return bracket_data
```

**День 4-7: Bracket компонент (SVG)**

```html
<!-- templates/includes/bracket.html -->
<div class="tournament-bracket" data-tournament-id="{{ tournament.id }}">
    <div class="bracket-controls">
        <button class="bracket-zoom" data-zoom="in">+</button>
        <button class="bracket-zoom" data-zoom="out">−</button>
        <button class="bracket-reset">Сброс</button>
    </div>
    
    <div class="bracket-container">
        <!-- Rounds will be rendered here -->
    </div>
</div>

<script>
class BracketViewer {
    constructor(containerId) {
        this.container = document.querySelector(containerId);
        this.tournamentId = this.container.dataset.tournamentId;
        this.zoom = 1;
        this.loadBracket();
    }
    
    async loadBracket() {
        try {
            const response = await fetch(`/api/v1/tournaments/${this.tournamentId}/bracket`);
            const data = await response.json();
            this.render(data);
            this.attachEventListeners();
        } catch (error) {
            console.error('Failed to load bracket:', error);
        }
    }
    
    render(data) {
        const container = this.container.querySelector('.bracket-container');
        container.innerHTML = '';
        
        data.rounds.forEach((round, roundIndex) => {
            const roundEl = document.createElement('div');
            roundEl.className = 'bracket-round';
            roundEl.innerHTML = `
                <h4 class="round-name">${round.name}</h4>
                <div class="round-matches"></div>
            `;
            
            const matchesContainer = roundEl.querySelector('.round-matches');
            
            round.matches.forEach(match => {
                const matchEl = document.createElement('div');
                matchEl.className = `match ${match.status}`;
                matchEl.dataset.matchId = match.id;
                
                matchEl.innerHTML = `
                    <div class="match-team team-1 ${match.winner_id === match.team1?.id ? 'winner' : ''}">
                        <span class="team-name">${match.team1?.name || 'TBD'}</span>
                        <span class="team-score">${match.team1?.score ?? '-'}</span>
                    </div>
                    <div class="match-team team-2 ${match.winner_id === match.team2?.id ? 'winner' : ''}">
                        <span class="team-name">${match.team2?.name || 'TBD'}</span>
                        <span class="team-score">${match.team2?.score ?? '-'}</span>
                    </div>
                    ${match.next_match_id ? `<div class="match-connector" data-next="${match.next_match_id}"></div>` : ''}
                `;
                
                matchesContainer.appendChild(matchEl);
            });
            
            container.appendChild(roundEl);
        });
    }
    
    attachEventListeners() {
        // Клик на матч — показать детали
        this.container.querySelectorAll('.match').forEach(match => {
            match.addEventListener('click', (e) => {
                const matchId = e.currentTarget.dataset.matchId;
                this.showMatchDetails(matchId);
            });
        });
        
        // Зум
        this.container.querySelectorAll('.bracket-zoom').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const action = e.target.dataset.zoom;
                this.zoom = action === 'in' ? this.zoom * 1.2 : this.zoom / 1.2;
                this.container.querySelector('.bracket-container').style.transform = `scale(${this.zoom})`;
            });
        });
    }
    
    async showMatchDetails(matchId) {
        // Модалка с деталями матча
        const response = await fetch(`/api/v1/matches/${matchId}`);
        const match = await response.json();
        // ... показать модалку
    }
}

// Инициализация
document.addEventListener('DOMContentLoaded', () => {
    new BracketViewer('.tournament-bracket');
    
    // Авто-обновление каждые 30 секунд
    setInterval(() => {
        bracketViewer.loadBracket();
    }, 30000);
});
</script>
```

```css
/* static/style.css — Bracket стили */
.tournament-bracket {
    background: var(--bg-card);
    border-radius: 16px;
    padding: 24px;
    overflow: hidden;
}

.bracket-controls {
    display: flex;
    gap: 12px;
    margin-bottom: 20px;
}

.bracket-zoom, .bracket-reset {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    color: var(--text-primary);
    padding: 8px 16px;
    border-radius: 6px;
    cursor: pointer;
    transition: all 0.2s;
}

.bracket-zoom:hover, .bracket-reset:hover {
    background: var(--accent-cyan);
    color: var(--bg-primary);
}

.bracket-container {
    display: flex;
    gap: 40px;
    overflow-x: auto;
    padding: 20px;
    transform-origin: left center;
    transition: transform 0.3s;
}

.bracket-round {
    display: flex;
    flex-direction: column;
    gap: 20px;
    min-width: 220px;
}

.round-name {
    text-align: center;
    color: var(--accent-cyan);
    font-weight: 600;
    margin-bottom: 10px;
    font-size: 14px;
}

.round-matches {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.match {
    background: var(--bg-secondary);
    border: 1px solid var(--border-color);
    border-radius: 8px;
    padding: 12px;
    min-width: 200px;
    position: relative;
    cursor: pointer;
    transition: all 0.2s;
}

.match:hover {
    border-color: var(--accent-cyan);
    transform: translateY(-2px);
}

.match.completed {
    opacity: 0.8;
}

.match.pending {
    border-style: dashed;
}

.match-team {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
}

.match-team.winner {
    color: #34d399;
    font-weight: 600;
}

.team-name {
    font-size: 13px;
}

.team-score {
    background: var(--bg-card);
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: 700;
    font-size: 14px;
}

.match-connector {
    position: absolute;
    right: -40px;
    top: 50%;
    width: 40px;
    height: 2px;
    background: var(--border-color);
}

.match-connector::after {
    content: '';
    position: absolute;
    right: 0;
    top: -100%;
    width: 2px;
    height: 200%;
    background: var(--border-color);
}

/* Адаптив */
@media (max-width: 768px) {
    .bracket-container {
        gap: 20px;
    }
    
    .bracket-round {
        min-width: 180px;
    }
    
    .match {
        min-width: 160px;
    }
}
```

**День 8-10: Генерация bracket для турнира**

```python
# tournaments.py — генерация сетки
import math
import random

def generate_single_elimination_bracket(db: Session, tournament_id: int):
    """Создать сетку single elimination для турнира"""
    tournament = db.query(Tournament).get(tournament_id)
    participations = [p for p in tournament.participations if p.is_confirmed]
    
    num_teams = len(participations)
    
    # Дополняем до степени двойки (bye)
    next_power = 1
    while next_power < num_teams:
        next_power *= 2
    
    # Добавляем bye (автоматический проход)
    while len(participations) < next_power:
        participations.append(None)
    
    # Перемешиваем для случайного посева
    random.shuffle(participations)
    
    # Создаём первый раунд
    num_first_round = len(participations) // 2
    matches_created = []
    
    for i in range(num_first_round):
        team1 = participations[i * 2]
        team2 = participations[i * 2 + 1]
        
        match = Match(
            tournament_id=tournament_id,
            team1_id=team1.id if team1 else None,
            team2_id=team2.id if team2 else None,
            round=f"Раунд {int(math.log2(num_first_round))}",
            match_order=i,
            status="pending" if team1 and team2 else "completed"
        )
        
        # Если bye, автоматически проходим
        if team1 and not team2:
            match.winner_id = team1.id
            match.team1_score = 1
            match.team2_score = 0
            match.status = "completed"
        elif team2 and not team1:
            match.winner_id = team2.id
            match.team1_score = 0
            match.team2_score = 1
            match.status = "completed"
        
        db.add(match)
        matches_created.append(match)
    
    # Создаём последующие раунды
    current_round_matches = matches_created
    round_num = int(math.log2(num_first_round))
    
    while len(current_round_matches) > 1:
        round_num -= 1
        next_round_matches = []
        
        for i in range(0, len(current_round_matches), 2):
            match1 = current_round_matches[i]
            match2 = current_round_matches[i + 1] if i + 1 < len(current_round_matches) else None
            
            next_match = Match(
                tournament_id=tournament_id,
                round=f"Раунд {round_num}" if round_num > 1 else "Финал",
                match_order=i // 2,
                status="pending"
            )
            
            db.add(next_match)
            
            # Связываем с предыдущими матчами
            match1.next_match_id = next_match.id
            if match2:
                match2.next_match_id = next_match.id
                db.add(match2)
            
            next_round_matches.append(next_match)
        
        current_round_matches = next_round_matches
        db.commit()
```

#### Критерии завершения

- [ ] API `/api/v1/tournaments/{id}/bracket` работает
- [ ] Генерация Single Elimination bracket работает
- [ ] Страница турнира отображает сетку
- [ ] Bracket интерактивный (клик → детали)
- [ ] Авто-обновление bracket при изменении результатов
- [ ] Поддержка Double Elimination (опционально)

---

## 🎮 ФАЗА 2: ВАЖНЫЕ УЛУЧШЕНИЯ (4-6 недель)

### 2.1 Автоматический матчмейкинг (Недели 1-3)

**Цель:** Реализовать автоматический подбор игроков для игр 1v1 или 5v5 по ELO ±200

#### Задачи

**День 1-3: Модель очереди**

```python
# models.py
class MatchmakingQueue(Base):
    __tablename__ = "matchmaking_queue"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)
    
    # Параметры поиска
    game_type = Column(String(20), default="1v1")  # 1v1, 2v2, 5v5
    elo = Column(Integer, nullable=False)
    elo_min = Column(Integer)  # Минимальный ELO для поиска
    elo_max = Column(Integer)  # Максимальный ELO для поиска
    
    # Статус
    status = Column(String(20), default="waiting")  # waiting, found, cancelled, timeout
    queued_at = Column(DateTime, default=datetime.utcnow, index=True)
    found_at = Column(DateTime, nullable=True)
    
    # Ссылка на созданный матч
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    
    user = relationship("User", backref="mm_queues")
    discipline = relationship("Discipline", backref="mm_queues")
    match = relationship("Match", backref="mm_queue")
```

**День 4-10: Алгоритм подбора**

```python
# matchmaking.py
import asyncio
from datetime import datetime, timedelta
from typing import List, Optional

class MatchmakingService:
    def __init__(self, db: Session):
        self.db = db
        self.BASE_ELO_RANGE = 200
        self.MAX_ELO_RANGE = 800
        self.MAX_WAIT_TIME = timedelta(minutes=5)
        self.ELO_EXPANSION_INTERVAL = timedelta(minutes=1)
        self.TEAM_SIZES = {"1v1": 1, "2v2": 2, "5v5": 5}
    
    async def start_matchmaking(self, queue_entry: MatchmakingQueue):
        """Запуск процесса поиска матча"""
        start_time = datetime.utcnow()
        elo_range = self.BASE_ELO_RANGE
        
        while True:
            # Ждём
            await asyncio.sleep(2)
            
            # Проверяем, не отменил ли пользователь
            self.db.refresh(queue_entry)
            if queue_entry.status != "waiting":
                return
            
            # Находим кандидатов
            candidates = self.find_candidates(queue_entry, elo_range)
            
            # Проверяем, достаточно ли игроков
            needed_players = self.TEAM_SIZES.get(queue_entry.game_type, 1)
            
            if len(candidates) >= needed_players - 1:
                # Создаём матч
                match = await self.create_match(
                    queue_entry,
                    candidates[:needed_players - 1]
                )
                
                if match:
                    queue_entry.status = "found"
                    queue_entry.match_id = match.id
                    queue_entry.found_at = datetime.utcnow()
                    self.db.commit()
                    
                    # Уведомляем игроков
                    await self.notify_players(match)
                    return
            
            # Расширяем диапазон ELO со временем
            elapsed = datetime.utcnow() - start_time
            
            if elapsed > self.MAX_WAIT_TIME:
                # Таймаут
                queue_entry.status = "timeout"
                self.db.commit()
                await self.notify_timeout(queue_entry)
                return
            
            # Увеличиваем диапазон ELO каждую минуту
            elo_range = min(
                self.MAX_ELO_RANGE,
                self.BASE_ELO_RANGE + (elapsed.seconds // 60) * self.BASE_ELO_RANGE
            )
    
    def find_candidates(
        self,
        queue_entry: MatchmakingQueue,
        elo_range: int
    ) -> List[MatchmakingQueue]:
        """Найти кандидатов для матча"""
        return self.db.query(MatchmakingQueue).filter(
            MatchmakingQueue.discipline_id == queue_entry.discipline_id,
            MatchmakingQueue.game_type == queue_entry.game_type,
            MatchmakingQueue.status == "waiting",
            MatchmakingQueue.id != queue_entry.id,
            MatchmakingQueue.elo.between(
                queue_entry.elo - elo_range,
                queue_entry.elo + elo_range
            ),
            MatchmakingQueue.queued_at <= datetime.utcnow()
        ).order_by(
            MatchmakingQueue.queued_at
        ).limit(10).all()
    
    async def create_match(
        self,
        queue_entry: MatchmakingQueue,
        candidates: List[MatchmakingQueue]
    ) -> Optional[Match]:
        """Создать матч из очереди"""
        try:
            tournament = self._get_or_create_mm_tournament(queue_entry.discipline_id)
            
            # Создаём TournamentParticipation для каждого игрока
            participations = []
            for q in [queue_entry] + candidates:
                participation = TournamentParticipation(
                    tournament_id=tournament.id,
                    user_id=q.user_id,
                    is_confirmed=True
                )
                self.db.add(participation)
                participations.append(participation)
            
            self.db.flush()
            
            # Создаём матч
            match = Match(
                tournament_id=tournament.id,
                team1_id=participations[0].id,
                team2_id=participations[1].id if len(participations) > 1 else None,
                round="1v1 Match",
                match_order=0,
                status="pending",
                scheduled_at=datetime.utcnow() + timedelta(minutes=5)
            )
            self.db.add(match)
            self.db.commit()
            
            return match
            
        except Exception as e:
            self.db.rollback()
            print(f"Match creation error: {e}")
            return None
    
    def _get_or_create_mm_tournament(self, discipline_id: int) -> Tournament:
        """Получить или создать турнир для матчмейкинга"""
        tournament = self.db.query(Tournament).filter(
            Tournament.name == "Matchmaking",
            Tournament.discipline_id == discipline_id,
            Tournament.status == "active"
        ).first()
        
        if not tournament:
            tournament = Tournament(
                name="Matchmaking",
                discipline_id=discipline_id,
                description="Автоматические матчи",
                max_teams=1000,
                status="active",
                format="1v1",
                is_online=True
            )
            self.db.add(tournament)
            self.db.commit()
            self.db.refresh(tournament)
        
        return tournament
    
    async def notify_players(self, match: Match):
        """Уведомить игроков о найденном матче"""
        # TODO: Отправить push/email/Discord уведомление
        pass
    
    async def notify_timeout(self, queue_entry: MatchmakingQueue):
        """Уведомить о таймауте поиска"""
        # TODO: Отправить уведомление
        pass


# Background task
async def matchmaking_worker():
    """Фоновая задача обработки очереди"""
    while True:
        db = SessionLocal()
        try:
            queues = db.query(MatchmakingQueue).filter(
                MatchmakingQueue.status == "waiting"
            ).all()
            
            for queue in queues:
                asyncio.create_task(MatchmakingService(db).start_matchmaking(queue))
            
            await asyncio.sleep(5)
        finally:
            db.close()
```

**День 11-14: API и UI**

```python
# api.py
@router.post("/matchmaking/queue")
async def join_queue(
    discipline: str,
    game_type: str = "1v1",
    request: Request,
    db: Session = Depends(get_db)
):
    """Встать в очередь матчмейкинга"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(401, "Требуется авторизация")
    
    disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
    if not disc:
        raise HTTPException(404, "Дисциплина не найдена")
    
    # Получаем рейтинг пользователя
    rating = db.query(PlayerRating).filter(
        PlayerRating.user_id == user.id,
        PlayerRating.discipline_id == disc.id
    ).first()
    
    if not rating:
        rating = PlayerRating(user_id=user.id, discipline_id=disc.id)
        db.add(rating)
        db.commit()
    
    # Проверяем, не в очереди ли уже
    existing = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status == "waiting"
    ).first()
    if existing:
        raise HTTPException(400, "Вы уже в очереди")
    
    queue_entry = MatchmakingQueue(
        user_id=user.id,
        discipline_id=disc.id,
        game_type=game_type,
        elo=rating.elo
    )
    db.add(queue_entry)
    db.commit()
    
    # Запускаем поиск матча в фоне
    asyncio.create_task(MatchmakingService(db).start_matchmaking(queue_entry))
    
    return {"status": "queued", "message": "Поиск матча начат"}


@router.get("/matchmaking/status")
async def get_queue_status(
    request: Request,
    db: Session = Depends(get_db)
):
    """Статус очереди пользователя"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(401, "Требуется авторизация")
    
    queue_entry = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status == "waiting"
    ).first()
    
    if not queue_entry:
        return {"status": "not_queued"}
    
    wait_time = (datetime.utcnow() - queue_entry.queued_at).total_seconds()
    return {
        "status": "queued",
        "wait_time": int(wait_time),
        "game_type": queue_entry.game_type,
        "elo": queue_entry.elo,
        "estimated_time": estimate_wait_time(queue_entry)
    }
```

#### Критерии завершения

- [ ] Модель `MatchmakingQueue` создана
- [ ] Алгоритм подбора работает
- [ ] Фоновая задача обрабатывает очередь
- [ ] API endpoints работают
- [ ] UI для очереди и поиска
- [ ] Уведомления о матче

---

### 2.2 Discord-интеграция (Недели 4-5)

**Цель:** Интеграция с Discord для уведомлений и авторизации

#### Задачи

1. OAuth2 авторизация через Discord
2. Привязка Discord ID к пользователю
3. Webhooks для уведомлений
4. Бот для турниров

```python
# auth.py — Discord OAuth2
from httpx import AsyncClient

@router.get("/auth/discord")
async def discord_login():
    """Перенаправление на Discord OAuth"""
    discord_auth_url = (
        "https://discord.com/api/oauth2/authorize"
        f"?client_id={settings.discord_client_id}"
        "&redirect_uri=http://localhost:8000/auth/discord/callback"
        "&response_type=code"
        "&scope=identify+email+guilds"
    )
    return RedirectResponse(discord_auth_url)


@router.get("/auth/discord/callback")
async def discord_callback(code: str, db: Session = Depends(get_db)):
    """Callback от Discord OAuth"""
    async with AsyncClient() as client:
        # Получаем токен
        token_response = await client.post(
            "https://discord.com/api/oauth2/token",
            data={
                "client_id": settings.discord_client_id,
                "client_secret": settings.discord_client_secret,
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "http://localhost:8000/auth/discord/callback"
            }
        )
        token_data = token_response.json()
        access_token = token_data["access_token"]
        
        # Получаем данные пользователя
        user_response = await client.get(
            "https://discord.com/api/users/@me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        discord_user = user_response.json()
        
        # Привязываем к существующему пользователю или создаём нового
        user = db.query(User).filter(
            User.email == discord_user.get("email")
        ).first()
        
        if not user:
            # Создаём нового
            user = User(
                email=discord_user.get("email"),
                username=discord_user.get("username"),
                hashed_password=get_password_hash(secrets.token_urlsafe(32)),
                is_verified=True,
                is_active=True
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Сохраняем Discord ID
        user.discord_id = discord_user.get("id")
        db.commit()
        
        # Логин
        access_token = create_access_token(data={"sub": user.email})
        response = RedirectResponse("/dashboard", status_code=303)
        response.set_cookie(key="access_token", value=f"Bearer {access_token}")
        return response
```

#### Критерии завершения

- [ ] Discord OAuth2 работает
- [ ] Привязка Discord ID к пользователю
- [ ] Webhooks для уведомлений о турнирах
- [ ] Бот для создания каналов

---

### 2.3 Расширенная статистика (Недели 5-6)

**Цель:** Детальная статистика игроков с графиками

#### Задачи

1. Модель `MatchHistory`
2. Агрегация статистики
3. Графики Chart.js
4. Экспорт CSV

```python
# models.py
class MatchHistory(Base):
    """История матчей игрока"""
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False)
    
    # Результат
    result = Column(String(20))  # win, loss, draw
    score_team = Column(Integer)
    score_opponent = Column(Integer)
    
    # Статистика (для CS2/Dota 2)
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    damage = Column(Integer, default=0)
    
    # ELO
    elo_before = Column(Integer)
    elo_after = Column(Integer)
    elo_change = Column(Integer)
    
    played_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", backref="match_history")
    match = relationship("Match", backref="history")
    discipline = relationship("Discipline", backref="match_history")
```

#### Критерии завершения

- [ ] Модель `MatchHistory` создана
- [ ] Статистика собирается после матчей
- [ ] Графики в профиле (Chart.js)
- [ ] Экспорт статистики CSV

---

## 💰 ФАЗА 3: МОНЕТИЗАЦИЯ (4-6 недель)

### 3.1 Premium-подписка

**Уровни:**
- **Free:** Базовые функции
- **Pro ($3/мес):** Расширенная статистика, приоритет в матчмейкинге, вето карт
- **Ultimate ($7/мес):** Персональный тренер, эксклюзивные турниры

```python
# models.py
class Subscription(Base):
    __tablename__ = "subscriptions"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    tier = Column(String(20), default="free")  # free, pro, ultimate
    status = Column(String(20), default="active")  # active, cancelled, expired
    
    started_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    payment_provider = Column(String(50))  # stripe, yookassa
    payment_id = Column(String(100))
    
    user = relationship("User", backref="subscriptions")
```

---

## 📊 ЧАСТЬ 6: ДОРОЖНАЯ КАРТА

```
Апрель 2026 ─────────────────────────────────────────────►
    │
    ├─ Недели 1-2:  Система ELO + Leaderboard
    ├─ Недели 3-4:  Bracket UI
    ├─ Недели 5-7:  Матчмейкинг
    ├─ Недели 8-9:  Discord-интеграция
    ├─ Недели 10-12: Статистика + Графики
    │
    ├─ Недели 13-16: Premium-подписка
    ├─ Недели 17-20: Мобильное приложение (React Native)
    └─ Недели 21-24: Античит (базовый)
```

---

## 📋 ЧАСТЬ 7: ЧЕК-ЛИСТ ДЛЯ РАЗРАБОТКИ

### Фаза 1: Критические улучшения

- [ ] Модель `PlayerRating` создана
- [ ] Модель `RatingChange` для истории
- [ ] Формула ELO реализована
- [ ] API `/api/v1/leaderboard` работает
- [ ] Страница `/leaderboard/{discipline}` создана
- [ ] Рейтинг отображается в профиле
- [ ] Рейтинг обновляется после матчей
- [ ] API `/api/v1/tournaments/{id}/bracket` работает
- [ ] Bracket UI реализован (SVG)
- [ ] Генерация Single Elimination работает
- [ ] Модель `MatchmakingQueue` создана
- [ ] Алгоритм подбора игроков работает
- [ ] Фоновая задача matchmaking_worker запущена

### Фаза 2: Важные улучшения

- [ ] Discord OAuth2 настроен
- [ ] Привязка Discord ID работает
- [ ] Webhooks для уведомлений
- [ ] Модель `MatchHistory` создана
- [ ] Графики Chart.js в профиле
- [ ] Экспорт статистики CSV

### Фаза 3: Монетизация

- [ ] Модель `Subscription` создана
- [ ] Платёжная интеграция (YooKassa/Stripe)
- [ ] Premium-функции реализованы
- [ ] Страница подписки

---

## 🏁 ЗАКЛЮЧЕНИЕ

### Текущее состояние EasyCyberPro

**Сильные стороны:**
- ✅ Рабочая аутентификация и профили
- ✅ Тренерская система (уникальная фича!)
- ✅ Турниры с заявками
- ✅ Админ-панель
- ✅ REST API
- ✅ Email-рассылки

**Критические недостатки:**
- ❌ Нет матчмейкинга
- ❌ Нет системы ELO
- ❌ Нет визуализации bracket
- ❌ Нет интеграции с играми

### Уникальное торговое предложение (УТП)

1. **Тренерская система** — Единственная платформа с тренер-ученик
2. **Локализация** — Русский интерфейс для СНГ
3. **Простота** — Лёгкое развёртывание
4. **Образовательный фокус** — Развитие игроков, а не только турниры

### Рекомендации

**Для MVP (следующие 4-6 недель):**
1. Система ELO + Leaderboard
2. Bracket UI
3. Базовый матчмейкинг

**Для полноценного запуска (3 месяца):**
4. Discord-интеграция
5. Расширенная статистика
6. Интеграция с играми (Steam API)

**Для масштабирования (6 месяцев):**
7. Мобильное приложение
8. Premium-подписка
9. Античит (базовый)

### Целевая аудитория

- **Геймеры СНГ** — 18-35 лет, Dota 2/CS2
- **Начинающие игроки** — Хотят развиваться
- **Любительские команды** — Ищут турниры
- **Тренеры** — Хотят учеников

### Конкурентные преимущества

| EasyCyberPro | FACEIT | Battlefy |
|--------------|--------|----------|
| Тренерская система | ❌ | ❌ |
| Локализация RU | ❌ | ❌ |
| Простота | ❌ Сложный | ❌ Сложный |
| Образовательный фокус | ❌ | ❌ |

**Миссия:** Создать платформу для развития киберспортсменов в СНГ, а не только для соревнований.

---

**Документ создан:** 1 апреля 2026 г.  
**Следующий пересмотр:** После завершения Фазы 1
