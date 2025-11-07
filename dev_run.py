"""
DEV_RUN.PY - Локальне тестування
"""

import sys
import os

# Встановити DEV режим
os.environ['REMOTEHAND_DEV_MODE'] = '1'

# Додати src в path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

print("Перевірка залежностей...")
import subprocess
subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt", "-q"],
               capture_output=True)

print("🔧 Запуск у DEV режимі...")

# Прямо запустити main
if __name__ == "__main__":
    import main
    main.main()
