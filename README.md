# 🚀 EasyCyberPro — Киберспортивная платформа

**Версия:** 2.0  
**Дата обновления:** 1 апреля 2026 г.

[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-blue.svg)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.10+-green.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-Proprietary-red.svg)]()

---

## 📋 Содержание

1. [О проекте](#о-проекте)
2. [Возможности](#возможности)
3. [Технологический стек](#технологический-стек)
4. [Быстрый старт](#быстрый-старт)
5. [Установка](#установка)
6. [Конфигурация](#конфигурация)
7. [Запуск](#запуск)
8. [Миграции БД](#миграции-бд)
9. [API Документация](#api-документация)
10. [Тестирование](#тестирование)
11. [Развёртывание](#развёртывание)
12. [Структура проекта](#структура-проекта)
13. [Документация](#документация)
14. [План развития](#план-развития)
15. [Поддержка](#поддержка)

---

## 📖 О проекте

**EasyCyberPro** — это веб-платформа для киберспортивных соревнований, позволяющая:

- 🎮 Организовывать турниры по Dota 2, CS2, Мир танков
- 👥 Управлять командами и игроками
- 📊 Вести рейтинг игроков (ELO система)
- 🏆 Проводить турниры с турнирными сетками
- 🎓 Обучаться у тренеров (уникальная фича!)
- 📰 Публиковать новости киберспорта

### Целевая аудитория

- **Игроки:** Любители киберспорта, желающие развиваться
- **Команды:** Любительские и полу-профессиональные составы
- **Тренеры:** Специалисты, обучающие игроков
- **Организаторы:** Проведение турниров любого масштаба

---

## ✨ Возможности

### ✅ Реализованный функционал

| Модуль | Функции |
|--------|---------|
| **Аутентификация** | Регистрация, вход, logout, восстановление пароля, email-верификация |
| **Профиль** | Аватар, био, соцсети, дисциплины, настройки приватности |
| **Рейтинг ELO** | 10 уровней, таблица лидеров, история изменений |
| **Турниры** | Каталог, фильтрация, регистрация, турнирные сетки |
| **Команды** | Создание, управление, участники, статистика |
| **Тренерская система** | Ученики, тренировки, посещаемость, заметки |
| **Новости** | CRUD, загрузка изображений, публикация |
| **Админ-панель** | Пользователи, турниры, команды, логи действий |
| **REST API** | Полноценное API v1 для всех сущностей |
| **Email-рассылка** | Верификация, уведомления, сброс пароля |

### 🔜 В разработке

- [ ] Автоматический матчмейкинг
- [ ] Интеграция со Steam API
- [ ] Discord-интеграция
- [ ] Мобильное приложение
- [ ] Premium-подписка

---

## 🛠️ Технологический стек

### Backend

| Технология | Версия | Назначение |
|------------|--------|------------|
| **Python** | 3.10+ | Язык программирования |
| **FastAPI** | 0.100+ | Веб-фреймворк |
| **SQLAlchemy** | 2.0+ | ORM для работы с БД |
| **Alembic** | 1.12+ | Миграции базы данных |
| **Pydantic** | 2.0+ | Валидация данных |
| **Jinja2** | 3.1+ | Шаблонизатор HTML |

### Безопасность

| Технология | Назначение |
|------------|------------|
| **bcrypt** | Хеширование паролей |
| **python-jose** | JWT токены |
| **SlowAPI** | Rate limiting |

### База данных

| Технология | Назначение |
|------------|------------|
| **SQLite** | Разработка (по умолчанию) |
| **PostgreSQL** | Production (рекомендуется) |

### Frontend

| Технология | Назначение |
|------------|------------|
| **HTML5** | Разметка |
| **CSS3** | Стили (темная тема) |
| **JavaScript** | Интерактивность |
| **Bracket Viewer** | Визуализация турнирных сеток |

---

## 🚀 Быстрый старт

```bash
# Клонирование репозитория
git clone <repository-url>
cd web_app

# Создание виртуального окружения
python -m venv venv

# Активация виртуального окружения
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Установка зависимостей
pip install -r requirements.txt

# Копирование .env.example в .env
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac

# Запуск сервера
python main.py
```

Откройте браузер: **http://localhost:8000**

---

## 📦 Установка

### Требования

- Python 3.10 или выше
- pip (менеджер пакетов Python)
- Git

### Шаг 1: Установка Python

**Windows:**
```powershell
# Скачайте установщик с python.org
# Запустите установщик, отметьте "Add Python to PATH"
```

**Linux (Ubuntu/Debian):**
```bash
sudo apt update
sudo apt install python3.10 python3-pip
```

**Mac:**
```bash
brew install python@3.10
```

### Шаг 2: Клонирование проекта

```bash
git clone <repository-url>
cd web_app
```

### Шаг 3: Создание виртуального окружения

```bash
# Windows
python -m venv venv
venv\Scripts\activate

# Linux/Mac
python3 -m venv venv
source venv/bin/activate
```

### Шаг 4: Установка зависимостей

```bash
pip install -r requirements.txt
```

### Шаг 5: Настройка окружения

```bash
# Скопируйте пример конфигурации
copy .env.example .env  # Windows
cp .env.example .env    # Linux/Mac
```

---

## ⚙️ Конфигурация

### Файл .env

```ini
# ==================== Email (Gmail) ====================
# Для работы email-рассылки:
# 1. Включите 2FA в аккаунте Google
# 2. Создайте пароль приложения: https://myaccount.google.com/apppasswords
# 3. Вставьте его в MAIL_PASSWORD

MAIL_USERNAME=your_email@gmail.com
MAIL_PASSWORD=your_app_password_here
MAIL_FROM=noreply@easycyberpro.ru
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587

# ==================== Приложение ====================
APP_URL=http://localhost:8000
SECRET_KEY=your_secret_key_here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
ADMIN_TOKEN_EXPIRE_HOURS=8

# ==================== Database ====================
DATABASE_URL=sqlite:///./app.db

# Для PostgreSQL:
# DATABASE_URL=postgresql://user:password@localhost:5432/easycyberpro

# ==================== Rate Limiting ====================
RATE_LIMIT_PER_MINUTE=10
RATE_LIMIT_BURST=5

# ==================== File Upload ====================
MAX_UPLOAD_SIZE_MB=5
ALLOWED_IMAGE_EXTENSIONS=.jpg,.jpeg,.png,.gif,.webp

# ==================== Logging ====================
LOG_LEVEL=INFO

# ==================== Debug ====================
DEBUG=false
```

### Генерация SECRET_KEY

```python
import secrets
print(secrets.token_urlsafe(32))
```

Или используйте встроенную генерацию (при первом запуске).

---

## ▶️ Запуск

### Режим разработки

```bash
# С авто-перезагрузкой при изменениях
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Или через main.py
python main.py
```

### Production режим

```bash
# Без авто-перезагрузки
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4

# С логированием
uvicorn main:app --host 0.0.0.0 --port 8000 --log-level info
```

### Через Gunicorn (рекомендуется для production)

```bash
pip install gunicorn

gunicorn main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

---

## 🗄️ Миграции БД

### Alembic настройка

```bash
# Инициализация Alembic (если не настроен)
alembic init alembic

# Создание первой миграции
alembic revision --autogenerate -m "Initial migration"

# Применение миграций
alembic upgrade head
```

### Основные команды

| Команда | Описание |
|---------|----------|
| `alembic revision --autogenerate -m "msg"` | Создать миграцию |
| `alembic upgrade head` | Применить все миграции |
| `alembic downgrade -1` | Откатить одну миграцию |
| `alembic history` | История миграций |
| `alembic current` | Текущая версия БД |

### Автоматическое создание таблиц

При первом запуске таблицы создаются автоматически:

```python
# main.py
try:
    create_tables()
    init_disciplines()
    logger.info("Database tables created and disciplines initialized")
except Exception as e:
    logger.error(f"Database initialization error: {e}")
    raise
```

---

## 📡 API Документация

FastAPI автоматически генерирует интерактивную документацию:

| Документация | URL |
|--------------|-----|
| **Swagger UI** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **OpenAPI JSON** | http://localhost:8000/openapi.json |

### Основные endpoints

#### Аутентификация

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/register` | GET/POST | Регистрация |
| `/login` | GET/POST | Вход |
| `/logout` | GET | Выход |
| `/forgot-password` | GET/POST | Восстановление пароля |

#### API v1

| Endpoint | Метод | Описание |
|----------|-------|----------|
| `/api/v1/auth/me` | GET | Текущий пользователь |
| `/api/v1/leaderboard` | GET | Таблица лидеров |
| `/api/v1/tournaments/{id}/bracket` | GET | Турнирная сетка |
| `/api/v1/matchmaking/queue` | POST | Встать в очередь матчмейкинга |

### Пример запроса

```bash
# Получить таблицу лидеров по CS2
curl -X GET "http://localhost:8000/api/v1/leaderboard?discipline=cs2&limit=50" \
  -H "Accept: application/json"
```

---

## 🧪 Тестирование

### Запуск тестов

```bash
# Все тесты
pytest

# С выводом информации
pytest -v

# С покрытием кода
pytest --cov=.

# Конкретный тест
pytest test_db.py -v
```

### Покрытие кода

```bash
# Установка pytest-cov
pip install pytest-cov

# Запуск с отчётом
pytest --cov=. --cov-report=html

# Отчёт откроется в: htmlcov/index.html
```

---

## 🌐 Развёртывание

### Docker (рекомендуется)

**Dockerfile:**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

**docker-compose.yml:**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - ./app.db:/app/app.db
    environment:
      - DATABASE_URL=sqlite:///./app.db
    command: uvicorn main:app --host 0.0.0.0 --port 8000

  # Для production с PostgreSQL:
  db:
    image: postgres:14
    environment:
      POSTGRES_DB: easycyberpro
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data

volumes:
  postgres_data:
```

**Запуск:**
```bash
docker-compose up -d
```

### VPS (Ubuntu 20.04+)

```bash
# Установка зависимостей
sudo apt update
sudo apt install -y python3.10 python3-pip nginx supervisor git

# Клонирование проекта
git clone <repository-url> /var/www/easycyberpro
cd /var/www/easycyberpro

# Виртуальное окружение
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Настройка Supervisor
sudo nano /etc/supervisor/conf.d/easycyberpro.conf
```

**/etc/supervisor/conf.d/easycyberpro.conf:**
```ini
[program:easycyberpro]
command=/var/www/easycyberpro/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000
directory=/var/www/easycyberpro
user=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/easycyberpro/out.log
```

```bash
# Перезапуск Supervisor
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start easycyberpro

# Настройка Nginx
sudo nano /etc/nginx/sites-available/easycyberpro
```

**/etc/nginx/sites-available/easycyberpro:**
```nginx
server {
    listen 80;
    server_name easycyberpro.ru;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /static {
        alias /var/www/easycyberpro/static;
    }
}
```

```bash
# Включение сайта
sudo ln -s /etc/nginx/sites-available/easycyberpro /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## 📁 Структура проекта

```
web_app/
├── main.py                 # Точка входа, инициализация FastAPI
├── config.py               # Настройки через pydantic-settings
├── models.py               # SQLAlchemy модели БД
├── schemas.py              # Pydantic схемы для API
├── utils.py                # Утилиты (хеширование, JWT, ELO)
├── auth.py                 # Аутентификация, регистрация
├── api.py                  # REST API v1 endpoints
├── leaderboard.py          # Таблица лидеров
│
├── admin.py                # Админ-панель: пользователи
├── admin_teams.py          # Админ-панель: команды
├── admin_tournaments.py    # Админ-панель: турниры
├── admin_coaches.py        # Админ-панель: тренеры
│
├── news.py                 # Новости
├── disciplines.py          # Дисциплины
├── tournaments.py          # Турниры для пользователей
├── profile.py              # Профиль пользователя
├── coach.py                # Тренерская система
│
├── alembic/                # Миграции БД
├── templates/              # Jinja2 HTML-шаблоны
│   ├── includes/           # Части шаблонов (navbar, footer)
│   ├── admin/              # Шаблоны админ-панели
│   ├── coach/              # Шаблоны тренера
│   └── *.html              # Основные шаблоны
├── static/                 # Статические файлы
│   ├── style.css           # Основные стили
│   ├── bracket.js          # Визуализация турнирных сеток
│   ├── images/             # Изображения
│   └── uploads/            # Загруженные файлы
│
├── requirements.txt        # Зависимости
├── .env                    # Переменные окружения
├── .env.example            # Пример конфигурации
├── pytest.ini              # Настройки тестов
│
├── QWEN.md                 # Контекст для разработчиков
├── USER_GUIDE.md           # Документация пользователя
├── COMPETITIVE_ANALYSIS.md # Анализ конкурентов
└── README.md               # Этот файл
```

---

## 📚 Документация

| Документ | Описание |
|----------|----------|
| **[USER_GUIDE.md](USER_GUIDE.md)** | Полное руководство пользователя |
| **[QWEN.md](QWEN.md)** | Контекст для разработчиков |
| **[COMPETITIVE_ANALYSIS.md](COMPETITIVE_ANALYSIS.md)** | Анализ конкурентов и план развития |
| **[/docs](http://localhost:8000/docs)** | API документация (Swagger) |

---

## 📈 План развития

### Фаза 1: Критические улучшения ✅

- [x] Система рейтинга ELO
- [x] Таблица лидеров
- [x] Визуализация турнирных сеток
- [x] Матчмейкинг (базовый)

### Фаза 2: Важные улучшения 🔜

- [ ] Discord-интеграция
- [ ] Расширенная статистика
- [ ] Интеграция со Steam API

### Фаза 3: Монетизация 📅

- [ ] Premium-подписка
- [ ] Система наград
- [ ] Мобильное приложение

---

## 🐛 Решение проблем

### Ошибка: "ModuleNotFoundError: No module named 'xxx'"

```bash
# Убедитесь, что виртуальное окружение активировано
venv\Scripts\activate  # Windows
source venv/bin/activate  # Linux/Mac

# Переустановите зависимости
pip install -r requirements.txt
```

### Ошибка: "DATABASE_URL is not set"

```bash
# Проверьте наличие .env файла
# Убедитесь, что DATABASE_URL указан
```

### Ошибка: "Address already in use"

```bash
# Найдите процесс на порту 8000
# Windows:
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :8000
kill -9 <PID>
```

### Ошибка: "CSRF token mismatch"

```bash
# Очистите cookie браузера
# Перезагрузите страницу
```

---

## 🤝 Поддержка

### Контакты

- **Email:** support@easycyberpro.ru
- **Discord:** https://discord.gg/easycyberpro
- **Telegram:** @easycyberpro_support

### Ресурсы

- **Официальный сайт:** https://easycyberpro.ru
- **Документация:** https://docs.easycyberpro.ru
- **GitHub:** https://github.com/easycyberpro/web_app

---

## 📄 Лицензия

EasyCyberPro — проприетарное программное обеспечение.

Все права защищены © 2026 EasyCyberPro.

---

**Создано с ❤️ для киберспорта**
