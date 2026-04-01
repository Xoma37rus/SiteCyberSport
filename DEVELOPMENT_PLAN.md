# 🚀 План развития EasyCyberPro: Догнать и превзойти конкурентов

## 📅 Обзор плана

| Фаза | Длительность | Фокус | Критерий успеха |
|------|--------------|-------|-----------------|
| **Фаза 1** | 2 недели | Рейтинг ELO + Leaderboard | Игроки видят свой рейтинг и прогресс |
| **Фаза 2** | 2 недели |Bracket UI (визуализация сеток) | Турниры отображаются с интерактивной сеткой |
| **Фаза 3** | 3 недели | Матчмейкинг | Автоматический подбор игр за < 3 мин |
| **Фаза 4** | 2 недели | Античит + Верификация | Снижение фейковых результатов на 90% |
| **Фаза 5** | 2 недели | Интеграция Steam | Авто-сбор статистики для CS2/Dota 2 |
| **Фаза 6** | 2 недели | Расширенная статистика | Графики, аналитика, экспорт |

**Общая длительность:** 13 недель (~3 месяца)  
**Цель:** Достичь паритета с FACEIT/Battlefy по ключевым функциям

---

## 🔥 ФАЗА 1: Рейтинговая система ELO (Недели 1-2)

### Цель
Внедрить рейтинговую систему по аналогии с FACEIT (10 уровней, ELO 0-2500+)

### Задачи

#### Неделя 1: База данных и логика

**День 1-2: Модель рейтинга**
```python
# models.py - новая модель
class PlayerRating(Base):
    __tablename__ = "player_ratings"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False, index=True)
    
    elo = Column(Integer, default=1000, index=True)  # Стартовый ELO
    level = Column(Integer, default=1, index=True)   # Уровень 1-10
    games_played = Column(Integer, default=0)
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    
    # Прогресс
    peak_elo = Column(Integer, default=1000)
    last_game_at = Column(DateTime, nullable=True)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="ratings")
    discipline = relationship("Discipline", backref="ratings")
    
    __table_args__ = (
        UniqueConstraint('user_id', 'discipline_id', name='uq_user_discipline'),
    )
```

**День 3-4: Формула расчёта ELO**
```python
# utils.py - функции расчёта
K_FACTOR = 32  # Коэффициент изменения
BASE_ELO = 1000

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
    for level, (min_elo, max_elo) in ELO_LEVELS.items():
        if min_elo <= elo <= max_elo:
            return level
    return 1

def calculate_elo_change(
    player_elo: int,
    opponent_elo: int,
    won: bool,
    is_team_game: bool = False
) -> int:
    """Расчёт изменения ELO после матча"""
    expected = 1 / (1 + 10 ** ((opponent_elo - player_elo) / 400))
    actual = 1 if won else 0
    
    change = K_FACTOR * (actual - expected)
    
    # Бонус за победу
    if won:
        change += 5
    
    # Для командных игр усредняем
    if is_team_game:
        change = change / 5  # 5 игроков в команде
    
    return int(round(change))

def update_player_rating(
    db: Session,
    user_id: int,
    discipline_id: int,
    elo_change: int
) -> PlayerRating:
    """Обновление рейтинга игрока"""
    rating = db.query(PlayerRating).filter(
        PlayerRating.user_id == user_id,
        PlayerRating.discipline_id == discipline_id
    ).first()
    
    if not rating:
        rating = PlayerRating(user_id=user_id, discipline_id=discipline_id)
        db.add(rating)
    
    rating.elo = max(0, rating.elo + elo_change)  # Не ниже 0
    rating.level = get_level_by_elo(rating.elo)
    rating.games_played += 1
    rating.last_game_at = datetime.utcnow()
    
    if elo_change > 0:
        rating.wins += 1
        rating.peak_elo = max(rating.peak_elo, rating.elo)
    else:
        rating.losses += 1
    
    db.commit()
    db.refresh(rating)
    return rating
```

**День 5: Инициализация рейтингов**
```python
# seed_ratings.py - скрипт для существующих пользователей
def init_all_ratings():
    db = SessionLocal()
    try:
        disciplines = db.query(Discipline).filter(Discipline.is_active == True).all()
        users = db.query(User).filter(User.is_active == True).all()
        
        for user in users:
            for disc in disciplines:
                existing = db.query(PlayerRating).filter(
                    PlayerRating.user_id == user.id,
                    PlayerRating.discipline_id == disc.id
                ).first()
                if not existing:
                    rating = PlayerRating(
                        user_id=user.id,
                        discipline_id=disc.id,
                        elo=BASE_ELO,
                        level=1
                    )
                    db.add(rating)
        
        db.commit()
        print(f"Created ratings for {len(users)} users")
    finally:
        db.close()
```

---

#### Неделя 2: API и UI

**День 1-2: API endpoints**
```python
# api.py - новые endpoints
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

@router.get("/users/{user_id}/rating", response_model=RatingResponse)
async def get_user_rating(
    user_id: int,
    discipline: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Рейтинг пользователя"""
    query = db.query(PlayerRating).filter(PlayerRating.user_id == user_id)
    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(PlayerRating.discipline_id == disc.id)
    
    ratings = query.all()
    return {"items": ratings}
```

**День 3-4: Leaderboard UI**
```html
<!-- templates/leaderboard.html -->
<div class="leaderboard">
    <h1>Таблица лидеров - {{ discipline.name }}</h1>
    
    <table class="leaderboard-table">
        <thead>
            <tr>
                <th>#</th>
                <th>Игрок</th>
                <th>Уровень</th>
                <th>ELO</th>
                <th>Игры</th>
                <th>Победы</th>
                <th>Win Rate</th>
            </tr>
        </thead>
        <tbody>
            {% for rating in ratings %}
            <tr class="leaderboard-row {% if rating.user_id == current_user.id %}current-user{% endif %}">
                <td>{{ loop.index }}</td>
                <td>
                    <a href="/profile/{{ rating.user_id }}">
                        <img src="{{ rating.user.avatar_url or '/static/images/default-avatar.png' }}" 
                             class="avatar-small">
                        {{ rating.user.username }}
                    </a>
                </td>
                <td>
                    <span class="level-badge level-{{ rating.level }}">
                        {{ rating.level }}
                    </span>
                </td>
                <td class="elo">{{ rating.elo }}</td>
                <td>{{ rating.games_played }}</td>
                <td>{{ rating.wins }}</td>
                <td>{{ "%.1f"|format(rating.wins / rating.games_played * 100 if rating.games_played > 0 else 0) }}%</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</div>
```

**День 5: Интеграция в профиль**
```html
<!-- templates/profile.html - блок рейтинга -->
<div class="rating-card">
    <h3>Рейтинг</h3>
    {% for rating in user.ratings %}
    <div class="discipline-rating">
        <div class="discipline-header">
            <img src="{{ rating.discipline.icon }}" alt="{{ rating.discipline.name }}">
            <span>{{ rating.discipline.name }}</span>
        </div>
        <div class="rating-stats">
            <div class="elo-display">
                <span class="elo-value">{{ rating.elo }}</span>
                <span class="level-badge level-{{ rating.level }}">Lvl {{ rating.level }}</span>
            </div>
            <div class="rating-progress">
                <div class="progress-bar" style="width: {{ (rating.elo % 200) / 2 }}%"></div>
            </div>
            <div class="rating-details">
                <span>{{ rating.wins }}W - {{ rating.losses }}L</span>
                <span>{{ "%.1f"|format(rating.wins / rating.games_played * 100 if rating.games_played > 0 else 0) }}% WR</span>
            </div>
        </div>
    </div>
    {% endfor %}
</div>
```

---

### ✅ Критерии завершения Фазы 1

- [ ] Модель `PlayerRating` создана и мигрирована
- [ ] Формула ELO работает корректно
- [ ] API `/api/v1/leaderboard` возвращает данные
- [ ] API `/api/v1/users/{id}/rating` работает
- [ ] Страница `/leaderboard/{discipline}` отображает топ-50
- [ ] В профиле пользователя виден рейтинг
- [ ] Скрипт инициализации рейтингов работает

---

## 🏆 ФАЗА 2: Bracket UI (Недели 3-4)

### Цель
Визуализация турнирных сеток с поддержкой Single/Double Elimination

### Задачи

#### Неделя 3: Backend для bracket

**День 1-2: API для данных сетки**
```python
# api.py - bracket endpoints
@router.get("/tournaments/{tournament_id}/bracket")
async def get_tournament_bracket(
    tournament_id: int,
    db: Session = Depends(get_db)
):
    """Получить данные для отрисовки турнирной сетки"""
    tournament = db.query(Tournament).get(tournament_id)
    if not tournament:
        raise HTTPException(404, "Турнир не найден")
    
    matches = db.query(Match).filter(
        Match.tournament_id == tournament_id
    ).order_by(Match.round, Match.match_order).all()
    
    bracket_data = {
        "tournament": {
            "id": tournament.id,
            "name": tournament.name,
            "format": tournament.format,
            "status": tournament.status
        },
        "rounds": []
    }
    
    # Группируем матчи по раундам
    current_round = None
    for match in matches:
        if match.round != current_round:
            current_round = match.round
            bracket_data["rounds"].append({
                "name": current_round,
                "matches": []
            })
        
        bracket_data["rounds"][-1]["matches"].append({
            "id": match.id,
            "team1": {
                "id": match.team1_id,
                "name": match.team1.team.name if match.team1 and match.team1.team else "TBD",
                "score": match.team1_score
            } if match.team1 else None,
            "team2": {
                "id": match.team2_id,
                "name": match.team2.team.name if match.team2 and match.team2.team else "TBD",
                "score": match.team2_score
            } if match.team2 else None,
            "winner_id": match.winner_id,
            "status": match.status,
            "next_match_id": match.next_match_id
        })
    
    return bracket_data
```

**День 3-5: Генерация сетки для турнира**
```python
# tournaments.py - создание bracket
def generate_single_elimination_bracket(db: Session, tournament_id: int):
    """Создать сетку single elimination для турнира"""
    tournament = db.query(Tournament).get(tournament_id)
    participations = [p for p in tournament.participations if p.is_confirmed]
    
    # Дополняем до степени двойки (bye)
    num_teams = len(participations)
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
            
            # Связываем с предыдущими матчами
            match1.next_match_id = next_match.id
            if match2:
                match2.next_match_id = next_match.id
            
            db.add(next_match)
            next_round_matches.append(next_match)
        
        current_round_matches = next_round_matches
    
    db.commit()
```

---

#### Неделя 4: Frontend визуализация

**День 1-3: SVG/CSS bracket component**
```html
<!-- templates/includes/bracket.html -->
<div class="tournament-bracket" data-tournament-id="{{ tournament.id }}">
    <div class="bracket-container">
        {% for round in bracket.rounds %}
        <div class="bracket-round">
            <h4 class="round-name">{{ round.name }}</h4>
            <div class="round-matches">
                {% for match in round.matches %}
                <div class="match" data-match-id="{{ match.id }}">
                    <div class="match-team team-1 {% if match.winner_id == match.team1.id %}winner{% endif %}">
                        <span class="team-name">{{ match.team1.name if match.team1 else 'TBD' }}</span>
                        <span class="team-score">{{ match.team1.score if match.team1 else '-' }}</span>
                    </div>
                    <div class="match-team team-2 {% if match.winner_id == match.team2.id %}winner{% endif %}">
                        <span class="team-name">{{ match.team2.name if match.team2 else 'TBD' }}</span>
                        <span class="team-score">{{ match.team2.score if match.team2 else '-' }}</span>
                    </div>
                    {% if match.next_match_id %}
                    <div class="match-connector" data-next="{{ match.next_match_id }}"></div>
                    {% endif %}
                </div>
                {% endfor %}
            </div>
        </div>
        {% endfor %}
    </div>
</div>
```

```css
/* static/style.css - Bracket стили */
.tournament-bracket {
    overflow-x: auto;
    padding: 20px;
    background: #161b22;
    border-radius: 8px;
}

.bracket-container {
    display: flex;
    gap: 40px;
    min-width: max-content;
}

.bracket-round {
    display: flex;
    flex-direction: column;
    gap: 20px;
}

.round-name {
    text-align: center;
    color: #58a6ff;
    font-weight: 600;
    margin-bottom: 10px;
}

.round-matches {
    display: flex;
    flex-direction: column;
    gap: 16px;
}

.match {
    background: #0d1117;
    border: 1px solid #30363d;
    border-radius: 6px;
    padding: 12px;
    min-width: 200px;
    position: relative;
    transition: all 0.2s;
}

.match:hover {
    border-color: #00f0ff;
    cursor: pointer;
}

.match-team {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 6px 0;
}

.match-team.winner {
    color: #3fb950;
    font-weight: 600;
}

.team-score {
    background: #21262d;
    padding: 2px 8px;
    border-radius: 4px;
    font-weight: bold;
}

.match-connector {
    position: absolute;
    right: -40px;
    top: 50%;
    width: 40px;
    height: 2px;
    background: #30363d;
}

.match-connector::after {
    content: '';
    position: absolute;
    right: 0;
    top: -100%;
    width: 2px;
    height: 200%;
    background: #30363d;
}
```

**День 4-5: Интерактивность и обновление**
```javascript
// static/bracket.js
class BracketViewer {
    constructor(containerId) {
        this.container = document.querySelector(containerId);
        this.tournamentId = this.container.dataset.tournamentId;
        this.loadBracket();
    }
    
    async loadBracket() {
        const response = await fetch(`/api/v1/tournaments/${this.tournamentId}/bracket`);
        const data = await response.json();
        this.render(data);
        this.attachEventListeners();
    }
    
    render(data) {
        // Рендеринг bracket
    }
    
    attachEventListeners() {
        document.querySelectorAll('.match').forEach(match => {
            match.addEventListener('click', (e) => {
                const matchId = e.currentTarget.dataset.matchId;
                this.showMatchDetails(matchId);
            });
        });
    }
    
    async showMatchDetails(matchId) {
        // Модалка с деталями матча
    }
}

// Авто-обновление каждые 30 секунд
setInterval(() => {
    bracketViewer.loadBracket();
}, 30000);
```

---

### ✅ Критерии завершения Фазы 2

- [ ] API `/api/v1/tournaments/{id}/bracket` работает
- [ ] Генерация Single Elimination bracket работает
- [ ] Страница турнира отображает сетку
- [ ] Bracket интерактивный (клик → детали)
- [ ] Авто-обновление bracket при изменении результатов
- [ ] Поддержка Double Elimination (опционально)

---

## 🎮 ФАЗА 3: Матчмейкинг (Недели 5-7)

### Цель
Автоматический подбор игроков для игр 1v1 или 5v5 по ELO ±200

### Задачи

#### Неделя 5: Очередь матчмейкинга

**День 1-2: Модель очереди**
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
    
    # Статус
    status = Column(String(20), default="waiting")  # waiting, found, cancelled
    queued_at = Column(DateTime, default=datetime.utcnow, index=True)
    found_at = Column(DateTime, nullable=True)
    
    user = relationship("User", backref="mm_queues")
    discipline = relationship("Discipline", backref="mm_queues")
```

**День 3-5: Алгоритм подбора**
```python
# matchmaking.py
from datetime import timedelta
import asyncio

class MatchmakingService:
    def __init__(self, db: Session):
        self.db = db
        self.ELO_RANGE = 200
        self.MAX_WAIT_TIME = timedelta(minutes=5)
        self.TEAM_SIZES = {"1v1": 1, "2v2": 2, "5v5": 5}
    
    async def find_match(self, queue_entry: MatchmakingQueue):
        """Поиск матча для игрока"""
        game_type = queue_entry.game_type
        team_size = self.TEAM_SIZES.get(game_type, 1)
        needed_players = team_size
        
        while True:
            # Ждём накопления игроков
            await asyncio.sleep(2)
            
            candidates = self.get_candidates(
                discipline_id=queue_entry.discipline_id,
                game_type=game_type,
                base_elo=queue_entry.elo,
                exclude_user_id=queue_entry.user_id
            )
            
            if len(candidates) >= needed_players - 1:
                # Нашли достаточно игроков
                match = self.create_match(
                    [queue_entry] + candidates[:needed_players - 1]
                )
                self.notify_players(match)
                return match
            
            # Расширяем диапазон ELO со временем
            wait_time = datetime.utcnow() - queue_entry.queued_at
            if wait_time > timedelta(minutes=2):
                self.ELO_RANGE = 400
            if wait_time > self.MAX_WAIT_TIME:
                # Таймаут - отменяем поиск
                self.cancel_queue(queue_entry)
                return None
    
    def get_candidates(
        self,
        discipline_id: int,
        game_type: str,
        base_elo: int,
        exclude_user_id: int
    ) -> List[MatchmakingQueue]:
        """Получить кандидатов для матча"""
        return self.db.query(MatchmakingQueue).filter(
            MatchmakingQueue.discipline_id == discipline_id,
            MatchmakingQueue.game_type == game_type,
            MatchmakingQueue.status == "waiting",
            MatchmakingQueue.elo.between(base_elo - self.ELO_RANGE, base_elo + self.ELO_RANGE),
            MatchmakingQueue.user_id != exclude_user_id
        ).order_by(MatchmakingQueue.queued_at).limit(5).all()
    
    def create_match(self, queue_entries: List[MatchmakingQueue]) -> Match:
        """Создать матч из очереди"""
        # Логика создания матча
        pass
    
    def notify_players(self, match: Match):
        """Уведомить игроков о матче"""
        # Отправка уведомлений
        pass
```

---

#### Неделя 6-7: API и UI

**API endpoints:**
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
    asyncio.create_task(MatchmakingService(db).find_match(queue_entry))
    
    return {"status": "queued", "message": "Поиск матча начат"}

@router.post("/matchmaking/cancel")
async def cancel_queue(
    request: Request,
    db: Session = Depends(get_db)
):
    """Выйти из очереди"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(401, "Требуется авторизация")
    
    queue_entry = db.query(MatchmakingQueue).filter(
        MatchmakingQueue.user_id == user.id,
        MatchmakingQueue.status == "waiting"
    ).first()
    
    if queue_entry:
        queue_entry.status = "cancelled"
        db.commit()
    
    return {"status": "cancelled"}

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
        "elo": queue_entry.elo
    }
```

**UI для матчмейкинга:**
```html
<!-- templates/matchmaking.html -->
<div class="matchmaking-panel">
    <h2>Поиск матча</h2>
    
    <div class="game-mode-select">
        <button class="mode-btn" data-mode="1v1">1 vs 1</button>
        <button class="mode-btn" data-mode="5v5">5 vs 5</button>
    </div>
    
    <div class="discipline-select">
        {% for disc in disciplines %}
        <button class="discipline-btn" data-discipline="{{ disc.slug }}">
            <img src="{{ disc.icon }}" alt="{{ disc.name }}">
            {{ disc.name }}
        </button>
        {% endfor %}
    </div>
    
    <button id="start-queue" class="btn-primary">Найти матч</button>
    
    <div id="queue-status" class="queue-status hidden">
        <div class="spinner"></div>
        <p>Поиск матча...</p>
        <p class="wait-time">Время в очереди: <span id="wait-timer">0</span> сек</p>
        <button id="cancel-queue" class="btn-secondary">Отмена</button>
    </div>
    
    <div id="match-found" class="match-found hidden">
        <h3>Матч найден!</h3>
        <p>Переход к матчу через <span id="countdown">10</span>...</p>
        <a href="/match/{{ match_id }}" class="btn-primary">Войти в матч</a>
    </div>
</div>

<script>
// matchmaking.js
document.getElementById('start-queue').addEventListener('click', async () => {
    const mode = document.querySelector('.mode-btn.active').dataset.mode;
    const discipline = document.querySelector('.discipline-btn.active').dataset.discipline;
    
    const response = await fetch('/api/v1/matchmaking/queue', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({game_type: mode, discipline: discipline})
    });
    
    if (response.ok) {
        document.getElementById('queue-status').classList.remove('hidden');
        startWaitTimer();
        pollStatus();
    }
});

async function pollStatus() {
    const interval = setInterval(async () => {
        const response = await fetch('/api/v1/matchmaking/status');
        const data = await response.json();
        
        if (data.status === 'not_queued') {
            clearInterval(interval);
            // Показать "Матч найден" или вернуть к поиску
        }
    }, 2000);
}
</script>
```

---

### ✅ Критерии завершения Фазы 3

- [ ] Модель `MatchmakingQueue` работает
- [ ] Алгоритм подбора по ELO ±200 работает
- [ ] API `/api/v1/matchmaking/queue` принимает в очередь
- [ ] API `/api/v1/matchmaking/status` показывает статус
- [ ] UI для поиска матча работает
- [ ] Уведомление о найденном матче
- [ ] Среднее время поиска < 3 минут

---

## 🛡️ ФАЗА 4: Античит и верификация (Недели 8-9)

### Цель
Снизить количество фейковых результатов и читеров

### Задачи

#### Неделя 8: Базовый античит

**День 1-3: Детекция аномалий**
```python
# anticheat.py
class AntiCheatService:
    def __init__(self, db: Session):
        self.db = db
    
    def detect_suspicious_result(self, match: Match) -> bool:
        """Проверка результата матча на аномалии"""
        # Проверка 1: Слишком быстрый матч
        if match.duration and match.duration < 300:  # < 5 минут
            return True
        
        # Проверка 2: Необычный счёт
        if match.team1_score > 30 or match.team2_score > 30:
            return True
        
        # Проверка 3: Большая разница в счёте при равном ELO
        if abs(match.team1.elo - match.team2.elo) < 100:
            score_diff = abs(match.team1_score - match.team2_score)
            if score_diff > 10:
                return True
        
        return False
    
    def get_user_report_count(self, user_id: int, days: int = 7) -> int:
        """Количество жалоб на пользователя за период"""
        week_ago = datetime.utcnow() - timedelta(days=days)
        return self.db.query(Report).filter(
            Report.target_id == user_id,
            Report.created_at > week_ago
        ).count()
    
    def auto_ban_check(self, user_id: int):
        """Автоматическая проверка на бан"""
        report_count = self.get_user_report_count(user_id)
        if report_count >= 5:
            # Требует модерации
            self.flag_for_review(user_id)
```

**День 4-5: Система жалоб**
```python
# models.py
class Report(Base):
    __tablename__ = "reports"
    
    id = Column(Integer, primary_key=True)
    reporter_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    target_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=True)
    
    reason = Column(String(50), nullable=False)  # cheating, throwing, abusive, other
    description = Column(Text, nullable=True)
    status = Column(String(20), default="pending")  # pending, reviewed, resolved, rejected
    
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    reporter = relationship("User", foreign_keys=[reporter_id])
    target = relationship("User", foreign_keys=[target_id])
    match = relationship("Match")
    reviewer = relationship("User", foreign_keys=[reviewed_by])
```

```python
# api.py
@router.post("/reports")
async def submit_report(
    target_id: int,
    reason: str,
    description: Optional[str] = None,
    match_id: Optional[int] = None,
    request: Request,
    db: Session = Depends(get_db)
):
    """Подать жалобу на игрока"""
    user = get_current_user_from_cookie(request, db)
    if not user:
        raise HTTPException(401, "Требуется авторизация")
    
    # Проверка: нельзя жаловаться на себя
    if target_id == user.id:
        raise HTTPException(400, "Нельзя подать жалобу на себя")
    
    # Проверка: не было ли недавних жалоб
    existing = db.query(Report).filter(
        Report.reporter_id == user.id,
        Report.target_id == target_id,
        Report.created_at > datetime.utcnow() - timedelta(hours=24)
    ).first()
    if existing:
        raise HTTPException(400, "Вы уже подавали жалобу на этого игрока")
    
    report = Report(
        reporter_id=user.id,
        target_id=target_id,
        reason=reason,
        description=description,
        match_id=match_id
    )
    db.add(report)
    db.commit()
    
    # Проверка на авто-бан
    anticheat = AntiCheatService(db)
    anticheat.auto_ban_check(target_id)
    
    return {"status": "submitted", "message": "Жалоба отправлена"}
```

---

#### Неделя 9: Верификация и UI модерации

**День 1-3: Админ-панель для модерации**
```python
# admin.py
@router.get("/admin/reports")
async def admin_reports(
    request: Request,
    page: int = 1,
    db: Session = Depends(get_db)
):
    """Просмотр жалоб"""
    admin = require_auth(request, db)
    if not admin.is_admin:
        raise HTTPException(403, "Требуется права админа")
    
    offset = (page - 1) * 20
    reports = db.query(Report).options(
        joinedload(Report.reporter),
        joinedload(Report.target),
        joinedload(Report.match)
    ).order_by(Report.created_at.desc()).offset(offset).limit(20).all()
    
    total = db.query(Report).count()
    
    return templates.TemplateResponse("admin/reports.html", {
        "request": request,
        "reports": reports,
        "page": page,
        "total_pages": (total + 19) // 20
    })

@router.post("/admin/reports/{report_id}/resolve")
async def resolve_report(
    report_id: int,
    action: str,  # ban, warn, dismiss
    request: Request,
    db: Session = Depends(get_db)
):
    """Обработка жалобы"""
    admin = require_auth(request, db)
    if not admin.is_admin:
        raise HTTPException(403, "Требуется права админа")
    
    report = db.query(Report).get(report_id)
    if not report:
        raise HTTPException(404, "Жалоба не найдена")
    
    report.status = "reviewed"
    report.reviewed_at = datetime.utcnow()
    report.reviewed_by = admin.id
    
    if action == "ban":
        report.target.is_active = False
        # Логирование
        log_admin_action(db, admin, "ban_user", "user", report.target.id)
    elif action == "warn":
        # Отправить предупреждение
        pass
    
    db.commit()
    
    return {"status": "resolved"}
```

**День 4-5: Верификация по ID**
```python
# models.py
class VerificationDocument(Base):
    __tablename__ = "verification_documents"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    
    document_type = Column(String(20), nullable=False)  # passport, driver_license, student_id
    document_url = Column(String(500), nullable=False)
    
    status = Column(String(20), default="pending")  # pending, approved, rejected
    rejection_reason = Column(String(200), nullable=True)
    
    submitted_at = Column(DateTime, default=datetime.utcnow)
    reviewed_at = Column(DateTime, nullable=True)
    reviewed_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    user = relationship("User", backref="verification_documents")
```

---

### ✅ Критерии завершения Фазы 4

- [ ] Детекция аномальных результатов работает
- [ ] Система жалоб реализована
- [ ] Админ-панель для модерации жалоб
- [ ] Авто-бан при 5+ жалобах за неделю
- [ ] Верификация по ID (загрузка документов)
- [ ] Бейдж "Verified" в профиле

---

## 🔗 ФАЗА 5: Интеграция Steam API (Недели 10-11)

### Цель
Автоматический сбор статистики и верификация результатов

### Задачи

#### Неделя 10: Steam OAuth и привязка аккаунта

```python
# auth.py - Steam OAuth
from steam import SteamAuth

@router.get("/auth/steam")
async def steam_login(request: Request):
    """Начать авторизацию через Steam"""
    steam_auth = SteamAuth(settings.steam_api_key, settings.app_url)
    auth_url = steam_auth.get_auth_url()
    return RedirectResponse(url=auth_url)

@router.get("/auth/steam/callback")
async def steam_callback(
    request: Request,
    openid_mode: str = Query(...),
    openid_identity: str = Query(...),
    db: Session = Depends(get_db)
):
    """Callback от Steam"""
    steam_auth = SteamAuth(settings.steam_api_key, settings.app_url)
    steam_id = steam_auth.validate_auth(openid_identity)
    
    if not steam_id:
        raise HTTPException(400, "Steam auth failed")
    
    user = get_current_user_from_cookie(request, db)
    if user:
        # Привязка Steam ID к существующему аккаунту
        user.steam_id = steam_id
        db.commit()
    else:
        # Проверка: есть ли пользователь с таким Steam ID
        user = db.query(User).filter(User.steam_id == steam_id).first()
        if not user:
            raise HTTPException(404, "Steam аккаунт не привязан")
    
    return RedirectResponse(url="/profile")
```

#### Неделя 11: Сбор статистики матчей

```python
# steam_api.py
import httpx

class SteamAPIService:
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.steampowered.com"
    
    async def get_cs2_match_stats(self, match_id: str) -> dict:
        """Получить статистику матча CS2"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/ICSGO_730/GetMatchStats/v1",
                params={"match_id": match_id, "key": self.api_key}
            )
            return response.json()
    
    async def get_dota2_match_details(self, match_id: int) -> dict:
        """Получить детали матча Dota 2"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/IDOTA2Match_570/GetMatchDetails/v1",
                params={"match_id": match_id, "key": self.api_key}
            )
            return response.json()
    
    async def get_player_summary(self, steam_id: str) -> dict:
        """Получить информацию об игроке"""
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/ISteamUser/GetPlayerSummaries/v2",
                params={"steamids": steam_id, "key": self.api_key}
            )
            data = response.json()
            return data['response']['players'][0] if data['response']['players'] else None
```

---

### ✅ Критерии завершения Фазы 5

- [ ] Steam OAuth работает
- [ ] Привязка Steam ID к пользователю
- [ ] API для получения статистики CS2/Dota 2
- [ ] Авто-верификация результатов через Steam
- [ ] Отображение Steam статистики в профиле

---

## 📊 ФАЗА 6: Расширенная статистика (Недели 12-13)

### Цель
Глубокая аналитика для игроков

### Задачи

#### Неделя 12: Модель статистики

```python
# models.py
class MatchHistory(Base):
    __tablename__ = "match_history"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    match_id = Column(Integer, ForeignKey("matches.id"), nullable=False, index=True)
    discipline_id = Column(Integer, ForeignKey("disciplines.id"), nullable=False)
    
    # Результат
    result = Column(String(10), nullable=False)  # win, loss
    elo_change = Column(Integer, nullable=False)
    
    # Статистика (универсальная)
    kills = Column(Integer, default=0)
    deaths = Column(Integer, default=0)
    assists = Column(Integer, default=0)
    score = Column(Integer, default=0)
    
    # Метаданные
    duration_seconds = Column(Integer, nullable=True)
    played_at = Column(DateTime, default=datetime.utcnow, index=True)
    
    user = relationship("User", backref="match_history")
    match = relationship("Match")
    discipline = relationship("Discipline")
```

```python
# api.py
@router.get("/users/{user_id}/stats")
async def get_user_stats(
    user_id: int,
    discipline: Optional[str] = None,
    period: str = "all",  # all, week, month, year
    db: Session = Depends(get_db)
):
    """Получить расширенную статистику пользователя"""
    # Расчёт статистики
    query = db.query(MatchHistory).filter(MatchHistory.user_id == user_id)
    
    if discipline:
        disc = db.query(Discipline).filter(Discipline.slug == discipline).first()
        if disc:
            query = query.filter(MatchHistory.discipline_id == disc.id)
    
    if period != "all":
        days = {"week": 7, "month": 30, "year": 365}[period]
        cutoff = datetime.utcnow() - timedelta(days=days)
        query = query.filter(MatchHistory.played_at > cutoff)
    
    matches = query.all()
    
    total_matches = len(matches)
    wins = sum(1 for m in matches if m.result == "win")
    losses = total_matches - wins
    
    total_kills = sum(m.kills for m in matches)
    total_deaths = sum(m.deaths for m in matches)
    total_assists = sum(m.assists for m in matches)
    
    kd_ratio = total_kills / total_deaths if total_deaths > 0 else total_kills
    kda_ratio = (total_kills + total_assists) / total_deaths if total_deaths > 0 else (total_kills + total_assists)
    
    return {
        "overview": {
            "matches": total_matches,
            "wins": wins,
            "losses": losses,
            "win_rate": wins / total_matches * 100 if total_matches > 0 else 0
        },
        "combat": {
            "kills": total_kills,
            "deaths": total_deaths,
            "assists": total_assists,
            "kd_ratio": round(kd_ratio, 2),
            "kda_ratio": round(kda_ratio, 2),
            "avg_kills": round(total_kills / total_matches, 1) if total_matches > 0 else 0
        },
        "recent_form": [
            {"result": m.result, "elo_change": m.elo_change}
            for m in matches[-10:]  # Последние 10 матчей
        ]
    }
```

#### Неделя 13: Графики и визуализация

```html
<!-- templates/profile_stats.html -->
<div class="stats-charts">
    <canvas id="elo-chart"></canvas>
    <canvas id="winrate-chart"></canvas>
    <canvas id="kd-chart"></canvas>
</div>

<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
// stats.js
const eloData = await fetch(`/api/v1/users/${userId}/stats/elo-history`).then(r => r.json());

new Chart(document.getElementById('elo-chart'), {
    type: 'line',
    data: {
        labels: eloData.dates,
        datasets: [{
            label: 'ELO',
            data: eloData.values,
            borderColor: '#00f0ff',
            tension: 0.4
        }]
    },
    options: {
        responsive: true,
        plugins: {
            legend: {display: false}
        }
    }
});
</script>
```

---

### ✅ Критерии завершения Фазы 6

- [ ] Модель `MatchHistory` работает
- [ ] API `/api/v1/users/{id}/stats` возвращает данные
- [ ] Графики ELO, Win Rate, K/D отображаются
- [ ] Экспорт статистики в CSV
- [ ] Сравнение с другими игроками

---

## 📋 Итоговый чек-лист

| Фаза | Задачи | Длительность | Статус |
|------|--------|--------------|--------|
| **Фаза 1** | Рейтинг ELO + Leaderboard | 2 недели | ⬜ |
| **Фаза 2** | Bracket UI | 2 недели | ⬜ |
| **Фаза 3** | Матчмейкинг | 3 недели | ⬜ |
| **Фаза 4** | Античит + Верификация | 2 недели | ⬜ |
| **Фаза 5** | Steam API | 2 недели | ⬜ |
| **Фаза 6** | Расширенная статистика | 2 недели | ⬜ |

**Итого:** 13 недель (~3 месяца)

---

## 🎯 Критерии успеха проекта

После завершения всех фаз EasyCyberPro будет иметь:

| Функция | Статус | Конкуренты |
|---------|--------|------------|
| Рейтинг ELO | ✅ | FACEIT ✅ |
| Bracket UI | ✅ | Battlefy ✅ |
| Матчмейкинг | ✅ | FACEIT ✅ |
| Античит | ✅ | FACEIT ✅ |
| Steam интеграция | ✅ | FACEIT ✅ |
| Расширенная статистика | ✅ | FACEIT ✅ |
| **Тренерская система** | ✅ | **Только у нас!** 🏆 |

**Результат:** Паритет с лидерами рынка + уникальное преимущество
