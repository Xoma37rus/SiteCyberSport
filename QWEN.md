# EasyCyberPro — Киберспортивная платформа

## Обзор проекта

**EasyCyberPro** — это полнофункциональная веб-платформа для организации и участия в киберспортивных турнирах. Платформа предоставляет возможности для регистрации пользователей, создания и управления командами, участия в турнирах по различным дисциплинам (Dota 2, Counter-Strike 2, Мир Танков), а также мощную админ-панель для управления всем контентом.

### Основной стек технологий

| Компонент | Технология |
|-----------|------------|
| Backend | FastAPI (Python 3.9+) |
| Database | SQLAlchemy + SQLite |
| Migrations | Alembic |
| Templates | Jinja2 |
| Authentication | JWT (python-jose) |
| Password Hashing | bcrypt |
| Email | fastapi-mail (SMTP) |
| Frontend | HTML5, CSS3, Vanilla JS |

### Архитектура проекта

```
web_app/
├── main.py                    # Точка входа, регистрация роутеров
├── config.py                  # Конфигурация через pydantic-settings
├── models.py                  # SQLAlchemy модели (10 моделей)
├── schemas.py                 # Pydantic схемы для API
│
├── auth.py                    # Аутентификация пользователей
├── admin.py                   # Админ-панель (пользователи, логи)
├── admin_teams.py             # CRUD команд (админ)
├── admin_tournaments.py       # CRUD турниров + заявки (админ)
├── news.py                    # Роутер новостей
├── disciplines.py             # Роутер дисциплин
├── tournaments.py             # Роутер турниров (пользователи)
├── api.py                     # REST API endpoints (/api/v1/...)
│
├── mailer.py                  # Отправка email (верификация, уведомления)
├── utils.py                   # Утилиты (хеширование, JWT, CSRF, flash)
│
├── seed_data.py               # Скрипт наполнения БД тестовыми данными
├── test_site.py               # Скрипт тестирования функционала
├── create_admin.py            # Скрипт создания администратора
├── reset_admin_password.py    # Скрипт сброса пароля админа
├── backup_db.py               # Резервное копирование БД
│
├── templates/                 # Jinja2 шаблоны
│   ├── index.html             # Главная страница
│   ├── login.html             # Вход
│   ├── register.html          # Регистрация
│   ├── dashboard.html         # Личный кабинет
│   ├── my_tournaments.html    # Мои турниры
│   ├── news.html              # Список новостей
│   ├── news_detail.html       # Детальная новость
│   ├── tournaments.html       # Турниры (с поиском и фильтрами)
│   ├── tournament_detail.html # Детали турнира + регистрация
│   ├── discipline.html        # Страница дисциплины
│   ├── about.html             # О проекте
│   ├── verify.html            # Подтверждение email
│   └── admin/                 # Админ-панель
│       ├── dashboard.html     # Главная админки
│       ├── login.html         # Вход администратора
│       ├── users.html         # Управление пользователями
│       ├── logs.html          # Логи действий
│       ├── news_list.html     # Новости (список)
│       ├── news_form.html     # Новости (форма)
│       ├── teams_list.html    # Команды (список)
│       ├── teams_form.html    # Команды (форма)
│       ├── tournaments_list.html      # Турниры (список)
│       ├── tournaments_form.html      # Турниры (форма)
│       └── tournament_participations.html # Заявки на турнир
│
├── static/                    # Статические файлы
│   ├── style.css              # Основные стили
│   ├── images/                # Изображения
│   └── uploads/               # Загруженные файлы
│
├── alembic/                   # Миграции базы данных
│   ├── versions/              # Файлы миграций
│   └── env.py                 # Конфигурация Alembic
│
├── backups/                   # Резервные копии БД
├── venv/                      # Виртуальное окружение Python
├── .env                       # Переменные окружения
├── alembic.ini                # Конфигурация Alembic
└── requirements.txt           # Зависимости Python
```

## Установка и запуск

### Требования

- Python 3.9+
- pip

### Установка зависимостей

```bash
cd C:\Users\User\web_app
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

### Конфигурация

Отредактируйте файл `.env` для настройки email-рассылки и других параметров:

```env
# Email (Gmail)
MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_FROM=noreply@easycyberpro.ru
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# Приложение
APP_URL=http://localhost:8000
SECRET_KEY=e7b3c9f2a1d8e6b4c5a7f9d2e8b3c6a1f4d7e9b2c5a8f1d3e6b9c2a5f8d1e4b7
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Database
DATABASE_URL=sqlite:///./app.db
```

> **Для Gmail:** Включите 2FA и создайте пароль приложения: https://myaccount.google.com/apppasswords

### Запуск сервера

```bash
# Через main.py
python main.py

# Или через uvicorn
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Сервер будет доступен по адресу: **http://localhost:8000**

### Миграции базы данных

```bash
# Применить все миграции
alembic upgrade head

# Создать новую миграцию после изменений в моделях
alembic revision --autogenerate -m "Описание изменений"

# Откатить последнюю миграцию
alembic downgrade -1
```

### Инициализация данных

```bash
# Создание тестовых данных (команды, турниры)
python seed_data.py

# Полное тестирование (создание пользователя и админа)
python test_site.py
```

### Данные для входа (после test_site.py)

| Роль | Email | Пароль | URL |
|------|-------|--------|-----|
| Пользователь | test@example.com | Test123! | /login |
| Администратор | admin@easycyberpro.ru | Admin123! | /admin/login |

## API Endpoints

### Health Check
- `GET /health` — Проверка статуса сервиса
- `GET /api/v1/health` — API версия (с номером версии)

### Новости
- `GET /api/v1/news` — Список новостей (пагинация: page, limit)
- `GET /api/v1/news/{id}` — Детальная новость

### Дисциплины
- `GET /api/v1/disciplines` — Все активные дисциплины
- `GET /api/v1/disciplines/{slug}` — Дисциплина по slug (dota2, cs2, tanks)

### Команды
- `GET /api/v1/teams` — Список команд (фильтр: discipline, пагинация)
- `GET /api/v1/teams/{id}` — Детали команды

### Турниры
- `GET /api/v1/tournaments` — Список турниров (фильтры: status, discipline)
- `GET /api/v1/tournaments/{id}` — Детали турнира

## Модели данных

### User (Пользователь)
- `id`, `email`, `username`, `hashed_password`
- `is_active`, `is_verified`, `is_admin`
- `verification_token`, `created_at`

### News (Новость)
- `id`, `title`, `content`, `excerpt`, `image_url`
- `author_id`, `is_published`, `created_at`, `updated_at`

### Discipline (Дисциплина)
- `id`, `name`, `slug`, `description`, `icon`
- `is_active`, `created_at`

### Team (Команда)
- `id`, `name`, `discipline_id`, `captain_id`
- `description`, `logo_url`, `wins`, `losses`, `rating`
- `is_active`, `created_at`
- **Property:** `win_rate` — процент побед (вычисляется)

### TeamMember (Участник команды)
- `id`, `team_id`, `user_id`, `player_name`, `role`
- `joined_at`

### Tournament (Турнир)
- `id`, `name`, `discipline_id`, `description`
- `prize_pool`, `max_teams`, `registration_deadline`
- `start_date`, `end_date`, `status`, `format`
- `is_online`, `image_url`, `created_at`, `updated_at`
- **Property:** `registered_teams_count` — количество подтверждённых команд

### TournamentParticipation (Заявка на турнир)
- `id`, `tournament_id`, `team_id`, `user_id`
- `is_confirmed`, `registered_at`

### Match (Матч турнирной сетки)
- `id`, `tournament_id`, `team1_id`, `team2_id`, `winner_id`
- `team1_score`, `team2_score`
- `round`, `match_order`, `status`
- `scheduled_at`, `created_at`, `next_match_id`

### AdminLog (Лог действий администратора)
- `id`, `admin_id`, `action`, `target_type`, `target_id`
- `details`, `ip_address`, `created_at`

## Функциональные возможности

### Для пользователей
- ✅ Регистрация и аутентификация (JWT в HttpOnly cookie)
- ✅ Подтверждение email (токен)
- ✅ Личный кабинет (dashboard)
- ✅ Страница "Мои турниры" — отслеживание заявок
- ✅ Просмотр новостей, турниров, дисциплин
- ✅ Регистрация команды на турнир (с модальным окном подтверждения)
- ✅ Автоматический расчёт винрейта команды

### Для администраторов
- ✅ Админ-панель с навигацией по всем разделам
- ✅ Управление пользователями (активация, права админа, удаление)
- ✅ Управление новостями (CRUD)
- ✅ Управление командами (CRUD, фильтр по дисциплинам)
- ✅ Управление турнирами (CRUD, валидация дат)
- ✅ Управление заявками на турниры (подтвердить/отказать с причиной)
- ✅ Просмотр логов действий администраторов
- ✅ CSRF-защита всех форм
- ✅ Flash-сообщения об операциях

### Email-уведомления
- ✅ Подтверждение регистрации
- ✅ Подача заявки на турнир
- ✅ Подтверждение участия в турнире
- ✅ Отказ в участии (с указанием причины)

### Безопасность
- ✅ Хеширование паролей (bcrypt)
- ✅ JWT-аутентификация (HttpOnly cookie)
- ✅ CSRF-токены для всех POST-запросов
- ✅ Разделение прав (пользователь / админ)
- ✅ Логирование действий администраторов
- ✅ Валидация дат турниров

## Разработка

### Структура роутеров

| Роутер | Префикс | Описание |
|--------|---------|----------|
| `auth_router` | — | Регистрация, вход, выход, dashboard, мои турниры |
| `admin_router` | /admin | Админ-панель (пользователи, логи) |
| `teams_router` | /admin/teams | Управление командами |
| `admin_tournaments_router` | /admin/tournaments | Управление турнирами и заявками |
| `news_router` | /news | Новости |
| `disciplines_router` | /discipline | Дисциплины |
| `tournaments_router` | /tournament | Турниры (публичные страницы) |
| `api_router` | /api/v1 | REST API |

### CORS настройка

Разрешены запросы с:
- `http://localhost:8000`
- `http://127.0.0.1:8000`

Credentials включены для поддержки cookie.

### Шаблоны

Jinja2 настроен с отключенным кэшированием для разработки:
- `auto_reload = True`
- `cache_size = 0`
- `ChoiceLoader` для гибкой загрузки шаблонов

### Оптимизация запросов

Используется `joinedload` для избежания N+1 запросов:
- Загрузка дисциплин с турнирами и командами
- Загрузка турниров с дисциплинами и заявками
- Загрузка заявок с командами и капитанами

## Скрипты утилит

| Скрипт | Описание |
|--------|----------|
| `test_site.py` | Полное тестирование: создание пользователя, админа, новости, турнира, команды |
| `seed_data.py` | Наполнение БД тестовыми командами (15) и турнирами (4) |
| `create_admin.py` | Создание администратора через CLI |
| `reset_admin_password.py` | Сброс пароля администратора |
| `backup_db.py` | Резервное копирование БД с timestamp |

## Дисциплины (по умолчанию)

| Название | Slug | Иконка |
|----------|------|--------|
| Dota 2 | dota2 | ⚔️ |
| Counter-Strike 2 | cs2 | 🔫 |
| Мир Танков | tanks | 🛡️ |

## Форматы турниров

- `single_elimination` — Одиночная сетка плей-офф
- `double_elimination` — Двойная сетка
- `round_robin` — Круговая система
- `swiss` — Швейцарская система

## Статусы турниров

- `upcoming` — Предстоящий
- `registration` — Открыта регистрация
- `active` — Активный
- `completed` — Завершён
- `cancelled` — Отменён

## Страницы проекта

### Публичные
- `/` — Главная (новости, дисциплины, турниры)
- `/news` — Все новости
- `/news/{id}` — Детальная новость
- `/tournaments` — Все турниры (с поиском, фильтрами, пагинацией, архивом)
- `/tournament/{id}` — Детали турнира + регистрация
- `/discipline/{slug}` — Страница дисциплины (команды, статистика)
- `/about` — О проекте

### Авторизация
- `/login` — Вход
- `/register` — Регистрация
- `/verify` — Подтверждение email
- `/dashboard` — Личный кабинет
- `/my-tournaments` — Мои турниры (заявки пользователя)

### Админ-панель
- `/admin` — Главная (статистика, последние пользователи)
- `/admin/login` — Вход администратора
- `/admin/news` — Новости (список)
- `/admin/news/create` — Создать новость
- `/admin/news/{id}/edit` — Редактировать новость
- `/admin/teams` — Команды (список с фильтром)
- `/admin/teams/create` — Создать команду
- `/admin/teams/{id}/edit` — Редактировать команду
- `/admin/tournaments` — Турниры (список с фильтрами)
- `/admin/tournaments/create` — Создать турнир
- `/admin/tournaments/{id}/edit` — Редактировать турнир
- `/admin/tournaments/{id}/participations` — Заявки на турнир
- `/admin/users` — Пользователи (с поиском)
- `/admin/logs` — Логи действий

## UX/UI особенности

- 🎨 Тёмная тема с акцентными цветами (cyan, blue, purple)
- 📱 Адаптивный дизайн
- 🔔 Flash-сообщения об операциях
- ⏳ Индикатор загрузки при отправке форм
- 🗂️ Модальные окна подтверждения
- 🎯 Цветовая индикация статусов (зелёный/жёлтый/красный)
- 📊 Таблицы с сортировкой и пагинацией

## Примечания

- База данных SQLite хранится в `app.db`
- Авто-верификация пользователей включена для локальной разработки
- Email-рассылка опциональна (не критична для работы)
- Резервные копии БД сохраняются в папку `backups/`
- Миграции управляются через Alembic
