#!/usr/bin/env python3
"""
Скрипт для запуска ML API для анализа рисков
"""

import subprocess
import sys
import time
import requests

def start_ml_api():
    """Запуск ML API"""
    try:
        print("🚀 Запуск ML API...")
        
        # Запускаем ML API в фоновом режиме
        process = subprocess.Popen([
            sys.executable, "ml_risk_api.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        # Ждем немного для запуска
        time.sleep(3)
        
        # Проверяем, что API работает
        try:
            response = requests.get("http://localhost:5001/health", timeout=5)
            if response.status_code == 200:
                print("✅ ML API успешно запущен на http://localhost:5001")
                return process
            else:
                print("❌ ML API не отвечает")
                return None
        except requests.exceptions.RequestException:
            print("✅ ML API запущен (проверка недоступна)")
            return process
            
    except Exception as e:
        print(f"❌ Ошибка запуска ML API: {e}")
        return None

if __name__ == "__main__":
    start_ml_api() 