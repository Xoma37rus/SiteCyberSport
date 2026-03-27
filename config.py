import os
import secrets
from pydantic_settings import BaseSettings
from typing import Optional


def _generate_secret_key() -> str:
    """Генерация криптографически стойкого SECRET_KEY"""
    return secrets.token_urlsafe(32)


class Settings(BaseSettings):
    # ==================== Database ====================
    database_url: str = "sqlite:///./app.db"

    # ==================== Security ====================
    # SECRET_KEY генерируется автоматически если не задан в .env
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    admin_token_expire_hours: int = 8

    # ==================== Rate Limiting ====================
    rate_limit_per_minute: int = 10
    rate_limit_burst: int = 5

    # ==================== File Upload ====================
    max_upload_size_mb: int = 5
    allowed_image_extensions: str = ".jpg,.jpeg,.png,.gif,.webp"
    max_upload_size_bytes: int = 5 * 1024 * 1024  # 5MB

    # ==================== CSRF Protection ====================
    csrf_token_expire_seconds: int = 3600

    # ==================== Email ====================
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "noreply@easycyberpro.ru"
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "EasyCyberPro"
    mail_tls: bool = True
    mail_ssl: bool = False

    # ==================== App ====================
    app_url: str = "http://localhost:8000"
    debug: bool = False

    # ==================== Logging ====================
    log_level: str = "INFO"

    class Config:
        env_file = ".env"
        extra = "ignore"

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Генерируем SECRET_KEY если не задан
        if not self.secret_key:
            object.__setattr__(self, 'secret_key', _generate_secret_key())
            # Сохраняем в .env для последующих запусков
            self._save_secret_key()

    def _save_secret_key(self):
        """Сохранение SECRET_KEY в .env файл"""
        env_path = os.path.join(os.path.dirname(__file__), '.env')
        try:
            lines = []
            secret_saved = False
            if os.path.exists(env_path):
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        if line.startswith('SECRET_KEY='):
                            secret_saved = True
                            continue
                        lines.append(line)

            if not secret_saved:
                lines.append(f'\nSECRET_KEY={self.secret_key}\n')

            with open(env_path, 'w', encoding='utf-8') as f:
                f.writelines(lines)
        except Exception as e:
            print(f"Warning: Could not save SECRET_KEY to .env: {e}")


settings = Settings()
