"""
Сброс пароля администратора
"""
import sys, os
venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

from sqlalchemy.orm import Session
from models import SessionLocal, User
from utils import get_password_hash

db = SessionLocal()
try:
    admin = db.query(User).filter(User.email == "admin@easycyberpro.ru").first()
    if admin:
        admin.hashed_password = get_password_hash("Admin123!")
        admin.is_admin = True
        admin.is_verified = True
        admin.is_active = True
        db.commit()
        print("✅ Пароль администратора обновлён!")
        print("   Email: admin@easycyberpro.ru")
        print("   Пароль: Admin123!")
    else:
        print("❌ Администратор не найден")
except Exception as e:
    db.rollback()
    print(f"❌ Ошибка: {e}")
finally:
    db.close()
