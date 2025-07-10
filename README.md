# Charity Bot - Telegram Bot для благотворительности

Бот для создания пожертвований через блокчейн с интеграцией смарт-контрактов и ML-анализом рисков.

## Функциональность

- 🔐 Регистрация и авторизация пользователей
- 💰 Создание кошельков с seed phrase
- 📝 Создание благотворительных кампаний
- 💸 Пожертвования через блокчейн
- 🤖 ML-анализ рисков транзакций
- 📊 Проверка статуса транзакций
- 🔍 Аудит всех действий
- 🏗️ Смарт-контракты на Solidity

## Установка

1. Клонируйте репозиторий
2. Установите зависимости:
```bash
pip install -r requirements.txt
npm install
```

3. Создайте файл `.env` с переменными окружения:
```env
BOT_TOKEN=your_bot_token_here
POSTGRES_DSN=postgresql+psycopg2://username@localhost:5432/database
SECRET_KEY=your_super_secret_key_here
```

4. Настройте базу данных PostgreSQL

## Запуск

### Запуск компонентов системы

#### 1. Локальный блокчейн (Hardhat)
```bash
npx hardhat-project/hardhat node
```

#### 2. Backend (FastAPI)
```bash
pkill -f "uvicorn main:app" && sleep 2 && uvicorn main:app --host 127.0.0.1 --port 8000 &
```

#### 3. Telegram Bot
```bash
python3 bot.py
```

### Автоматический запуск всей системы
```bash
python run_system.py
```

## API Endpoints

- `POST /register/` - Регистрация пользователя
- `POST /login/` - Авторизация пользователя
- `POST /wallet/create/` - Создание кошелька
- `POST /campaigns/` - Создание кампании
- `GET /campaigns/` - Список всех кампаний
- `POST /donate` - Создание пожертвования (с ML-анализом рисков)
- `GET /status/{tx_hash}` - Проверка статуса транзакции
- `GET /balance/{user_id}` - Проверка баланса кошелька

## Команды бота

- `/start` - Приветствие и список команд
- `/register` - Регистрация нового пользователя
- `/login` - Вход в систему
- `/wallet` - Создать кошелек
- `/campaign` - Создать кампанию
- `/campaigns` - Показать список кампаний
- `/donate` - Сделать пожертвование
- `/balance` - Проверить баланс
- `/status <tx_hash>` - Проверить статус транзакции

## Структура проекта

```
├── main.py                    # FastAPI приложение
├── bot.py                     # Telegram бот
├── blockchain.py              # Интеграция с блокчейном
├── ml_risk_api.py            # ML API для анализа рисков
├── models.py                  # Модели базы данных
├── db.py                      # Работа с базой данных
├── contract_deployer.py       # Деплой смарт-контрактов
├── check_balance.py           # Проверка баланса
├── simple_bot.py             # Упрощенная версия бота
├── start_ml_api.py           # Запуск ML API
├── run_system.py             # Скрипт запуска всей системы
├── reset_db.py               # Сброс базы данных
├── env.py                     # Конфигурация окружения
├── alembic/                   # Миграции базы данных
│   ├── env.py
│   ├── versions/
│   └── script.py.mako
├── contracts/                 # Смарт-контракты Solidity
│   ├── Campaign.sol
│   ├── ComplianceOracle.sol
│   ├── DonationFactory.sol
│   ├── Lock.sol
│   ├── PlatformToken.sol
│   └── ProofNFT.sol
├── hardhat-project/           # Hardhat конфигурация
│   ├── contracts/
│   ├── hardhat.config.js
│   ├── package.json
│   └── test/
├── templates/                 # HTML шаблоны
├── static/                    # Статические файлы
│   ├── css/
│   └── images/
├── requirements.txt           # Python зависимости
├── package.json              # Node.js зависимости
├── risk_model.pkl            # ML модель для анализа рисков
└── db.sqlite3               # SQLite база данных
```

## Интеграция со смарт-контрактами

Система интегрирована с блокчейном Ethereum:

1. ✅ Web3.py для работы с Ethereum
2. ✅ Смарт-контракты Solidity в папке `contracts/`
3. ✅ Hardhat для локальной разработки
4. ✅ ML-анализ рисков транзакций
5. ✅ Интеграция в эндпоинты `/donate` и `/status`

### Смарт-контракты:
- `Campaign.sol` - Контракт кампании
- `DonationFactory.sol` - Фабрика для создания кампаний
- `ProofNFT.sol` - NFT для подтверждения пожертвований
- `ComplianceOracle.sol` - Оракул для проверки соответствия
- `PlatformToken.sol` - Токен платформы
- `Lock.sol` - Базовый контракт блокировки

## База данных

Система использует Alembic для управления миграциями:

```bash
# Создание новой миграции
alembic revision --autogenerate -m "Описание изменений"

# Применение миграций
alembic upgrade head

# Откат миграции
alembic downgrade -1
```

## Безопасность

- Пароли хешируются с помощью bcrypt
- JWT токены для авторизации
- ML-анализ рисков транзакций
- Аудит всех действий пользователей
- Валидация входных данных
- Проверка соответствия через Compliance Oracle

## Разработка

Для добавления новых функций:

1. Обновите модели в `models.py`
2. Добавьте эндпоинты в `main.py`
3. Создайте команды в `bot.py`
4. Обновите смарт-контракты в `contracts/`
5. Создайте миграции через Alembic
6. Обновите документацию

## Полезные команды

```bash
# Запуск всех компонентов
python run_system.py

# Сброс базы данных
python reset_db.py

# Проверка баланса
python check_balance.py

# Запуск ML API отдельно
python start_ml_api.py

# Деплой контрактов
python contract_deployer.py
``` 