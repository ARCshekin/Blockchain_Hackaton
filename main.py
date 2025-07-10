from fastapi import FastAPI, Request, HTTPException, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from sqlalchemy.orm import Session
from db import SessionLocal, User, Campaign, Donation, AuditLog, init_db
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
import logging
from passlib.hash import bcrypt
from datetime import datetime, timedelta
from jose import JWTError, jwt
import os
from blockchain import blockchain_manager
from contract_deployer import ContractDeployer
from dotenv import load_dotenv
import traceback
load_dotenv()

app = FastAPI()
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Initialize database on startup
@app.on_event("startup")
async def startup_event():
    init_db()

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/login/")
ML_API_URL = "http://localhost:5001/score"

ORGANIZATIONS = [
    {"id": "redcross", "name": "Красный Крест"},
    {"id": "wwf", "name": "Всемирный фонд дикой природы"},
    {"id": "unicef", "name": "Детский фонд ООН"},
    {"id": "doctors", "name": "Врачи без границ"},
]


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(SessionLocal)):
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise HTTPException(status_code=401, detail="Не удалось проверить токен")
        user = db.query(User).filter(User.username == username).first()
        if user is None:
            raise HTTPException(status_code=401, detail="Пользователь не найден")
        return user
    except JWTError:
        raise HTTPException(status_code=401, detail="Неверный токен")


def create_access_token(data: dict, expires_delta: timedelta | None = None):
    to_encode = data.copy()
    expire = datetime.utcnow() + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


class UserCreate(BaseModel):
    telegram_id: str
    username: str
    password: str
    role: str = "user"


class SeedPhraseCreate(BaseModel):
    telegram_id: str
    seed_phrase: str


class CampaignCreate(BaseModel):
    title: str
    description: str

class CampaignCreateTelegram(BaseModel):
    title: str
    description: str
    telegram_id: str


@app.get("/donate", response_class=HTMLResponse)
async def donation_interface(request: Request, user_id: int, db: Session = Depends(get_db)):
    organizations = db.query(Campaign).all()
    print("ORGS:", organizations)
    for org in organizations:
        print("ORG:", org.id, org.title)
    return templates.TemplateResponse("index.html", {
        "request": request,
        "user_id": user_id,
        "organizations": organizations,
    })


@app.post("/donate")
def create_donation(donation_data: dict, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    
    # Получаем данные пользователя
    donor_id = donation_data.get("donor")
    amount_wei = donation_data.get("amount_wei", 0)
    campaign_id = donation_data.get("campaign_id", 1)
    
    # Проверяем риск через ML API
    user = db.query(User).filter(User.telegram_id == donor_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    
    tx_count = db.query(Donation).filter(Donation.user_id == user.id).count()
    is_blacklisted = False  # В реальном проекте проверка черного списка
    
    risk_score = blockchain_manager.check_risk_score(amount_wei, tx_count, is_blacklisted)
    
    force = donation_data.get("force", False)
    # Если риск высокий, отклоняем транзакцию, если не force
    if risk_score > 0.8 and not force:
        raise HTTPException(status_code=400, detail=f"Транзакция отклонена из-за высокого риска: {risk_score:.2f}")
    
    # Получаем адрес контракта кампании
    campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
    if not campaign:
        raise HTTPException(status_code=404, detail="Кампания не найдена")
    
    # Создаем пожертвование в блокчейне
    tx_hash = blockchain_manager.make_donation(
        campaign_address="0x0000000000000000000000000000000000000000",  # Заглушка
        amount_wei=amount_wei,
        donor_address=str(donor_id) if donor_id else "0x0000000000000000000000000000000000000000"
    )
    
    if not tx_hash:
        raise HTTPException(status_code=500, detail="Ошибка создания транзакции в блокчейне")
    
    # Создаем запись о пожертвовании в БД
    donation = Donation(
        user_id=user.id,  # Используем ID пользователя из БД
        campaign_id=campaign_id,
        amount=amount_wei / 1e18,  # Конвертируем в ETH
        timestamp=datetime.utcnow(),
        tx_hash=tx_hash  # Сохраняем хеш транзакции
    )
    db.add(donation)
    db.commit()
    
    return {
        "tx_hash": tx_hash,
        "status": "pending",
        "amount_wei": amount_wei,
        "risk_score": risk_score,
        "message": "Пожертвование отправлено в блокчейн"
    }


@app.get("/status/{tx_hash}")
def get_transaction_status(tx_hash: str, db: Session = Depends(get_db)):
    # Проверяем статус транзакции в блокчейне
    status = blockchain_manager.get_transaction_status(tx_hash)
    
    if "error" in status:
        raise HTTPException(status_code=500, detail=status["error"])
    
    return status


@app.get("/balance/{user_id}")
def get_wallet_balance(user_id: str, db: Session = Depends(get_db)):
    """Получение баланса кошелька пользователя"""
    try:
        user = db.query(User).filter(User.telegram_id == user_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if not getattr(user, 'wallet_created'):
            raise HTTPException(status_code=400, detail="Кошелек не создан")
        
        # В реальном проекте здесь будет проверка баланса в блокчейне
        # Пока возвращаем заглушку
        balance_wei = 1000000000000000000  # 1 ETH в wei
        balance_eth = balance_wei / 1e18
        
        return {
            "user_id": user_id,
            "balance_wei": balance_wei,
            "balance_eth": balance_eth,
            "wallet_created": getattr(user, 'wallet_created')
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения баланса: {e}")


@app.get("/campaigns/")
def get_campaigns(db: Session = Depends(get_db)):
    """Получение списка всех кампаний"""
    campaigns = db.query(Campaign).all()
    return [
        {
            "id": campaign.id,
            "title": campaign.title,
            "description": campaign.description,
            "created_at": campaign.id  # Заглушка для даты создания
        }
        for campaign in campaigns
    ]


@app.post("/campaigns/")
def create_campaign(campaign: CampaignCreate, request: Request, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    ip = request.client.host if request.client else "unknown"
    
    # Создаем кампанию в БД
    db_campaign = Campaign(
        title=campaign.title,
        description=campaign.description
    )
    db.add(db_campaign)
    db.commit()
    db.refresh(db_campaign)
    
    # Создаем смарт-контракт кампании
    campaign_address = blockchain_manager.create_campaign(str(getattr(current_user, 'telegram_id')))
    
    return {
        "id": db_campaign.id,
        "title": db_campaign.title,
        "contract_address": campaign_address,
        "message": "Кампания успешно создана"
    }


@app.post("/campaigns/telegram/")
def create_campaign_telegram(campaign: CampaignCreateTelegram, request: Request = None, db: Session = Depends(get_db)):
    """Создание кампании через Telegram ID (без JWT авторизации)"""
    ip = request.client.host if request and hasattr(request, 'client') and request.client else "unknown"
    
    try:
        # Проверяем, что пользователь существует
        user = db.query(User).filter(User.telegram_id == campaign.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if not bool(getattr(user, 'wallet_created')):
            raise HTTPException(status_code=400, detail="Сначала создайте кошелек")
        
        if not bool(getattr(user, 'private_key')):
            raise HTTPException(status_code=400, detail="Приватный ключ не найден")
        
        # Создаем кампанию в БД
        db_campaign = Campaign(
            title=campaign.title,
            description=campaign.description
        )
        db.add(db_campaign)
        db.commit()
        db.refresh(db_campaign)
        
        # Развертываем индивидуальный смарт-контракт кампании
        deployer = ContractDeployer()
        contract_result = deployer.deploy_campaign_contract(
            campaign_title=str(campaign.title),
            campaign_description=str(campaign.description)
        )
        
        if 'error' in contract_result and contract_result['error']:
            print('Ошибка создания контракта:', contract_result['error'])
            # Удаляем кампанию из БД если контракт не создался
            db.delete(db_campaign)
            db.commit()
            raise HTTPException(status_code=500, detail=f"Ошибка создания контракта: {contract_result['error']}")
        
        # Сохраняем адрес контракта в БД
        setattr(user, 'campaign_contract_address', str(contract_result['contract_address']))
        db.commit()
        
        return {
            "id": db_campaign.id,
            "title": db_campaign.title,
            "contract_address": contract_result['contract_address'],
            "transaction_hash": contract_result['transaction_hash'],
            "gas_used": contract_result['gas_used'],
            "message": "Кампания успешно создана"
        }
    except Exception as e:
        print('ERROR in create_campaign_telegram:', e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка создания кампании: {str(e)}")



@app.post("/register/")
def register_user(user: UserCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    
    # Проверяем, не существует ли уже пользователь с таким telegram_id
    existing_user = db.query(User).filter(User.telegram_id == user.telegram_id).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Пользователь с таким Telegram ID уже существует")
    
    # Хешируем пароль
    password_hash = bcrypt.hash(user.password)
    
    # Создаем нового пользователя
    db_user = User(
        telegram_id=user.telegram_id,
        username=user.username,
        password_hash=password_hash,
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "id": db_user.id,
        "username": db_user.username,
        "telegram_id": db_user.telegram_id,
        "role": db_user.role,
        "access_token": access_token
    }


@app.post("/login/")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Ищем пользователя по username
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    
    # Проверяем пароль
    if not bcrypt.verify(form_data.password, str(user.password_hash)):
        raise HTTPException(status_code=401, detail="Неверное имя пользователя или пароль")
    
    # Создаем токен доступа
    access_token = create_access_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,
        "username": user.username,
        "telegram_id": user.telegram_id,
        "wallet_created": user.wallet_created
    }

@app.post("/wallet/create/")
def create_wallet(seed_phrase: SeedPhraseCreate, request: Request, db: Session = Depends(get_db)):
    ip = request.client.host if request.client else "unknown"
    
    try:
        # Ищем пользователя по telegram_id
        user = db.query(User).filter(User.telegram_id == seed_phrase.telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if bool(user.wallet_created):
            raise HTTPException(status_code=400, detail="Кошелек уже создан")
        
        # Создаем новый кошелек для пользователя
        deployer = ContractDeployer()
        wallet_data = deployer.create_user_wallet()
        
        # Обновляем данные пользователя
        setattr(user, 'wallet_created', True)
        setattr(user, 'seed_phrase', str(seed_phrase.seed_phrase))
        setattr(user, 'private_key', str(wallet_data['private_key']))
        setattr(user, 'wallet_address', str(wallet_data['wallet_address']))
        
        # Развертываем фабрику контрактов для пользователя
        factory_result = deployer.deploy_factory_contract(str(wallet_data['private_key']))
        if 'error' not in factory_result:
            setattr(user, 'factory_contract_address', str(factory_result['contract_address']))
        
        db.commit()
        
        return {
            "message": "Кошелек успешно создан",
            "wallet_created": True,
            "wallet_address": wallet_data['wallet_address'],
            "factory_contract_address": factory_result.get('contract_address'),
            "transaction_hash": factory_result.get('transaction_hash')
        }
    except Exception as e:
        import traceback
        print('ERROR in create_wallet:', e)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Ошибка создания кошелька: {str(e)}")


@app.get("/wallet/info/{telegram_id}")
def get_wallet_info(telegram_id: str, db: Session = Depends(get_db)):
    """Получение информации о кошельке пользователя"""
    try:
        user = db.query(User).filter(User.telegram_id == telegram_id).first()
        if not user:
            raise HTTPException(status_code=404, detail="Пользователь не найден")
        
        if not bool(user.wallet_created):
            raise HTTPException(status_code=400, detail="Кошелек не создан")
        
        return {
            "telegram_id": telegram_id,
            "wallet_address": user.wallet_address,
            "factory_contract_address": user.factory_contract_address,
            "campaign_contract_address": user.campaign_contract_address,
            "wallet_created": user.wallet_created
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения информации о кошельке: {str(e)}")


@app.get("/contract/balance/{contract_address}")
def get_contract_balance(contract_address: str):
    """Получение баланса смарт-контракта"""
    try:
        deployer = ContractDeployer()
        balance = deployer.get_contract_balance(contract_address)
        return {
            "contract_address": contract_address,
            "balance_eth": balance,
            "balance_wei": balance * 1e18 if isinstance(balance, (int, float)) else 0
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка получения баланса контракта: {str(e)}")


@app.post("/donate/individual/")
def create_individual_donation(donation_data: dict, request: Request, db: Session = Depends(get_db)):
    """Создание пожертвования через индивидуальный контракт"""
    ip = request.client.host if request.client else "unknown"
    
    try:
        donor_id = donation_data.get("donor")
        amount_wei = donation_data.get("amount_wei", 0)
        campaign_id = donation_data.get("campaign_id", 1)
        
        # Получаем пользователя-донора
        donor = db.query(User).filter(User.telegram_id == donor_id).first()
        if not donor:
            raise HTTPException(status_code=404, detail="Донор не найден")
        
        # Получаем кампанию
        campaign = db.query(Campaign).filter(Campaign.id == campaign_id).first()
        if not campaign:
            raise HTTPException(status_code=404, detail="Кампания не найдена")
        
        # Проверяем риск через ML API
        tx_count = db.query(Donation).filter(Donation.user_id == donor.id).count()
        is_blacklisted = False
        risk_score = blockchain_manager.check_risk_score(amount_wei, tx_count, is_blacklisted)
        
        if risk_score > 0.8:
            raise HTTPException(status_code=400, detail=f"Транзакция отклонена из-за высокого риска: {risk_score:.2f}")
        
        # Создаем пожертвование через индивидуальный контракт
        deployer = ContractDeployer()
        
        # Используем адрес контракта кампании (если есть) или общий адрес
        contract_address = getattr(campaign, 'contract_address', None) or "0x0000000000000000000000000000000000000000"
        
        # В реальном проекте здесь будет вызов функции donate в смарт-контракте
        # Пока возвращаем заглушку
        tx_hash = f"0x{os.urandom(32).hex()}"
        
        # Создаем запись о пожертвовании в БД
        donation = Donation(
            user_id=donor.id,
            campaign_id=campaign_id,
            amount=amount_wei / 1e18,
            timestamp=datetime.utcnow(),
            tx_hash=tx_hash  # Сохраняем хеш транзакции
        )
        db.add(donation)
        db.commit()
        
        return {
            "tx_hash": tx_hash,
            "status": "pending",
            "amount_wei": amount_wei,
            "risk_score": risk_score,
            "contract_address": contract_address,
            "message": "Пожертвование отправлено в индивидуальный контракт"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка создания пожертвования: {str(e)}")


@app.get("/donations/{telegram_id}")
def get_user_donations(telegram_id: str, db: Session = Depends(get_db)):
    """Получение всех транзакций пользователя по telegram_id"""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Пользователь не найден")
    donations = db.query(Donation).filter(Donation.user_id == user.id).all()
    result = []
    for d in donations:
        result.append({
            "id": d.id,
            "campaign_id": d.campaign_id,
            "amount": d.amount,
            "timestamp": d.timestamp,
            "tx_hash": d.tx_hash  # Используем сохраненный tx_hash
        })
    return result