# EasyCyberPro — Киберспортивная платформа

**Версия:** 2.0
**Дата создания:** Апрель 2026
**Последнее обновление:** 7 апреля 2026

## Обзор проекта

**EasyCyberPro** — это полнофункциональная веб-платформа для киберспортивных соревнований, разработанная на **FastAPI** (Python). Платформа позволяет организовывать турниры по Dota 2, CS2, Мир танков, управлять командами и игроками, вести рейтинг игроков (ELO система, аналог FACEIT), проводить турниры с турнирными сетками, а также предоставляет систему обучения у тренеров.

### Ключевые возможности

- 🎮 **Турниры:** Каталог, фильтрация, регистрация, турнирные сетки (Single/Double Elimination)
- 👥 **Команды:** Создание, управление участниками, статистика
- 📊 **Рейтинг ELO:** 10 уровней (аналог FACEIT), таблица лидеров, история изменений
- 🏆 **Матчмейкинг:** Автоматический подбор соперников (базовый)
- 🎓 **Тренерская система:** Ученики, тренировки, посещаемость, заметки
- 📰 **Новости:** CRUD операции, загрузка изображений, публикация
- 🔐 **Аутентификация:** Регистрация, вход, logout, восстановление пароля, email-верификация
- 👤 **Профиль:** Аватар, био, соцсети, дисциплины, настройки приватности
- 🛡️ **Админ-панель:** Управление пользователями, турнирами, командами, тренерами, логи действий
- 📡 **REST API v1:** Полноценное API для всех сущностей

### Технологический стек

| Категория | Технология |
|-----------|------------|
| **Фреймворк** | FastAPI 0.100+ |
| **Язык** | Python 3.10+ |
| **ORM** | SQLAlchemy 2.0+ |
| **Миграции** | Alembic 1.12+ |
| **Валидация** | Pydantic 2.0+ |
| **Шаблоны** | Jinja2 3.1+ |
| **БД (dev)** | SQLite |
| **БД (prod)** | PostgreSQL (рекомендуется) |
| **Безопасность** | bcrypt, python-jose (JWT), SlowAPI (rate limiting), CSRF |
| **Email** | fastapi-mail (Gmail SMTP) |
| **Frontend** | HTML5, CSS3 (тёмная тема), JavaScript |

## Структура проекта

```
web_app/
├── main.py                     # Точка входа, инициализация FastAPI, роутинг
├── config.py                   # Настройки через pydantic-settings (.env)
├── models.py                   # SQLAlchemy модели БД (User, News, Team, Tournament, Match, и т.д.)
├── schemas.py                  # Pydantic схемы для API валидации
├── utils.py                    # Утилиты: хеширование, JWT, ELO расчёты, CSRF
├── auth.py                     # Аутентификация, регистрация, восстановление пароля
├── api.py                      # REST API v1 endpoints (JSON responses)
├── leaderboard.py              # Таблица лидеров
├── mailer.py                   # Email-рассылка (верификация, уведомления)
│
├── admin.py                    # Админ-панель: пользователи
├── admin_teams.py              # Админ-панель: команды
├── admin_tournaments.py        # Админ-панель: турниры
├── admin_coaches.py            # Админ-панель: тренеры
│
├── news.py                     # Новости (CRUD)
├── disciplines.py              # Дисциплины (Dota 2, CS2, Мир танков)
├── tournaments.py              # Публичные турниры для пользователей
├── profile.py                  # Профиль пользователя
├── coach.py                    # Тренерская система (сессии, ученики)
│
├── alembic/                    # Миграции БД
│   ├── versions/               # Файлы миграций
│   └── env.py                  # Конфигурация Alembic
├── templates/                  # Jinja2 HTML-шаблоны
│   ├── includes/               # Части шаблонов (navbar, footer)
│   ├── admin/                  # Шаблоны админ-панели
│   ├── coach/                  # Шаблоны тренера
│   └── *.html                  # Основные страницы
├── static/                     # Статические файлы
│   ├── style.css               # Основные стили (тёмная тема)
│   ├── bracket.js              # Визуализация турнирных сеток
│   ├── images/                 # Изображения (дисциплины, иконки)
│   └── uploads/                # Загруженные пользователями файлы
│
├── requirements.txt            # Python зависимости
├── .env                        # Переменные окружения (не коммитить!)
├── pytest.ini                  # Настройки pytest
├── alembic.ini                 # Конфигурация Alembic
└── app.db                      # SQLite база данных (dev)
```

## Модели данных

### Основные сущности

| Модель | Описание |
|--------|----------|
| **User** | Пользователи (email, username, роль, профиль, настройки, статистика) |
| **Discipline** | Игровые дисциплины (Dota 2, CS2, Мир танков) |
| **Team** | Команды (капитан, дисциплина, участники, рейтинг, win rate) |
| **TeamMember** | Участники команды |
| **Tournament** | Турниры (даты, статус, формат, призовой фонд) |
| **Match** | Матчи турнирной сетки (команды, счёт, раунд, статус) |
| **TournamentParticipation** | Участие команды в турнире |
| **News** | Новости (автор, контент, изображения) |
| **AdminLog** | Логирование действий администратора |
| **PasswordResetToken** | Токены сброса пароля |

### Система рейтинга ELO

| Модель | Описание |
|--------|----------|
| **PlayerRating** | Рейтинг игрока по дисциплинам (ELO, уровень, статистика) |
| **RatingChange** | История изменений рейтинга |
| **MatchmakingQueue** | Очередь матчмейкинга |

### Тренерская система

| Модель | Описание |
|--------|----------|
| **CoachStudent** | Связь тренер-ученик |
| **TrainingSession** | Тренировки (расписание, статус, заметки) |
| **TrainingAttendance** | Посещаемость тренировок |

### Связи многие-ко-многим

- **user_disciplines** — пользователи и их дисциплины (с skill_level: beginner/intermediate/advanced/pro)

## Быстрый старт

### Требования

- Python 3.10 или выше
- pip (менеджер пакетов Python)

### Установка и запуск

```bash
# Переход в директорию проекта
cd C:\Users\User\web_app

# Активация виртуального окружения
venv\Scripts\activate

# Запуск сервера
python main.py
```

Откройте браузер: **http://localhost:8000**

### Альтернативный запуск (с авто-перезагрузкой)

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## Конфигурация

### Файл .env

Основные параметры в `.env`:

```ini
# Database
DATABASE_URL=sqlite:///./app.db

# Security
SECRET_KEY=<auto-generated>
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_TOKEN_EXPIRE_HOURS=8

# Email (Gmail)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_FROM=noreply@easycyberpro.ru
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_BURST=5

# App
APP_URL=http://localhost:8000
DEBUG=false
```

**Генерация SECRET_KEY:**
```python
import secrets
print(secrets.token_urlsafe(32))
```

> **Примечание:** При первом запуске SECRET_KEY генерируется автоматически и сохраняется в `.env`.

## База данных

### Автоматическое создание таблиц

При запуске `main.py` таблицы создаются автоматически:

```python
create_tables()
init_disciplines()  # Инициализация Dota 2, CS2, Мир танков
```

### Alembic миграции

```bash
# Создать миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить все миграции
alembic upgrade head

# Откатить одну миграцию
alembic downgrade -1

# Текущая версия
alembic current

# История миграций
alembic history
```

## API Документация

FastAPI автоматически генерирует интерактивную документацию:

| Документация | URL |
|--------------|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

### Основные API endpoints (v1)

#### Аутентификация

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/auth/me` | GET | Текущий пользователь |

#### Рейтинги и лидерборды

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/leaderboard` | GET | Таблица лидеров (параметр: `discipline`) |
| `/api/v1/leaderboards` | GET | Все дисциплины с лидербордами |
| `/api/v1/users/{user_id}/ratings` | GET | Все рейтинги пользователя |
| `/api/v1/users/{user_id}/rating/{discipline_slug}` | GET | Рейтинг по конкретной дисциплине |
| `/api/v1/users/{user_id}/rating/{discipline_slug}/history` | GET | История изменений рейтинга |

#### Матчмейкинг

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/matchmaking/queue` | POST | Встать в очередь |
| `/api/v1/matchmaking/status` | GET | Статус очереди |
| `/api/v1/matchmaking/queue` | DELETE | Выйти из очереди |

#### Турниры

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/tournaments` | GET | Список турниров |
| `/api/v1/tournaments/{id}` | GET | Детали турнира |
| `/api/v1/tournaments/{id}/bracket` | GET | Турнирная сетка |
| `/api/v1/matches/{match_id}` | GET | Детали матча |

#### Новости, команды, дисциплины

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/news` | GET | Список новостей |
| `/api/v1/news/{id}` | GET | Новость по ID |
| `/api/v1/teams` | GET | Список команд |
| `/api/v1/disciplines` | GET | Список дисциплин |

## Система рейтинга ELO

### Уровни (аналог FACEIT)

| Уровень | Диапазон ELO |
|---------|--------------|
| 1 | 0–199 |
| 2 | 200–399 |
| 3 | 400–599 |
| 4 | 600–799 |
| 5 | 800–999 |
| 6 | 1000–1199 |
| 7 | 1200–1399 |
| 8 | 1400–1699 |
| 9 | 1700–1999 |
| 10 | 2000+ |

### K-факторы

- **48** — новые игроки (< 10 игр)
- **32** — базовый (10–100 игр)
- **16** — опытные (> 100 игр)

### Формула расчёта

```
ΔR = K * (S - E)
```

Где:
- `S` — фактический счёт (1 = победа, 0 = поражение, 0.5 = ничья)
- `E` — ожидаемый счёт: `1 / (1 + 10 ^ ((R_opponent - R_player) / 400))`

Стартовый ELO: **1000**

## Архитектура приложения

### Роутинг

Все роутеры регистрируются в `main.py`:

| Модуль | Префикс / Назначение |
|--------|---------------------|
| `auth.py` | `/register`, `/login`, `/logout`, `/verify`, `/forgot-password`, `/reset-password` |
| `admin.py` | `/admin/*` — управление пользователями |
| `admin_teams.py` | `/admin/teams/*` — управление командами |
| `admin_tournaments.py` | `/admin/tournaments/*` — управление турнирами |
| `admin_coaches.py` | `/admin/coaches/*` — управление тренерами |
| `news.py` | `/news/*` — CRUD новостей (admin + public) |
| `disciplines.py` | `/disciplines/*` — дисциплины |
| `tournaments.py` | `/tournaments/*` — публичные турниры |
| `api.py` | `/api/v1/*` — REST API |
| `profile.py` | `/profile/*` — профиль пользователя |
| `coach.py` | `/coach/*` — тренерская система |
| `leaderboard.py` | `/leaderboard/*` — таблицы лидеров |

### Аутентификация

- **Токены:** JWT через cookie (`access_token`)
- **Хеширование:** bcrypt
- **CSRF:** токены через `secrets.token_urlsafe`
- **Rate limiting:** SlowAPI (10/мин, 5/сек burst)

### Flash-сообщения

Flash-сообщения передаются через cookie в base64-кодированном JSON формате.

## Тестирование

```bash
# Все тесты
pytest

# С подробным выводом
pytest -v

# С покрытием кода
pip install pytest-cov
pytest --cov=. --cov-report=html

# Конкретный тестовый файл
pytest test_db.py -v
```

Отчёт о покрытии: `htmlcov/index.html`

## Разработка

### Добавление нового модуля

1. Создать файл модуля (например, `my_module.py`)
2. Определить роутер:
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/my-module", tags=["My Module"])

   @router.get("/")
   async def my_endpoint():
       return {"message": "Hello"}
   ```
3. Зарегистрировать роутер в `main.py`:
   ```python
   from my_module import router as my_module_router
   app.include_router(my_module_router)
   ```

### Создание новой модели БД

1. Добавить класс в `models.py` (наследник `Base`)
2. Создать миграцию Alembic:
   ```bash
   alembic revision --autogenerate -m "Add new_model"
   alembic upgrade head
   ```
3. Добавить Pydantic схему в `schemas.py`

### Шаблоны и статика

- HTML шаблоны: `templates/`
- Статические файлы: `static/`
- Загруженные файлы: `static/uploads/`

## Развёртывание

### Production (uvicorn)

```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4 --log-level info
```

### Gunicorn (рекомендуется)

```bash
pip install gunicorn
gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

### Production БД (PostgreSQL)

В `.env`:
```ini
DATABASE_URL=postgresql://user:password@localhost:5432/easycyberpro
```

## Полезные команды

| Задача | Команда |
|--------|---------|
| Запуск сервера | `python main.py` |
| Запуск с reload | `uvicorn main:app --reload` |
| Запустить тесты | `pytest -v` |
| Миграция БД | `alembic upgrade head` |
| Создать миграцию | `alembic revision --autogenerate -m "msg"` |
| Найти процесс на порту 8000 | `netstat -ano \| findstr :8000` |
| Убить процесс | `taskkill /PID <PID> /F` |

## Решение проблем

### ModuleNotFoundError

```bash
# Убедитесь, что виртуальное окружение активировано
venv\Scripts\activate

# Переустановите зависимости
pip install -r requirements.txt
```

### Address already in use (порт 8000)

```bash
# Windows: найти процесс
netstat -ano | findstr :8000
# Завершить процесс
taskkill /PID <PID> /F
```

### CSRF token mismatch

Очистите cookie брауера и перезагрузите страницу.

## Зависимости (requirements.txt)

```
fastapi>=0.100.0
uvicorn[standard]>=0.20.0
jinja2>=3.1.0
python-multipart>=0.0.6
sqlalchemy>=2.0.0
alembic>=1.12.0
passlib>=1.7.4
bcrypt==4.0.1
python-jose[cryptography]>=3.3.0
fastapi-mail>=1.4.0
pydantic>=2.0.0
pydantic-settings>=2.0.0
slowapi>=0.1.9
pytest>=7.4.0
pytest-asyncio>=0.21.0
httpx>=0.24.0
```

## Лицензия

EasyCyberPro — проприетарное программное обеспечение. Все права защищены © 2026 EasyCyberPro.
