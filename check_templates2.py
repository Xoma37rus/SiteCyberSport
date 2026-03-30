from jinja2 import Environment, FileSystemLoader
import os

templates_dir = 'templates'
env = Environment(loader=FileSystemLoader(templates_dir))

errors = []

# Проверяем каждый шаблон с подробным выводом ошибки
test_templates = [
    'admin/dashboard.html',
    'coach/dashboard.html',
    'includes/navbar.html'
]

for template_path in test_templates:
    try:
        # Пробуем загрузить с разными путями
        full_path = os.path.join(templates_dir, template_path)
        if os.path.exists(full_path):
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            # Пробуем скомпилировать
            env.from_string(content)
            print(f"OK: {template_path}")
        else:
            print(f"NOT FOUND: {template_path}")
    except Exception as e:
        print(f"ERROR: {template_path}")
        print(f"  Details: {e}")
        errors.append((template_path, str(e)))
