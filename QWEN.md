# EasyCyberPro — Киберспортивная платформа

## Обзор проекта

**EasyCyberPro** — это веб-платформа для киберспортивных соревнований, разработанная на **FastAPI** (Python). Платформа предоставляет функционал для регистрации пользователей, создания команд, участия в турнирах, публикации новостей и управления админ-панелью.

### Основные возможности

- **Аутентификация и авторизация**: регистрация, вход, восстановление пароля, JWT-токены
- **Пользовательские профили**: настройка профиля, статистика, социальные сети
- **Команды**: создание и управление командами, приглашение участников
- **Турниры**: регистрация на турниры, турнирные сетки, матчи
- **Новости**: публикация и просмотр новостей платформы
- **Дисциплины**: поддержка нескольких игровых дисциплин (Dota 2, CS2, Tanks)
- **Админ-панель**: управление пользователями, логами, контентом
- **REST API**: полный API для frontend и мобильных приложений
- **Email-рассылка**: уведомления о событиях, подтверждение регистрации

### Технологический стек

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI, Python 3.10+ |
| База данных | SQLite (с поддержкой миграции на PostgreSQL) |
| ORM | SQLAlchemy 2.0 |
| Миграции | Alembic |
| Шаблоны | Jinja2 |
| Аутентификация | JWT (python-jose), bcrypt |
| Валидация | Pydantic v2 |
| Тестирование | pytest, pytest-asyncio, httpx |
| Email | fastapi-mail |
| Rate Limiting | slowapi |

---

## Структура проекта

```
web_app/
├── main.py                 # Точка входа приложения
├── config.py               # Конфигурация и настройки
├── models.py               # SQLAlchemy модели БД
├── schemas.py              # Pydantic схемы для API
├── auth.py                 # Маршруты аутентификации
├── admin.py                # Админ-панель (пользователи)
├── admin_teams.py          # Админ-панель (команды)
├── admin_tournaments.py    # Админ-панель (турниры)
├── api.py                  # REST API v1 endpoints
├── news.py                 # Новости (админ + публичные)
├── disciplines.py          # Дисциплины
├── tournaments.py          # Турниры (публичные)
├── profile.py              # Профиль пользователя
├── mailer.py               # Email-рассылка
├── utils.py                # Утилиты (хеширование, токены)
├── create_admin.py         # Скрипт создания админа
├── reset_admin_password.py # Скрипт сброса пароля админа
├── backup_db.py            # Резервное копирование БД
├── update_db.py            # Обновление БД
├── seed_data.py            # Начальное наполнение БД
├── test_api.py             # Тесты API
├── test_site.py            # Тесты сайта
├── pytest.ini              # Конфигурация pytest
├── requirements.txt        # Зависимости Python
├── alembic.ini             # Конфигурация Alembic
├── alembic/                # Миграции БД
│   └── versions/           # Файлы миграций
├── templates/              # Jinja2 шаблоны
│   ├── admin/              # Шаблоны админ-панели
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   └── ...
├── static/                 # Статические файлы
│   ├── style.css
│   ├── images/
│   └── uploads/            # Загруженные файлы
└── backups/                # Резервные копии БД
```

---

## Установка и запуск

### Требования

- Python 3.10 или выше
- pip

### Установка зависимостей

```bash
cd C:\Users\User\web_app

# Активация виртуального окружения (если существует)
venv\Scripts\activate

# Установка зависимостей
pip install -r requirements.txt
```

### Настройка окружения

Отредактируйте файл `.env`:

```env
# Email (Gmail)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_FROM=noreply@easycyberpro.ru
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Приложение
APP_URL=http://localhost:8000
SECRET_KEY=ваш_секретный_ключ
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./app.db
```

> **Важно**: Для работы email-рассылки через Gmail:
> 1. Включите 2FA в аккаунте Google
> 2. Создайте пароль приложения: https://myaccount.google.com/apppasswords
> 3. Вставьте его в `MAIL_PASSWORD`

### Запуск сервера

```bash
# Через main.py
python main.py

# Или через uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

Приложение будет доступно по адресу: **http://localhost:8000**

### Создание администратора

```bash
python create_admin.py
```

Следуйте инструкциям для создания учётной записи администратора.

---

## База данных

### Модели данных

Основные модели (файл `models.py`):

| Модель | Описание |
|--------|----------|
| `User` | Пользователи (email, username, роли, профиль) |
| `News` | Новости платформы |
| `Discipline` | Игровые дисциплины (Dota 2, CS2, Tanks) |
| `Team` | Команды игроков |
| `TeamMember` | Участники команд |
| `Tournament` | Турниры |
| `TournamentParticipation` | Участие команд в турнирах |
| `Match` | Матчи турнирной сетки |
| `AdminLog` | Лог действий администратора |
| `PasswordResetToken` | Токены сброса пароля |

### Миграции (Alembic)

```bash
# Создать новую миграцию
alembic revision --autogenerate -m "Описание изменений"

# Применить миграции
alembic upgrade head

# Откатить миграцию
alembic downgrade -1
```

### Резервное копирование

```bash
# Создать резервную копию
python backup_db.py
```

---

## API Endpoints

### Health Check

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/health` | Проверка статуса сервиса |
| GET | `/api/v1/health` | Проверка статуса API |

### Новости

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/news` | Список новостей (пагинация) |
| GET | `/api/v1/news/{id}` | Новость по ID |

### Дисциплины

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/disciplines` | Список дисциплин |
| GET | `/api/v1/disciplines/{slug}` | Дисциплина по slug |

### Команды

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/teams` | Список команд |
| GET | `/api/v1/teams/{id}` | Команда по ID |

### Турниры

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/api/v1/tournaments` | Список турниров |
| GET | `/api/v1/tournaments/{id}` | Турнир по ID |

### Аутентификация

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/register` | Страница регистрации |
| POST | `/register` | Регистрация пользователя |
| GET | `/login` | Страница входа |
| POST | `/login` | Аутентификация |
| GET | `/logout` | Выход |
| GET | `/verify` | Подтверждение email |
| GET | `/forgot-password` | Запрос сброса пароля |
| POST | `/forgot-password` | Отправка токена сброса |
| GET | `/reset-password` | Страница сброса пароля |
| POST | `/reset-password` | Сброс пароля |

### Админ-панель

| Метод | Endpoint | Описание |
|-------|----------|----------|
| GET | `/admin` | Главная админ-панели |
| GET | `/admin/login` | Вход администратора |
| POST | `/admin/login` | Аутентификация админа |
| GET | `/admin/logout` | Выход |
| GET | `/admin/users` | Управление пользователями |
| POST | `/admin/users/{id}/toggle-admin` | Изменить статус админа |
| POST | `/admin/users/{id}/toggle-active` | Изменить активность |
| POST | `/admin/users/{id}/delete` | Удалить пользователя |
| GET | `/admin/logs` | Лог действий |

---

## Тестирование

### Запуск тестов

```bash
# Все тесты
pytest -v

# Конкретный файл
pytest test_api.py -v

# С покрытием
pytest --cov=. -v
```

### Структура тестов

- `test_api.py` — тесты REST API (health, новости, дисциплины, команды, турниры, аутентификация)
- `test_site.py` — тесты веб-страниц

### Fixtures

Тесты используют тестовую SQLite БД (`test_app.db`), которая создаётся заново перед каждым тестом.

---

## Конфигурация

### Основные настройки (config.py)

| Параметр | По умолчанию | Описание |
|----------|--------------|----------|
| `database_url` | `sqlite:///./app.db` | Подключение к БД |
| `secret_key` | авто-генерация | Ключ для JWT |
| `algorithm` | `HS256` | Алгоритм шифрования |
| `access_token_expire_minutes` | 30 | Время жизни токена |
| `rate_limit_per_minute` | 10 | Лимит запросов в минуту |
| `max_upload_size_mb` | 5 | Макс. размер загрузки |

### Rate Limiting

Приложение использует slowapi для ограничения запросов:
- **10 запросов в минуту** (настраивается в `.env`)
- **5 запросов в секунду** (burst)

---

## Разработка

### Добавление нового модуля

1. Создайте файл маршрута (например, `new_module.py`)
2. Определите роутер:
   ```python
   from fastapi import APIRouter
   router = APIRouter(prefix="/new-module", tags=["New Module"])
   ```
3. Добавьте маршруты
4. Зарегистрируйте в `main.py`:
   ```python
   from new_module import router as new_module_router
   app.include_router(new_module_router)
   ```

### Стиль кода

- **Именование**: snake_case для функций/переменных, PascalCase для классов
- **Типизация**: используйте type hints
- **Документация**: docstrings для функций и классов
- **Логирование**: используйте `logging` модуль

### Логи

Логи выводятся в консоль и файл `server.log`. Уровень логирования настраивается в `.env`:
```env
LOG_LEVEL=INFO
```

---

## Безопасность

### Реализованные механизмы

- **JWT-аутентификация** с раздельными токенами для пользователей и админов
- **Хеширование паролей** через bcrypt
- **CSRF-защита** для форм
- **Rate Limiting** для защиты от DDoS
- **Валидация входных данных** через Pydantic
- **Email-верификация** (авто-верификация в dev-режиме)

### Роли пользователей

| Роль | Описание |
|------|----------|
| `user` | Обычный пользователь |
| `admin` | Администратор (полный доступ) |
| `trainer` | Тренер |
| `student`, `student_pro`, `student_ult` | Учебные роли |

---

## Полезные команды

```bash
# Проверка зависимостей
pip list --outdated

# Обновление зависимостей
pip install --upgrade -r requirements.txt

# Очистка кэша Python
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete

# Проверка БД
python -c "from models import *; print('DB OK')"
```

---

## Контакты и поддержка

- **Email**: noreply@easycyberpro.ru
- **Логирование ошибок**: `error.log`
- **Лог сервера**: `server.log`
