import os
import sys
import subprocess
import psutil
from pathlib import Path
from config import LOCK_FILE, APP_NAME


class SingleInstance:
    """Перевірка на єдиний екземпляр програми"""

    def __init__(self):
        self.lock_file = LOCK_FILE
        self.fp = None

    def is_running(self):
        """Перевірка чи програма вже запущена"""
        if sys.platform == 'win32':
            import win32event
            import win32api
            import winerror

            self.mutex = win32event.CreateMutex(None, False, APP_NAME)
            if win32api.GetLastError() == winerror.ERROR_ALREADY_EXISTS:
                return True
        else:
            try:
                self.fp = open(self.lock_file, 'w')
                import fcntl
                fcntl.flock(self.fp, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except IOError:
                return True
        return False


def open_rdp_connection(host, port):
    """Відкриття RDP підключення"""
    rdp_command = f'mstsc /v:{host}:{port}'
    subprocess.Popen(rdp_command, shell=True)


def close_all_rdp_sessions():
    """Закриття всіх RDP сесій"""
    for proc in psutil.process_iter(['name']):
        try:
            if proc.info['name'].lower() == 'mstsc.exe':
                proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            pass


def test_connection(host):
    """Тест з'єднання через ping"""
    param = '-n' if sys.platform == 'win32' else '-c'
    command = ['ping', param, '1', host]
    result = subprocess.run(command, capture_output=True, text=True)
    return result.returncode == 0