import requests
import os
import sys
import subprocess
from pathlib import Path
from config import GITHUB_API_URL, VERSION_FILE, BASE_DIR


def get_current_version():
    """Отримання поточної версії"""
    version_path = BASE_DIR / VERSION_FILE
    if version_path.exists():
        with open(version_path, 'r') as f:
            return f.read().strip()
    return "0.0.0"


def get_latest_version():
    """Отримання останньої версії з GitHub"""
    try:
        response = requests.get(GITHUB_API_URL, timeout=5)
        if response.status_code == 200:
            data = response.json()
            return data['tag_name'].lstrip('v'), data['assets'][0]['browser_download_url']
    except Exception as e:
        print(f"Помилка перевірки оновлень: {e}")
    return None, None


def download_update(download_url, save_path):
    """Завантаження оновлення"""
    response = requests.get(download_url, stream=True)
    with open(save_path, 'wb') as f:
        for chunk in response.iter_content(chunk_size=8192):
            f.write(chunk)


def check_and_update():
    """Перевірка та встановлення оновлень"""
    current_version = get_current_version()
    latest_version, download_url = get_latest_version()

    if latest_version and latest_version > current_version:
        print(f"Доступне оновлення: {latest_version}")
        update_path = BASE_DIR / "RemoteHand_new.exe"
        download_update(download_url, update_path)

        # Запуск оновленої версії та закриття поточної
        batch_script = f'''
        @echo off
        timeout /t 2 /nobreak
        move /y "{update_path}" "{sys.executable}"
        start "" "{sys.executable}"
        '''
        batch_path = BASE_DIR / "update.bat"
        with open(batch_path, 'w') as f:
            f.write(batch_script)
        subprocess.Popen(['cmd', '/c', str(batch_path)], shell=True)
        sys.exit(0)
    return False
