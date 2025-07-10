#!/usr/bin/env python3
"""
Скрипт для запуска всей системы Charity Bot
"""

import subprocess
import sys
import time
import requests
import signal
import os

class SystemManager:
    def __init__(self):
        self.processes = []
        
    def start_backend(self):
        """Запуск FastAPI backend"""
        try:
            print("🚀 Запуск FastAPI backend...")
            process = subprocess.Popen([
                sys.executable, "-m", "uvicorn", "main:app", 
                "--reload", "--host", "0.0.0.0", "--port", "8000"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(("Backend", process))
            time.sleep(3)
            print("✅ Backend запущен на http://localhost:8000")
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска backend: {e}")
            return False
    
    def start_ml_api(self):
        """Запуск ML API"""
        try:
            print("🤖 Запуск ML API...")
            process = subprocess.Popen([
                sys.executable, "ml_risk_api.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(("ML API", process))
            time.sleep(3)
            print("✅ ML API запущен на http://localhost:5001")
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска ML API: {e}")
            return False
    
    def start_bot(self):
        """Запуск Telegram бота"""
        try:
            print("🤖 Запуск Telegram бота...")
            process = subprocess.Popen([
                sys.executable, "bot.py"
            ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            self.processes.append(("Bot", process))
            time.sleep(2)
            print("✅ Telegram бот запущен")
            return True
        except Exception as e:
            print(f"❌ Ошибка запуска бота: {e}")
            return False
    
    def check_services(self):
        """Проверка работы сервисов"""
        print("\n🔍 Проверка сервисов...")
        
        # Проверка backend
        try:
            response = requests.get("http://localhost:8000/docs", timeout=5)
            if response.status_code == 200:
                print("✅ Backend работает")
            else:
                print("❌ Backend не отвечает")
        except:
            print("❌ Backend недоступен")
        
        # Проверка ML API
        try:
            response = requests.get("http://localhost:5001/health", timeout=5)
            if response.status_code == 200:
                print("✅ ML API работает")
            else:
                print("❌ ML API не отвечает")
        except:
            print("❌ ML API недоступен")
    
    def stop_all(self):
        """Остановка всех процессов"""
        print("\n🛑 Остановка всех сервисов...")
        for name, process in self.processes:
            try:
                process.terminate()
                process.wait(timeout=5)
                print(f"✅ {name} остановлен")
            except:
                process.kill()
                print(f"⚠️ {name} принудительно остановлен")
    
    def signal_handler(self, signum, frame):
        """Обработчик сигналов для корректного завершения"""
        print("\n🛑 Получен сигнал завершения...")
        self.stop_all()
        sys.exit(0)

def main():
    """Главная функция"""
    manager = SystemManager()
    
    # Регистрируем обработчик сигналов
    signal.signal(signal.SIGINT, manager.signal_handler)
    signal.signal(signal.SIGTERM, manager.signal_handler)
    
    print("🎉 Запуск системы Charity Bot...")
    print("=" * 50)
    
    # Запускаем сервисы
    success = True
    success &= manager.start_backend()
    success &= manager.start_ml_api()
    success &= manager.start_bot()
    
    if success:
        print("\n🎉 Все сервисы запущены!")
        manager.check_services()
        
        print("\n📋 Доступные сервисы:")
        print("🌐 Backend API: http://localhost:8000")
        print("📊 API Docs: http://localhost:8000/docs")
        print("🤖 ML API: http://localhost:5001")
        print("📱 Telegram Bot: активен")
        
        print("\n⏹️ Для остановки нажмите Ctrl+C")
        
        try:
            # Держим процессы активными
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n🛑 Получен сигнал остановки...")
    else:
        print("\n❌ Ошибка запуска системы")
        manager.stop_all()
        sys.exit(1)

if __name__ == "__main__":
    main() 