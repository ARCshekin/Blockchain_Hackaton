import os
from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Boolean, create_engine
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from datetime import datetime

# Строка подключения к PostgreSQL (замените на свою при необходимости)
POSTGRES_DSN = os.getenv("POSTGRES_DSN", "postgresql+psycopg2://arsenijsekin@localhost:5432/hackathon")

Base = declarative_base()

class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    telegram_id = Column(String, unique=True)
    username = Column(String)
    password_hash = Column(String)  # Хеш пароля
    role = Column(String, default='user')  # user/admin
    seed_phrase = Column(String, nullable=True)  # Seed phrase для кошелька
    wallet_created = Column(Boolean, default=False)  # Флаг создания кошелька
    private_key = Column(String, nullable=True)  # Приватный ключ кошелька
    wallet_address = Column(String, nullable=True)  # Адрес кошелька
    campaign_contract_address = Column(String, nullable=True)  # Адрес смарт-контракта кампании
    factory_contract_address = Column(String, nullable=True)  # Адрес фабрики контрактов
    donations = relationship('Donation', back_populates='user')
    audit_logs = relationship('AuditLog', back_populates='user')

class Campaign(Base):
    __tablename__ = 'campaigns'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    description = Column(String)
    donations = relationship('Donation', back_populates='campaign')

class Donation(Base):
    __tablename__ = 'donations'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    campaign_id = Column(Integer, ForeignKey('campaigns.id'))
    amount = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)
    tx_hash = Column(String, nullable=True)  # Хеш транзакции
    user = relationship('User', back_populates='donations')
    campaign = relationship('Campaign', back_populates='donations')

class AuditLog(Base):
    __tablename__ = 'audit_logs'
    id = Column(Integer, primary_key=True)
    action = Column(String)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    details = Column(String)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user = relationship('User', back_populates='audit_logs')

# Создаем движок и сессию
engine = create_engine(POSTGRES_DSN, echo=True)
SessionLocal = sessionmaker(bind=engine)

def init_db():
    # Создает все таблицы
    Base.metadata.create_all(engine)
    print("Таблицы созданы!") 