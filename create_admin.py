"""
Скрипт для создания первого администратора.
Запустите: python create_admin.py
Или с аргументами: python create_admin.py email username password
"""

import sys
import os

# Добавляем путь к venv если скрипт запущен без активации
venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

from sqlalchemy.orm import Session
from models import User, SessionLocal, create_tables
from utils import get_password_hash


def create_admin(email=None, username=None, password=None):
    create_tables()

    print("=== Создание администратора ===\n")

    if not email:
        email = input("Email администратора: ").strip()
    if not username:
        username = input("Имя пользователя: ").strip()
    if not password:
        password = input("Пароль: ").strip()

    if not email or not username or not password:
        print("Все поля обязательны!")
        return

    db = SessionLocal()
    try:
        existing = db.query(User).filter((User.email == email) | (User.username == username)).first()
        if existing:
            print(f"Пользователь с таким email или именем уже существует!")
            if existing.is_admin:
                print("Он уже администратор.")
                return
            overwrite = input("Назначить его администратором? (y/n): ").strip().lower()
            if overwrite == 'y':
                existing.is_admin = True
                existing.is_verified = True
                existing.is_active = True
                db.commit()
                print(f"Пользователь {existing.username} теперь администратор!")
            return

        admin = User(
            email=email,
            username=username,
            hashed_password=get_password_hash(password),
            is_admin=True,
            is_verified=True,
            is_active=True
        )

        db.add(admin)
        db.commit()

        print(f"\n[SUCCESS] Администратор {username} успешно создан!")
        print(f"   Email: {email}")
        print(f"\nВход в админ-панель: http://localhost:8000/admin/login")

    finally:
        db.close()


if __name__ == "__main__":
    if len(sys.argv) >= 4:
        create_admin(sys.argv[1], sys.argv[2], sys.argv[3])
    else:
        create_admin()
