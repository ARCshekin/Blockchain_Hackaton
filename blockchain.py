import os
from web3 import Web3
from web3.middleware import geth_poa_middleware
import json
import requests
from typing import Dict, Any, Optional

class BlockchainManager:
    def __init__(self):
        self.w3 = None
        self.factory_contract = None
        self.campaign_contracts = {}
        self.setup_web3()
    
    def setup_web3(self):
        """Настройка подключения к блокчейну"""
        try:
            # Для тестирования используем локальный узел или тестнет
            rpc_url = "http://127.0.0.1:8545"
            self.w3 = Web3(Web3.HTTPProvider(rpc_url))
            
            # Добавляем middleware для PoA сетей (например, Polygon)
            self.w3.middleware_onion.inject(geth_poa_middleware, layer=0)
            
            if self.w3.is_connected():
                print(f"✅ Подключение к блокчейну установлено: {rpc_url}")
            else:
                print("❌ Не удалось подключиться к блокчейну")
        except Exception as e:
            print(f"❌ Ошибка подключения к блокчейну: {e}")
    
    def load_contract_abi(self, contract_name: str) -> Dict:
        """Загрузка ABI контракта"""
        try:
            # В реальном проекте ABI должен быть скомпилирован
            # Здесь используем базовый ABI для примера
            if contract_name == "Campaign":
                return [
                    {
                        "inputs": [
                            {"internalType": "address", "name": "_owner", "type": "address"},
                            {"internalType": "address", "name": "_complianceOracle", "type": "address"},
                            {"internalType": "address", "name": "_proofNFT", "type": "address"}
                        ],
                        "name": "initialize",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    },
                    {
                        "inputs": [],
                        "name": "donate",
                        "outputs": [],
                        "stateMutability": "payable",
                        "type": "function"
                    },
                    {
                        "anonymous": False,
                        "inputs": [
                            {"indexed": True, "internalType": "address", "name": "donor", "type": "address"},
                            {"indexed": False, "internalType": "uint256", "name": "amount", "type": "uint256"},
                            {"indexed": False, "internalType": "uint256", "name": "timestamp", "type": "uint256"}
                        ],
                        "name": "Donated",
                        "type": "event"
                    }
                ]
            elif contract_name == "DonationFactory":
                return [
                    {
                        "inputs": [
                            {"internalType": "address", "name": "_complianceOracle", "type": "address"},
                            {"internalType": "address", "name": "_proofNFT", "type": "address"}
                        ],
                        "name": "__init__",
                        "outputs": [],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    },
                    {
                        "inputs": [{"internalType": "address", "name": "owner", "type": "address"}],
                        "name": "createCampaign",
                        "outputs": [{"internalType": "address", "name": "", "type": "address"}],
                        "stateMutability": "nonpayable",
                        "type": "function"
                    }
                ]
            return []
        except Exception as e:
            print(f"❌ Ошибка загрузки ABI для {contract_name}: {e}")
            return []
    
    def get_contract(self, contract_name: str, address: str = None):
        """Получение контракта"""
        try:
            abi = self.load_contract_abi(contract_name)
            if address:
                return self.w3.eth.contract(address=address, abi=abi)
            else:
                # Для фабрики используем адрес по умолчанию
                factory_address = os.getenv("FACTORY_ADDRESS", "0x0000000000000000000000000000000000000000")
                return self.w3.eth.contract(address=factory_address, abi=abi)
        except Exception as e:
            print(f"❌ Ошибка получения контракта {contract_name}: {e}")
            return None
    
    def create_campaign(self, owner_address: str) -> Optional[str]:
        """Создание новой кампании"""
        try:
            factory = self.get_contract("DonationFactory")
            if not factory:
                return None
            
            # В реальном проекте здесь будет вызов createCampaign
            # Пока возвращаем заглушку
            campaign_address = f"0x{os.urandom(20).hex()}"
            self.campaign_contracts[campaign_address] = owner_address
            
            print(f"✅ Кампания создана: {campaign_address}")
            return campaign_address
        except Exception as e:
            print(f"❌ Ошибка создания кампании: {e}")
            return None
    
    def make_donation(self, campaign_address: str, amount_wei: int, donor_address: str) -> Optional[str]:
        """Создание пожертвования"""
        try:
            campaign = self.get_contract("Campaign", campaign_address)
            if not campaign:
                return None
            
            # В реальном проекте здесь будет вызов donate()
            # Пока возвращаем заглушку tx_hash
            tx_hash = f"0x{os.urandom(32).hex()}"
            
            print(f"✅ Пожертвование создано: {tx_hash}")
            return tx_hash
        except Exception as e:
            print(f"❌ Ошибка создания пожертвования: {e}")
            return None
    
    def get_transaction_status(self, tx_hash: str) -> Dict[str, Any]:
        """Получение статуса транзакции"""
        try:
            if not self.w3.is_connected():
                return {"error": "Нет подключения к блокчейну"}
            
            # В реальном проекте здесь будет проверка статуса
            # Пока возвращаем заглушку
            return {
                "tx_hash": tx_hash,
                "status": "confirmed",
                "block_number": 12345,
                "gas_used": 21000,
                "timestamp": "2024-01-01T00:00:00Z"
            }
        except Exception as e:
            return {"error": f"Ошибка получения статуса: {e}"}
    
    def check_risk_score(self, amount: int, tx_count: int, is_blacklisted: bool) -> float:
        """Проверка риска через ML API"""
        try:
            ml_api_url = os.getenv("ML_API_URL", "http://localhost:5001/score")
            data = {
                "amount": amount,
                "tx_count": tx_count,
                "is_blacklisted": is_blacklisted
            }
            
            response = requests.post(ml_api_url, json=data, timeout=5)
            if response.status_code == 200:
                return response.json().get("risk_score", 0.0)
            else:
                print(f"❌ Ошибка ML API: {response.text}")
                return 0.5  # Средний риск по умолчанию
        except Exception as e:
            print(f"❌ Ошибка проверки риска: {e}")
            return 0.5

# Глобальный экземпляр менеджера блокчейна
blockchain_manager = BlockchainManager() 