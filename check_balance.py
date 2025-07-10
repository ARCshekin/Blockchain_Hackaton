from web3 import Web3
import os
from dotenv import load_dotenv

# Загрузить переменные окружения из .env
load_dotenv()

PRIVATE_KEY = "47c99abed3324a2707c28affff1267e45918ec8c3f20b8aa892e8b065d2942dd"
if not PRIVATE_KEY:
    print("PRIVATE_KEY не найден в .env")
    exit(1)

# Подключение к локальному RPC (или замените на свой)
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8545"))

# Получить адрес из приватного ключа
account = w3.eth.account.from_key(PRIVATE_KEY)
address = account.address
print("Адрес:", address)

# Получить баланс
balance_wei = w3.eth.get_balance(address)
balance_eth = w3.from_wei(balance_wei, 'ether')
print(f"Баланс: {balance_wei} wei ({balance_eth} ETH)")