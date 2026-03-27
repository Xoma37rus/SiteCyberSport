"""
Тесты для API EasyCyberPro
Запуск: pytest test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from main import app
from models import Base, User, News, Discipline, Tournament, get_db
from utils import get_password_hash


# ==================== Fixture для тестовой БД ====================

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_app.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def db_session():
    """Создание тестовой БД перед каждым тестом"""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture(scope="function")
def client(db_session):
    """TestClient с переопределённой БД"""
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ==================== Helper функции ====================

def create_test_user(db, email="test@example.com", username="testuser", password="Test123!", is_admin=False, is_verified=True):
    user = User(
        email=email,
        username=username,
        hashed_password=get_password_hash(password),
        is_admin=is_admin,
        is_verified=is_verified,
        is_active=True
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def create_test_discipline(db, name="Test Discipline", slug="test-disc"):
    discipline = Discipline(name=name, slug=slug, description="Test", is_active=True)
    db.add(discipline)
    db.commit()
    db.refresh(discipline)
    return discipline


def create_test_news(db, title="Test News", author_id=1, is_published=True):
    news = News(
        title=title,
        content="Test content",
        excerpt="Test excerpt",
        author_id=author_id,
        is_published=is_published
    )
    db.add(news)
    db.commit()
    db.refresh(news)
    return news


# ==================== Тесты Health Check ====================

class TestHealthCheck:
    def test_health_endpoint(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "EasyCyberPro"

    def test_root_health(self, client):
        response = client.get("/health")
        assert response.status_code == 200


# ==================== Тесты API Новостей ====================

class TestNewsAPI:
    def test_get_news_list_empty(self, client, db_session):
        response = client.get("/api/v1/news")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []
        assert data["total"] == 0

    def test_get_news_list_with_data(self, client, db_session):
        user = create_test_user(db_session)
        create_test_news(db_session, title="News 1", author_id=user.id)
        create_test_news(db_session, title="News 2", author_id=user.id)
        create_test_news(db_session, title="News 3", author_id=user.id, is_published=False)

        response = client.get("/api/v1/news?limit=2")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2  # Только опубликованные
        assert len(data["items"]) == 2
        assert data["items"][0]["title"] == "News 2"

    def test_get_news_by_id(self, client, db_session):
        user = create_test_user(db_session)
        news = create_test_news(db_session, title="Specific News", author_id=user.id)

        response = client.get(f"/api/v1/news/{news.id}")
        assert response.status_code == 200
        assert response.json()["title"] == "Specific News"

    def test_get_news_not_found(self, client, db_session):
        response = client.get("/api/v1/news/999")
        assert response.status_code == 404


# ==================== Тесты API Дисциплин ====================

class TestDisciplinesAPI:
    def test_get_disciplines_empty(self, client, db_session):
        response = client.get("/api/v1/disciplines")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_get_disciplines_with_data(self, client, db_session):
        create_test_discipline(db_session, name="Dota 2", slug="dota2")
        create_test_discipline(db_session, name="CS2", slug="cs2")

        response = client.get("/api/v1/disciplines")
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    def test_get_discipline_by_slug(self, client, db_session):
        discipline = create_test_discipline(db_session, slug="test-slug")

        response = client.get("/api/v1/disciplines/test-slug")
        assert response.status_code == 200
        assert response.json()["slug"] == "test-slug"

    def test_get_discipline_not_found(self, client, db_session):
        response = client.get("/api/v1/disciplines/nonexistent")
        assert response.status_code == 404


# ==================== Тесты API Команд ====================

class TestTeamsAPI:
    def test_get_teams_empty(self, client, db_session):
        response = client.get("/api/v1/teams")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []


# ==================== Тесты API Турниров ====================

class TestTournamentsAPI:
    def test_get_tournaments_empty(self, client, db_session):
        response = client.get("/api/v1/tournaments")
        assert response.status_code == 200
        data = response.json()
        assert data["items"] == []

    def test_get_tournaments_filter_by_status(self, client, db_session):
        # Тест будет дополнен после создания турниров
        response = client.get("/api/v1/tournaments?status=upcoming")
        assert response.status_code == 200


# ==================== Тесты Аутентификации ====================

class TestAuthAPI:
    def test_register_page(self, client):
        response = client.get("/register")
        assert response.status_code == 200

    def test_login_page(self, client):
        response = client.get("/login")
        assert response.status_code == 200

    def test_register_validation_email(self, client, db_session):
        # Невалидный email
        response = client.post("/register", data={
            "email": "invalid-email",
            "username": "testuser",
            "password": "Test123!"
        })
        assert response.status_code == 200
        assert "Некорректный формат email" in response.text

    def test_register_validation_password(self, client, db_session):
        # Короткий пароль
        response = client.post("/register", data={
            "email": "test@example.com",
            "username": "testuser",
            "password": "123"
        })
        assert response.status_code == 200
        assert "минимум 6 символов" in response.text

    def test_register_success(self, client, db_session):
        response = client.post("/register", data={
            "email": "newuser@example.com",
            "username": "newuser",
            "password": "Test123!"
        })
        assert response.status_code == 200
        assert "успешно зарегистрирован" in response.text

        # Проверка, что пользователь создан
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.username == "newuser"


# ==================== Тесты Админ-панели ====================

class TestAdminAPI:
    def test_admin_login_page(self, client):
        response = client.get("/admin/login")
        assert response.status_code == 200

    def test_admin_login_wrong_password(self, client, db_session):
        create_test_user(db_session, email="admin@test.com", password="Correct123!", is_admin=True)

        response = client.post("/admin/login", data={
            "email": "admin@test.com",
            "password": "WrongPassword"
        })
        assert response.status_code == 200
        assert "Неверный email или пароль" in response.text

    def test_admin_login_success(self, client, db_session):
        create_test_user(db_session, email="admin@test.com", password="Admin123!", is_admin=True, is_verified=True)

        response = client.post("/admin/login", data={
            "email": "admin@test.com",
            "password": "Admin123!"
        })
        # После успешного входа - редирект или успех (зависит от реализации)
        assert response.status_code in [200, 303]
        # Проверяем, что есть cookie или редирект на /admin
        if response.status_code == 303:
            assert "admin_access_token" in response.cookies
        else:
            # Если 200, проверяем, что это админ панель
            assert "admin" in str(response.url).lower() or "admin" in response.text.lower()


# ==================== Тесты CORS ====================

class TestCORS:
    def test_cors_headers(self, client):
        response = client.options(
            "/api/v1/health",
            headers={
                "Origin": "http://localhost:8000",
                "Access-Control-Request-Method": "GET"
            }
        )
        assert response.status_code == 200


# ==================== Запуск тестов ====================

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
