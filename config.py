from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    # Database
    database_url: str = "sqlite:///./app.db"

    # Security
    secret_key: str = "e7b3c9f2a1d8e6b4c5a7f9d2e8b3c6a1f4d7e9b2c5a8f1d3e6b9c2a5f8d1e4b7"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # Email
    mail_username: str = ""
    mail_password: str = ""
    mail_from: str = "noreply@easycyberpro.ru"
    mail_port: int = 587
    mail_server: str = "smtp.gmail.com"
    mail_from_name: str = "EasyCyberPro"
    mail_tls: bool = True
    mail_ssl: bool = False

    # App
    app_url: str = "http://localhost:8000"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
