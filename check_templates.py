from jinja2 import Environment, FileSystemLoader
import os

templates_dir = 'templates'
env = Environment(loader=FileSystemLoader(templates_dir))

errors = []
count = 0

for root, dirs, files in os.walk(templates_dir):
    for file in files:
        if file.endswith('.html'):
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, templates_dir)
            try:
                env.get_template(rel_path)
                count += 1
                print(f"OK: {rel_path}")
            except Exception as e:
                errors.append((rel_path, str(e)))
                print(f"ERROR: {rel_path}: {e}")

print(f'\n====================')
print(f'Проверено шаблонов: {count}')
print(f'Ошибок: {len(errors)}')
if errors:
    print('\nСписок ошибок:')
    for path, error in errors:
        print(f'  {path}: {error}')
else:
    print('Все шаблоны корректны!')
