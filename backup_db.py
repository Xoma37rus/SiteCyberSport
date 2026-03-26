"""
Скрипт для резервного копирования базы данных
Запустите: python backup_db.py
Бэкапы сохраняются в папку backups/
"""

import os
import sys
import shutil
from datetime import datetime

# Добавляем путь к venv если скрипт запущен без активации
venv_path = os.path.join(os.path.dirname(__file__), 'venv', 'Lib', 'site-packages')
if os.path.exists(venv_path):
    sys.path.insert(0, venv_path)

# Пути
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'app.db')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups')


def create_backup():
    """Создание резервной копии БД"""
    
    # Создаём папку для бэкапов если не существует
    if not os.path.exists(BACKUP_DIR):
        os.makedirs(BACKUP_DIR)
        print(f"📁 Создана папка для бэкапов: {BACKUP_DIR}")
    
    # Проверяем существование БД
    if not os.path.exists(DB_PATH):
        print("❌ База данных не найдена!")
        return False
    
    # Генерируем имя файла с датой и временем
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_filename = f'app_backup_{timestamp}.db'
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    try:
        # Копируем файл БД
        shutil.copy2(DB_PATH, backup_path)
        
        # Получаем размер файла
        file_size = os.path.getsize(backup_path)
        size_mb = file_size / (1024 * 1024)
        
        print(f"\n✅ Бэкап успешно создан!")
        print(f"📦 Файл: {backup_filename}")
        print(f"📊 Размер: {size_mb:.2f} MB")
        print(f"📁 Путь: {backup_path}")
        
        # Очищаем старые бэкапы (храним последние 10)
        cleanup_old_backups()
        
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка создания бэкапа: {e}")
        return False


def cleanup_old_backups(keep=10):
    """Удаление старых бэкапов, оставляем только последние N"""
    try:
        # Получаем список всех бэкапов
        backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('app_backup_') and f.endswith('.db')]
        
        if len(backups) > keep:
            # Сортируем по имени (дата в имени)
            backups.sort(reverse=True)
            
            # Удаляем старые
            for old_backup in backups[keep:]:
                old_path = os.path.join(BACKUP_DIR, old_backup)
                os.remove(old_path)
                print(f"🗑️ Удалён старый бэкап: {old_backup}")
    
    except Exception as e:
        print(f"⚠️ Ошибка очистки старых бэкапов: {e}")


def list_backups():
    """Показать список всех бэкапов"""
    if not os.path.exists(BACKUP_DIR):
        print("📁 Папка бэкапов не найдена")
        return
    
    backups = [f for f in os.listdir(BACKUP_DIR) if f.startswith('app_backup_') and f.endswith('.db')]
    
    if not backups:
        print("📁 Бэкапов пока нет")
        return
    
    print(f"\n📦 Доступные бэкапы ({len(backups)}):")
    print("-" * 60)
    
    for i, backup in enumerate(sorted(backups, reverse=True), 1):
        backup_path = os.path.join(BACKUP_DIR, backup)
        file_size = os.path.getsize(backup_path) / (1024 * 1024)
        modified = datetime.fromtimestamp(os.path.getmtime(backup_path)).strftime('%d.%m.%Y %H:%M')
        print(f"  {i}. {backup} ({file_size:.2f} MB) - {modified}")


def restore_backup(backup_filename):
    """Восстановление из бэкапа"""
    backup_path = os.path.join(BACKUP_DIR, backup_filename)
    
    if not os.path.exists(backup_path):
        print(f"❌ Бэкап не найден: {backup_filename}")
        return False
    
    try:
        # Создаём бэкап текущей БД перед восстановлением
        if os.path.exists(DB_PATH):
            create_backup()
        
        # Восстанавливаем
        shutil.copy2(backup_path, DB_PATH)
        print(f"\n✅ База данных восстановлена из: {backup_filename}")
        return True
        
    except Exception as e:
        print(f"\n❌ Ошибка восстановления: {e}")
        return False


def print_help():
    """Показать справку"""
    print("""
📊 Резервное копирование базы данных EasyCyberPro

Использование:
    python backup_db.py              - Создать бэкап
    python backup_db.py list         - Показать список бэкапов
    python backup_db.py restore FILE - Восстановить из бэкапа
    python backup_db.py help         - Показать эту справку

Примеры:
    python backup_db.py
    python backup_db.py list
    python backup_db.py restore app_backup_20260323_120000.db
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Без аргументов - создаём бэкап
        create_backup()
    elif sys.argv[1] == 'list':
        list_backups()
    elif sys.argv[1] == 'restore':
        if len(sys.argv) < 3:
            print("❌ Укажите имя файла бэкапа")
            print("   Пример: python backup_db.py restore app_backup_20260323_120000.db")
        else:
            restore_backup(sys.argv[2])
    elif sys.argv[1] == 'help':
        print_help()
    else:
        print(f"❌ Неизвестная команда: {sys.argv[1]}")
        print_help()
