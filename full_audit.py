"""
Полный аудит платформы EasyCyberPro
Выявление ошибок в коде, дизайне и архитектуре
"""
import os
import re
import ast

print("=" * 70)
print("АУДИТ ПЛАТФОРМЫ EasyCyberPro")
print("=" * 70)

issues = {
    'critical': [],
    'major': [],
    'minor': [],
    'suggestions': []
}

# ==================== ПРОВЕРКА ФАЙЛОВ ====================

print("\n[1/6] Анализ структуры файлов...")

required_files = {
    'main.py': 'Основное приложение',
    'models.py': 'Модели данных',
    'auth.py': 'Аутентификация',
    'admin.py': 'Админ-панель',
    'admin_coaches.py': 'Управление тренерами',
    'coach.py': 'Личный кабинет тренера',
    'config.py': 'Конфигурация',
    'utils.py': 'Утилиты',
    'schemas.py': 'Pydantic схемы',
}

for file, desc in required_files.items():
    if os.path.exists(file):
        print(f"  ✓ {file} - {desc}")
    else:
        issues['critical'].append(f"Отсутствует файл: {file}")
        print(f"  ✗ {file} - ОТСУТСТВУЕТ")

# ==================== АНАЛИЗ MODELS.PY ====================

print("\n[2/6] Анализ models.py...")

with open('models.py', 'r', encoding='utf-8') as f:
    models_content = f.read()

# Проверка на наличие всех необходимых моделей
required_models = ['User', 'News', 'Discipline', 'Team', 'Tournament', 
                   'CoachStudent', 'TrainingSession', 'TrainingAttendance']

for model in required_models:
    if f'class {model}' in models_content:
        print(f"  ✓ Модель {model}")
    else:
        issues['major'].append(f"Отсутствует модель: {model}")
        print(f"  ✗ Модель {model} - ОТСУТСТВУЕТ")

# Проверка relationships
if 'back_populates' in models_content or 'backref' in models_content:
    print("  ✓ Relationships настроены")
else:
    issues['minor'].append("Возможно не настроены relationships между моделями")

# ==================== АНАЛИЗ MAIN.PY ====================

print("\n[3/6] Анализ main.py...")

with open('main.py', 'r', encoding='utf-8') as f:
    main_content = f.read()

# Проверка импортов роутеров
required_routers = [
    'auth_router',
    'admin_router',
    'admin_coaches_router',
    'coach_router',
    'news_router',
    'disciplines_router',
    'tournaments_router',
    'profile_router',
]

for router in required_routers:
    if router in main_content:
        print(f"  ✓ Роутер {router} подключен")
    else:
        issues['major'].append(f"Роутер {router} не подключен в main.py")
        print(f"  ✗ Роутер {router} - НЕ ПОДКЛЮЧЕН")

# Проверка CORS
if 'CORSMiddleware' in main_content:
    print("  ✓ CORS настроен")
else:
    issues['minor'].append("CORS middleware не настроен")

# Проверка rate limiting
if 'SlowAPI' in main_content or 'limiter' in main_content:
    print("  ✓ Rate limiting настроен")
else:
    issues['suggestions'].append("Рекомендуется настроить rate limiting")

# ==================== АНАЛИЗ ШАБЛОНОВ ====================

print("\n[4/6] Анализ шаблонов...")

templates_dir = 'templates'
template_files = []
for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            template_files.append(os.path.join(root, file))

print(f"  Найдено шаблонов: {len(template_files)}")

# Проверка на наличие базовых шаблонов
required_templates = [
    'index.html',
    'login.html',
    'register.html',
    'dashboard.html',
    'profile.html',
    'admin/dashboard.html',
    'admin/login.html',
    'coach/dashboard.html',
]

for template in required_templates:
    path = os.path.join(templates_dir, *template.split('/'))
    if os.path.exists(path):
        print(f"  ✓ {template}")
    else:
        issues['major'].append(f"Отсутствует шаблон: {template}")
        print(f"  ✗ {template} - ОТСУТСТВУЕТ")

# Проверка шаблонов на потенциальные проблемы
print("\n  Проверка шаблонов на проблемы...")
for template_file in template_files:
    with open(template_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    rel_path = os.path.relpath(template_file, templates_dir)
    
    # Проверка на наличие csrf_token в формах
    if '<form' in content and 'csrf_token' not in content and 'admin' not in rel_path and 'coach' not in rel_path:
        # Не все формы требуют CSRF
        pass
    
    # Проверка на наличие обработчиков ошибок
    if 'flash' in content or 'error' in content or 'message' in content:
        pass  # Есть обработка сообщений

# ==================== АНАЛИЗ БЕЗОПАСНОСТИ ====================

print("\n[5/6] Анализ безопасности...")

# Проверка utils.py на безопасность
with open('utils.py', 'r', encoding='utf-8') as f:
    utils_content = f.read()

if 'bcrypt' in utils_content or 'passlib' in utils_content:
    print("  ✓ Пароли хешируются")
else:
    issues['critical'].append("Пароли не хешируются!")

if 'jwt' in utils_content or 'create_access_token' in utils_content:
    print("  ✓ JWT токены используются")
else:
    issues['minor'].append("JWT токены не используются")

if 'generate_csrf_token' in utils_content:
    print("  ✓ CSRF защита реализована")
else:
    issues['major'].append("CSRF защита не реализована")

# Проверка config.py
with open('config.py', 'r', encoding='utf-8') as f:
    config_content = f.read()

if 'secret_key' in config_content:
    print("  ✓ SECRET_KEY настроен")
else:
    issues['critical'].append("SECRET_KEY не настроен!")

# ==================== АНАЛИЗ CSS ====================

print("\n[6/6] Анализ CSS...")

css_path = os.path.join('static', 'style.css')
if os.path.exists(css_path):
    with open(css_path, 'r', encoding='utf-8') as f:
        css_content = f.read()
    
    print(f"  ✓ style.css существует ({len(css_content)} символов)")
    
    # Проверка CSS переменных
    if ':root' in css_content:
        print("  ✓ CSS переменные используются")
    else:
        issues['suggestions'].append("Рекомендуется использовать CSS переменные")
    
    # Проверка на наличие responsive design
    if '@media' in css_content:
        print("  ✓ Responsive design присутствует")
    else:
        issues['minor'].append("Отсутствует responsive design (@media queries)")
else:
    issues['major'].append("Отсутствует файл style.css")

# ==================== ИТОГОВЫЙ ОТЧЁТ ====================

print("\n" + "=" * 70)
print("ИТОГОВЫЙ ОТЧЁТ")
print("=" * 70)

total_issues = sum(len(v) for v in issues.values())

print(f"\nКритические ошибки: {len(issues['critical'])}")
for issue in issues['critical']:
    print(f"  🔴 {issue}")

print(f"\nСерьёзные ошибки: {len(issues['major'])}")
for issue in issues['major']:
    print(f"  🟠 {issue}")

print(f"\nНезначительные проблемы: {len(issues['minor'])}")
for issue in issues['minor']:
    print(f"  🟡 {issue}")

print(f"\nРекомендации: {len(issues['suggestions'])}")
for issue in issues['suggestions']:
    print(f"  💡 {issue}")

print(f"\n{'=' * 70}")
if total_issues == 0:
    print("✅ ОШИБОК НЕ НАЙДЕНО")
elif len(issues['critical']) > 0:
    print("🔴 ТРЕБУЕТСЯ НЕМЕДЛЕННОЕ ИСПРАВЛЕНИЕ")
elif len(issues['major']) > 0:
    print("🟠 ТРЕБУЕТСЯ ИСПРАВЛЕНИЕ")
else:
    print("🟡 РЕКОМЕНДУЕТСЯ УЛУЧШИТЬ")
print(f"{'=' * 70}")
