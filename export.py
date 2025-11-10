#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Project Structure Exporter
Створює детальний опис структури проєкту та вміст файлів у один файл
"""

import os
from pathlib import Path
from datetime import datetime

# Файли та папки, які треба ігнорувати
IGNORE_PATTERNS = {
    # Папки
    '__pycache__', '.git', '.idea', '.vscode', 'node_modules',
    'venv', 'env', '.env', 'dist', 'build', '.pytest_cache',
    '.mypy_cache', 'htmlcov', '.coverage', 'logs', 'tmp',
    # Файли
    '.pyc', '.pyo', '.pyd', '.so', '.dll', '.dylib', '.exe',
    '.log', '.sqlite', '.db', '.pkl', '.pickle', '.DS_Store',
    'Thumbs.db', '.env', '.env.local', '.gitignore'
}

# Розширення файлів для читання (текстові файли)
TEXT_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.html', '.css', '.scss',
    '.json', '.yaml', '.yml', '.toml', '.ini', '.cfg', '.conf',
    '.txt', '.md', '.rst', '.xml', '.sql', '.sh', '.bash',
    '.env.example', '.gitignore', 'Dockerfile', 'Makefile',
    '.java', '.c', '.cpp', '.h', '.go', '.rs', '.php', '.rb'
}

# Максимальний розмір файлу (1 MB)
MAX_FILE_SIZE = 1024 * 1024


def should_ignore(path: Path) -> bool:
    """Перевіряє, чи треба ігнорувати файл/папку"""
    name = path.name

    # Перевірка точного збігу
    if name in IGNORE_PATTERNS:
        return True

    # Перевірка розширення
    if path.suffix in IGNORE_PATTERNS:
        return True

    # Перевірка прихованих файлів (крім .env.example)
    if name.startswith('.') and name != '.env.example':
        return True

    return False


def is_text_file(path: Path) -> bool:
    """Перевіряє, чи є файл текстовим"""
    # Перевірка розширення
    if path.suffix.lower() in TEXT_EXTENSIONS:
        return True

    # Файли без розширення, які зазвичай текстові
    if path.suffix == '' and path.name in {'Dockerfile', 'Makefile', 'README', 'LICENSE'}:
        return True

    return False


def get_tree_structure(root_path: Path, prefix: str = "", is_last: bool = True) -> list:
    """Генерує дерево структури проєкту"""
    lines = []

    try:
        items = sorted(root_path.iterdir(), key=lambda x: (not x.is_dir(), x.name.lower()))
        items = [item for item in items if not should_ignore(item)]

        for i, item in enumerate(items):
            is_last_item = i == len(items) - 1
            current_prefix = "└── " if is_last_item else "├── "
            lines.append(f"{prefix}{current_prefix}{item.name}{'/' if item.is_dir() else ''}")

            if item.is_dir():
                extension = "    " if is_last_item else "│   "
                lines.extend(get_tree_structure(item, prefix + extension, is_last_item))

    except PermissionError:
        pass

    return lines


def read_file_content(file_path: Path) -> str:
    """Читає вміст файлу"""
    try:
        # Перевірка розміру
        if file_path.stat().st_size > MAX_FILE_SIZE:
            return f"[Файл занадто великий: {file_path.stat().st_size / 1024:.1f} KB]"

        # Спроба прочитати як текст
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except UnicodeDecodeError:
        # Якщо не вдалося прочитати як UTF-8
        try:
            with open(file_path, 'r', encoding='cp1251') as f:
                return f.read()
        except:
            return "[Не вдалося прочитати файл - бінарний або невідоме кодування]"
    except Exception as e:
        return f"[Помилка читання: {str(e)}]"


def collect_files(root_path: Path) -> list:
    """Збирає всі текстові файли проєкту"""
    files = []

    for item in root_path.rglob('*'):
        if item.is_file() and not should_ignore(item) and is_text_file(item):
            # Перевірка, що всі батьківські папки не ігноруються
            if not any(should_ignore(parent) for parent in item.parents):
                files.append(item)

    return sorted(files)


def generate_project_export(project_path: str, output_file: str = None):
    """Генерує повний експорт проєкту"""
    root = Path(project_path).resolve()

    if not root.exists():
        print(f"❌ Помилка: Шлях '{project_path}' не існує!")
        return

    if output_file is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_file = f"project_export_{timestamp}.txt"

    print(f"📁 Аналіз проєкту: {root.name}")
    print(f"📝 Генерація експорту...")

    with open(output_file, 'w', encoding='utf-8') as f:
        # Заголовок
        f.write("=" * 80 + "\n")
        f.write(f"ЕКСПОРТ ПРОЄКТУ: {root.name}\n")
        f.write(f"Дата: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Шлях: {root}\n")
        f.write("=" * 80 + "\n\n")

        # Структура проєкту
        f.write("📂 СТРУКТУРА ПРОЄКТУ\n")
        f.write("-" * 80 + "\n")
        f.write(f"{root.name}/\n")
        tree_lines = get_tree_structure(root)
        f.write("\n".join(tree_lines))
        f.write("\n\n")

        # Збір файлів
        files = collect_files(root)

        f.write(f"📄 ВМІСТ ФАЙЛІВ ({len(files)} файлів)\n")
        f.write("=" * 80 + "\n\n")

        # Вміст кожного файлу
        for i, file_path in enumerate(files, 1):
            relative_path = file_path.relative_to(root)

            print(f"  [{i}/{len(files)}] {relative_path}")

            f.write("\n" + "=" * 80 + "\n")
            f.write(f"Файл {i}/{len(files)}: {relative_path}\n")
            f.write("-" * 80 + "\n")

            content = read_file_content(file_path)
            f.write(content)
            f.write("\n")

        # Підсумок
        f.write("\n" + "=" * 80 + "\n")
        f.write("КІНЕЦЬ ЕКСПОРТУ\n")
        f.write("=" * 80 + "\n")

    file_size = Path(output_file).stat().st_size
    print(f"\n✅ Експорт завершено!")
    print(f"📄 Файл: {output_file}")
    print(f"📊 Розмір: {file_size / 1024:.1f} KB")
    print(f"📁 Файлів оброблено: {len(files)}")


if __name__ == "__main__":
    import sys

    # Використання: python export_project.py [шлях_до_проєкту] [вихідний_файл]
    project_path = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else None

    generate_project_export(project_path, output_file)
