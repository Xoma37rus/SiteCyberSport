# EasyCyberPro — Киберспортивная платформа

## 📋 Обзор проекта

**EasyCyberPro** — это веб-платформа для киберспортивных соревнований, построенная на **FastAPI (Python)**. Платформа позволяет организовывать турниры, управлять командами, вести статистику игроков и предоставляет тренерскую систему.

### Основное назначение
- Организация и проведение онлайн-турниров по кибердисциплинам (Dota 2, CS2, Мир танков)
- Управление командами и игроками
- Рейтинговая система и статистика
- Тренерская платформа (уникальная фича)
- Новостной портал

---

## 🏗️ Архитектура и технологии

### Стек технологий
| Компонент | Технология |
|-----------|------------|
| **Backend** | Python 3.10+, FastAPI |
| **База данных** | SQLite (разработка), поддержка PostgreSQL через SQLAlchemy |
| **ORM** | SQLAlchemy 2.0 |
| **Миграции** | Alembic |
| **Шаблоны** | Jinja2 |
| **Аутентификация** | JWT (python-jose), bcrypt |
| **Валидация** | Pydantic 2.0 |
| **Email** | FastAPI-Mail (SMTP) |
| **Rate Limiting** | SlowAPI |
| **Тесты** | pytest, pytest-asyncio, httpx |

### Структура проекта
```
web_app/
├── main.py                 # Точка входа, инициализация FastAPI
├── config.py               # Настройки через pydantic-settings
├── models.py               # SQLAlchemy модели БД
├── schemas.py              # Pydantic схемы для API
├── auth.py                 # Аутентификация, регистрация, восстановление пароля
├── api.py                  # REST API v1 endpoints
├── utils.py                # Утилиты (хеширование, JWT, CSRF)
├── mailer.py               # Email-рассылки
│
├── admin.py                # Админ-панель: пользователи
├── admin_teams.py          # Админ-панель: команды
├── admin_tournaments.py    # Админ-панель: турниры
├── admin_coaches.py        # Админ-панель: тренеры
│
├── news.py                 # Новости (CRUD)
├── disciplines.py          # Дисциплины (игры)
├── tournaments.py          # Турниры для пользователей
├── teams.py                # Команды (создание, управление)
├── profile.py              # Профиль пользователя
├── coach.py                # Тренерская система
│
├── alembic/                # Миграции БД
├── templates/              # Jinja2 HTML-шаблоны
├── static/                 # Статика (CSS, изображения, загрузки)
├── venv/                   # Python virtual environment
│
├── requirements.txt        # Зависимости
├── .env                    # Переменные окружения (секреты)
└── pytest.ini              # Настройки тестов
```

---

## 🚀 Запуск и разработка

### Предварительные требования
- Python 3.10 или выше
- pip

### Установка

```bash
# Клонирование и переход в директорию
cd C:\Users\User\web_app

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка окружения

Создайте файл `.env` в корне проекта:

```env
# Email (Gmail)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_FROM=noreply@easycyberpro.ru
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Приложение
APP_URL=http://localhost:8000
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./app.db

# Rate Limiting
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_BURST=5

# Logging
LOG_LEVEL=INFO
```

> **Примечание:** `SECRET_KEY` генерируется автоматически при первом запуске, если не задан.

### Запуск сервера

```bash
# Через main.py
python main.py

# Или через uvicorn напрямую
uvicorn main:app --host 0.0.0.0 --port 8000 --reload

# Режим разработки с авто-перезагрузкой
uvicorn main:app --reload --log-level debug
```

Сервер будет доступен по адресу: **http://localhost:8000**

### API Документация

FastAPI автоматически генерирует интерактивную документацию:

- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

---

## 🧪 Тестирование

```bash
# Запуск всех тестов
pytest

# Запуск с выводом coverage
pytest --cov=.

# Запуск конкретного теста
pytest test_db.py -v

# Запуск с выводом логов
pytest -s -v
```

---

## 🗄️ База данных

### Модели данных

#### Основные сущности

| Модель | Описание |
|--------|----------|
| `User` | Пользователи (email, username, пароль, профиль, роли) |
| `News` | Новости платформы |
| `Discipline` | Игровые дисциплины (Dota 2, CS2, Tanks) |
| `Team` | Команды с капитаном и участниками |
| `TeamMember` | Участники команд |
| `Tournament` | Турниры с настройками формата |
| `TournamentParticipation` | Заявки команд на турниры |
| `Match` | Матчи турнирной сетки |
| `AdminLog` | Лог действий администратора |
| `PasswordResetToken` | Токены сброса пароля |
| `CoachStudent` | Связь тренер-ученик |
| `TrainingSession` | Тренировочные сессии |
| `TrainingAttendance` | Посещаемость тренировок |

### Миграции (Alembic)

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Description"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1

# История миграций
alembic history
```

### Инициализация данных

При первом запуске автоматически создаются:
- Таблицы БД
- Дисциплины по умолчанию (Dota 2, CS2, Мир танков)

---

## 🔐 Безопасность

### Аутентификация
- **JWT токены** с сроком действия 30 минут
- **HttpOnly cookie** для хранения токена
- **bcrypt** для хеширования паролей
- **Email-верификация** (авто-верификация в режиме разработки)

### Защита
- **Rate Limiting:** 10 запросов/минуту, 5/секунду (burst)
- **CSRF Protection** для форм
- **CORS** настроен для localhost:8000

### Роли пользователей
- `admin` — полный доступ к админ-панели
- `trainer` — доступ к тренерским функциям
- `student`, `student_pro`, `student_ult` — уровни учеников
- `user` — базовый пользователь

---

## 📡 REST API

API версии v1 доступно по префиксу `/api/v1`.

### Основные endpoints

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/auth/me` | GET | Текущий пользователь |
| `/api/v1/health` | GET | Статус сервиса |
| `/api/v1/news` | GET | Список новостей (пагинация) |
| `/api/v1/news/{id}` | GET | Новость по ID |
| `/api/v1/disciplines` | GET | Список дисциплин |
| `/api/v1/teams` | GET | Список команд (фильтр по дисциплине) |
| `/api/v1/teams/{id}` | GET | Команда по ID |
| `/api/v1/tournaments` | GET | Список турниров (фильтры) |
| `/api/v1/tournaments/{id}` | GET | Турнир по ID |

### Пример запроса

```bash
curl -X GET "http://localhost:8000/api/v1/news?page=1&limit=10" \
  -H "Accept: application/json"
```

---

## 🎨 Frontend

### Шаблоны (Jinja2)

Расположены в `templates/`:

| Шаблон | Описание |
|--------|----------|
| `index.html` | Главная страница |
| `login.html`, `register.html` | Аутентификация |
| `profile.html` | Профиль пользователя |
| `dashboard.html` | Дашборд |
| `tournaments.html`, `tournament_detail.html` | Турниры |
| `news.html`, `news_detail.html` | Новости |
| `admin/*.html` | Админ-панель |
| `coach/*.html` | Тренерский кабинет |

### Статика

- `static/style.css` — основные стили (тёмная тема, CSS-переменные)
- `static/images/` — изображения
- `static/uploads/` — загруженные файлы

---

## 📦 Основные модули

### auth.py
- Регистрация (`/register`)
- Вход (`/login`)
- Выход (`/logout`)
- Восстановление пароля (`/forgot-password`, `/reset-password`)
- Верификация email (`/verify`)

### admin.py
- Управление пользователями
- Логи действий
- Модерация

### tournaments.py
- Каталог турниров
- Регистрация команд
- Управление заявками

### coach.py
- Список учеников
- Планирование тренировок
- Отметка посещаемости

### mailer.py
- Отправка верификационных писем
- Уведомления о турнирах
- Сброс пароля

---

## 🔧 Конфигурация

### config.py

Класс `Settings` на основе `pydantic-settings` загружает переменные из:
1. Переменных окружения
2. Файла `.env`

```python
from config import settings

# Доступ к настройкам
settings.database_url
settings.secret_key
settings.rate_limit_per_minute
settings.mail_server
```

---

## 📝 Планы развития

См. `DEVELOPMENT_PLAN.md` для детального плана.

### Критические задачи (Фаза 1-2)
1. **Рейтинговая система ELO** — модель `PlayerRating`, расчёт рейтинга, leaderboard
2. **Визуализация турнирных сеток** — Bracket UI (SVG/Canvas)
3. **Матчмейкинг** — автоматический подбор игроков по ELO
4. **Античит** — базовая валидация результатов

### Улучшения UX (Фаза 3-4)
- Расширенная статистика игроков
- Ладдеры (ежедневные соревнования)
- Discord-интеграция
- Стриминг (Twitch embed)

### Монетизация
- Premium-подписка
- Система наград и достижений

---

## 🐛 Известные ограничения

| Ограничение | Решение |
|-------------|---------|
| SQLite не подходит для production | Миграция на PostgreSQL |
| Нет визуализации турнирной сетки | В разработке (Bracket UI) |
| Ручной ввод результатов матчей | Интеграция Steam API (план) |
| Нет античита | Базовая валидация (план) |

---

## 📞 Поддержка и контакты

- **Email:** noreply@easycyberpro.ru
- **Документация:** `/docs` (Swagger)

---

## 📄 Лицензия

EasyCyberPro — проприетарное ПО.

---

## 📊 Быстрые команды

```bash
# Запуск сервера
uvicorn main:app --reload

# Запуск тестов
pytest -v

# Создание миграции
alembic revision --autogenerate -m "new migration"

# Применение миграций
alembic upgrade head

# Проверка зависимостей
pip list --outdated

# Обновление зависимостей
pip install -r requirements.txt --upgrade
```
