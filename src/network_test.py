import subprocess
import re
import socket
import logging
from pathlib import Path
import tempfile

logger = logging.getLogger(__name__)


class NetworkTest:
    """Тестування мережі з звітом"""

    def __init__(self, config_manager, telegram_api):
        self.config = config_manager
        self.telegram = telegram_api

    def run_ping_test(self, host, count=20):
        """Виконати ping тест на хосту"""
        try:
            result = subprocess.run(
                ['ping', host, '-n', str(count)],
                capture_output=True,
                text=True,
                encoding='cp1252',
                timeout=60,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            return result.stdout
        except Exception as e:
            logger.error(f"Помилка ping: {e}")
            return f"Помилка при тестуванні {host}: {str(e)}"

    def parse_ping_loss(self, ping_output):
        """Витягти відсоток втрати пакетів"""
        try:
            match = re.search(r'(\d+)%\s+(потерь|loss)', ping_output, re.IGNORECASE)
            if match:
                return int(match.group(1))
            return 0
        except:
            return -1

    def run_full_test(self):
        """Запустити повний тест мережі"""
        pc_name = socket.gethostname()
        store_location = self.config.store_location_text

        hosts = {
            "1С Сервер": "23.88.7.196",
            "Google DNS": "8.8.8.8"
        }

        report_parts = []
        total_loss = 0

        for name, ip in hosts.items():
            ping_output = self.run_ping_test(ip)
            loss = self.parse_ping_loss(ping_output)

            if loss >= 0:
                status = "✅" if loss == 0 else ("⚠️" if loss <= 15 else "❌")
                report_parts.append(f"{status} {name} ({ip}): {loss}% втрати")
                total_loss += loss
            else:
                report_parts.append(f"❌ {name} ({ip}): Помилка тестування")

        avg_loss = total_loss / len(hosts) if hosts else 0

        if avg_loss == 0:
            status_text = "✅ Мережа в нормі"
            color = "green"
        elif avg_loss <= 15:
            status_text = "⚠️ Є невеликі проблеми"
            color = "orange"
        else:
            status_text = "❌ Серйозні проблеми"
            color = "red"

        # Відправити в Telegram
        test_report = "\n".join(report_parts)
        self.telegram.send_network_report(store_location, pc_name, test_report)

        return {
            "status": status_text,
            "color": color,
            "details": test_report
        }
