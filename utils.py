from passlib.context import CryptContext
from datetime import datetime, timedelta
from typing import Optional
from jose import jwt
from config import settings
import secrets
import base64
import json
import bcrypt

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
