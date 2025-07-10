import asyncio
import os
import requests
from aiogram import Bot, Dispatcher, types, F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, CallbackQuery
from aiogram.utils.markdown import hbold
from dotenv import load_dotenv
from db import SessionLocal, User

load_dotenv()

API_TOKEN = os.getenv("BOT_TOKEN")
BACKEND_URL = "https://0ff1b77dcc4c.ngrok-free.app"

bot = Bot(token=API_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)
router = Router()
user_tokens = {}

class RegisterState(StatesGroup):
    waiting_for_username = State()
    waiting_for_password = State()

class WalletState(StatesGroup):
    waiting_for_seed_phrase = State()

class CampaignState(StatesGroup):
    waiting_for_title = State()
    waiting_for_description = State()

class DonateState(StatesGroup):
    waiting_for_amount = State()
    waiting_for_campaign = State()

# --- Inline Keyboard for main menu ---
def get_main_menu_keyboard(user_id=None):
    from aiogram.types import WebAppInfo
    keyboard = [
        [InlineKeyboardButton(text="Кошелёк", callback_data="wallet")],
        [InlineKeyboardButton(text="Создать кампанию", callback_data="campaign")],
        [InlineKeyboardButton(text="Список кампаний", callback_data="campaigns")],
        [InlineKeyboardButton(
            text="Пожертвовать",
            web_app=WebAppInfo(url=f"{BACKEND_URL}/donate?user_id={user_id}" if user_id else f"{BACKEND_URL}/donate")
        )],
        [InlineKeyboardButton(text="Статус транзакции", callback_data="status")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=keyboard)

# --- Проверка регистрации пользователя через backend ---
def is_registered(user_id: int) -> bool:
    with SessionLocal() as db:
        user = db.query(User).filter(User.telegram_id == str(user_id)).first()
        print(f"DEBUG is_registered: user_id={user_id}, found={user}, username={getattr(user, 'username', None)}, password_hash={getattr(user, 'password_hash', None)}")
        return user is not None and user.username and user.password_hash

@router.message(Command("start"))
async def send_welcome(message: Message):
    try:
        resp = requests.get(f"{BACKEND_URL}/wallet/info/{message.from_user.id}")
        if resp.status_code in (200, 400):
            welcome_text = (
                "👋 Вы уже зарегистрированы!\n\n"
                "Воспользуйтесь кнопками ниже для управления ботом."
            )
        else:
            welcome_text = (
                "🤖 Добро пожаловать в Charity Bot!\n\n"
                "Для начала работы выполните /register или воспользуйтесь кнопками ниже."
            )
    except Exception:
        welcome_text = (
            "🤖 Добро пожаловать в Charity Bot!\n\n"
            "Для начала работы выполните /register или воспользуйтесь кнопками ниже."
        )
    sent_msg = await message.answer(welcome_text, reply_markup=get_main_menu_keyboard(user_id=message.from_user.id))
    try:
        await message.bot.pin_chat_message(message.chat.id, sent_msg.message_id, disable_notification=True)
    except Exception:
        pass  # если не хватает прав, просто игнорируем

@router.message(Command("register"))
async def register_start(message: Message, state: FSMContext):
    await message.answer("Введите имя пользователя для регистрации:")
    await state.set_state(RegisterState.waiting_for_username)

@router.message(RegisterState.waiting_for_username)
async def register_username(message: Message, state: FSMContext):
    await state.update_data(username=message.text.strip())
    await message.answer("Теперь введите пароль:")
    await state.set_state(RegisterState.waiting_for_password)

@router.message(RegisterState.waiting_for_password)
async def register_password(message: Message, state: FSMContext):
    user_data = await state.get_data()
    username = user_data['username']
    password = message.text.strip()
    data = {
        "telegram_id": str(message.from_user.id),
        "username": username,
        "password": password
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/register/", json=data)
        if resp.status_code == 200:
            await message.answer("✅ Регистрация успешна! Можете создать кошелек и использовать бота.", reply_markup=get_main_menu_keyboard(user_id=message.from_user.id))
        else:
            error_msg = resp.json().get('detail', 'Неизвестная ошибка')
            await message.answer(f"❌ Ошибка регистрации: {error_msg}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()

@router.message(Command("wallet"))
async def wallet_start(message: Message, state: FSMContext):
    await message.answer("🔐 Введите seed phrase для создания кошелька:")
    await state.set_state(WalletState.waiting_for_seed_phrase)

@router.message(WalletState.waiting_for_seed_phrase)
async def create_wallet(message: Message, state: FSMContext):
    user_id = message.from_user.id
    seed_phrase = message.text.strip()
    data = {
        "telegram_id": str(user_id),
        "seed_phrase": seed_phrase
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/wallet/create/", json=data)
        if resp.status_code == 200:
            await message.answer("✅ Кошелек успешно создан! Теперь вы можете делать пожертвования.")
        else:
            error_msg = resp.json().get('detail', 'Неизвестная ошибка')
            await message.answer(f"❌ Ошибка создания кошелька: {error_msg}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()

@router.message(Command("campaign"))
async def campaign_start(message: Message, state: FSMContext):
    await message.answer("📝 Введите название кампании:")
    await state.set_state(CampaignState.waiting_for_title)

@router.message(CampaignState.waiting_for_title)
async def campaign_title(message: Message, state: FSMContext):
    await state.update_data(title=message.text.strip())
    await message.answer("📄 Введите описание кампании:")
    await state.set_state(CampaignState.waiting_for_description)

@router.message(CampaignState.waiting_for_description)
async def campaign_description(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()
    title = user_data['title']
    description = message.text.strip()
    data = {
        'title': title,
        'description': description,
        'telegram_id': str(user_id)
    }
    
    try:
        resp = requests.post(f"{BACKEND_URL}/campaigns/telegram/", json=data)
        if resp.status_code == 200:
            response_data = resp.json()
            await message.answer(f"✅ Кампания успешно создана!\n"
                               f"Название: {title}\n"
                               f"ID: {response_data.get('id')}\n"
                               f"Контракт: {response_data.get('contract_address', 'N/A')}")
        else:
            error_msg = resp.json().get('detail', 'Неизвестная ошибка')
            await message.answer(f"❌ Ошибка создания кампании: {error_msg}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()

@router.message(Command("donate"))
async def donate_start(message: Message, state: FSMContext):
    await message.answer("💰 Введите сумму пожертвования в wei:")
    await state.set_state(DonateState.waiting_for_amount)

@router.message(DonateState.waiting_for_amount)
async def donate_amount(message: Message, state: FSMContext):
    try:
        amount_wei = int(message.text)
        await state.update_data(amount_wei=amount_wei)
        await message.answer("🎯 Введите ID кампании для пожертвования:")
        await state.set_state(DonateState.waiting_for_campaign)
    except ValueError:
        await message.answer("❌ Пожалуйста, введите корректное число.")
        await state.clear()

@router.message(DonateState.waiting_for_campaign)
async def donate_campaign(message: Message, state: FSMContext):
    user_id = message.from_user.id
    user_data = await state.get_data()
    amount_wei = user_data['amount_wei']
    campaign_id = message.text.strip()
    data = {
        "donor": str(user_id),
        "amount_wei": amount_wei,
        "campaign_id": campaign_id
    }
    try:
        resp = requests.post(f"{BACKEND_URL}/donate", json=data)
        if resp.status_code == 200:
            response_data = resp.json()
            tx_hash = response_data.get("tx_hash", "N/A")
            risk_score = response_data.get("risk_score", "N/A")
            await message.answer(f"✅ Пожертвование отправлено!\n"
                                 f"Tx hash: {tx_hash}\n"
                                 f"Risk score: {risk_score}\n"
                                 f"Проверить статус: /status {tx_hash}")
        else:
            try:
                error_msg = resp.json().get('detail', 'Неизвестная ошибка')
            except:
                error_msg = resp.text
            await message.answer(f"❌ Ошибка пожертвования: {error_msg}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")
    await state.clear()

@router.message(Command("balance"))
async def check_balance(message: Message):
    user_id = message.from_user.id
    if not is_registered(user_id):
        reg_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")]]
        )
        await message.answer("❌ Сначала зарегистрируйтесь.", reply_markup=reg_kb)
        return
    try:
        resp = requests.get(f"{BACKEND_URL}/balance/{user_id}")
        if resp.status_code == 200:
            balance_data = resp.json()
            balance_eth = balance_data.get('balance_eth', 0)
            await message.answer(f"💰 Баланс кошелька: {balance_eth:.6f} ETH")
        else:
            error_msg = resp.json().get('detail', 'Неизвестная ошибка')
            await message.answer(f"❌ Ошибка получения баланса: {error_msg}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("status"))
async def handle_status(message: Message):
    args = message.text.split(maxsplit=1)
    if len(args) < 2:
        await message.answer("❌ Укажите хеш транзакции: /status <tx_hash>")
        return
    tx_hash = args[1].strip()
    try:
        resp = requests.get(f"{BACKEND_URL}/status/{tx_hash}")
        if resp.status_code == 200:
            status = resp.json()
            await message.answer(f"📊 Статус транзакции:\n{status}")
        else:
            await message.answer(f"❌ Ошибка получения статуса: {resp.text}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

@router.message(Command("campaigns"))
async def list_campaigns(message: Message):
    try:
        resp = requests.get(f"{BACKEND_URL}/campaigns/")
        if resp.status_code == 200:
            campaigns = resp.json()
            if campaigns:
                campaign_list = "📋 Список кампаний:\n\n"
                for campaign in campaigns:
                    campaign_list += f"🎯 ID: {campaign['id']}\n"
                    campaign_list += f"📝 Название: {campaign['title']}\n"
                    campaign_list += f"📄 Описание: {campaign['description']}\n"
                    campaign_list += "─" * 30 + "\n"
                await message.answer(campaign_list)
            else:
                await message.answer("📋 Кампании пока не созданы")
        else:
            await message.answer(f"❌ Ошибка получения списка кампаний: {resp.text}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

# --- Callback handlers for main menu ---
@router.callback_query(F.data == "wallet")
async def wallet_callback(call: CallbackQuery, state: FSMContext):
    print(f"DEBUG CALLBACK wallet: from_user.id={call.from_user.id}, data={call.data}")
    user_id = call.from_user.id
    if not is_registered(user_id):
        reg_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")]]
        )
        await call.message.answer("❌ Сначала зарегистрируйтесь.", reply_markup=reg_kb)
        await call.answer()
        return
    await wallet_start(call.message, state)
    await call.answer()

@router.callback_query(F.data == "campaign")
async def campaign_callback(call: CallbackQuery, state: FSMContext):
    print(f"DEBUG CALLBACK campaign: from_user.id={call.from_user.id}, data={call.data}")
    user_id = call.from_user.id
    if not is_registered(user_id):
        reg_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")]]
        )
        await call.message.answer("❌ Сначала зарегистрируйтесь.", reply_markup=reg_kb)
        await call.answer()
        return
    await campaign_start(call.message, state)
    await call.answer()

@router.callback_query(F.data == "campaigns")
async def campaigns_callback(call: CallbackQuery):
    await list_campaigns(call.message)
    await call.answer()

@router.callback_query(F.data == "donate")
async def donate_callback(call: CallbackQuery, state: FSMContext):
    print(f"DEBUG CALLBACK donate: from_user.id={call.from_user.id}, data={call.data}")
    user_id = call.from_user.id
    if not is_registered(user_id):
        reg_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")]]
        )
        await call.message.answer("❌ Сначала зарегистрируйтесь.", reply_markup=reg_kb)
        await call.answer()
        return
    await donate_start(call.message, state)
    await call.answer()

@router.callback_query(F.data == "balance")
async def balance_callback(call: CallbackQuery):
    print(f"DEBUG CALLBACK balance: from_user.id={call.from_user.id}, data={call.data}")
    user_id = call.from_user.id
    if not is_registered(user_id):
        reg_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")]]
        )
        await call.message.answer("❌ Сначала зарегистрируйтесь.", reply_markup=reg_kb)
        await call.answer()
        return
    await check_balance(call.message)
    await call.answer()

@router.callback_query(F.data == "status")
async def status_callback(call: CallbackQuery):
    user_id = call.from_user.id
    if not is_registered(user_id):
        reg_kb = InlineKeyboardMarkup(
            inline_keyboard=[[InlineKeyboardButton(text="Зарегистрироваться", callback_data="register")]]
        )
        await call.message.answer("❌ Сначала зарегистрируйтесь.", reply_markup=reg_kb)
        await call.answer()
        return
    # Получаем список транзакций пользователя
    try:
        resp = requests.get(f"{BACKEND_URL}/donations/{user_id}")
        if resp.status_code == 200:
            donations = resp.json()
            if not donations:
                await call.message.answer("У вас пока нет транзакций.")
                await call.answer()
                return
            # Формируем inline-клавиатуру
            keyboard = []
            for d in donations:
                label = f"...{d['tx_hash'][-10:]}" if d['tx_hash'] else f"ID {d['id']} (нет tx_hash)"
                callback_data = f"txstatus:{d['id']}"
                keyboard.append([InlineKeyboardButton(text=label, callback_data=callback_data)])
            markup = InlineKeyboardMarkup(inline_keyboard=keyboard)
            await call.message.answer("Выберите транзакцию:", reply_markup=markup)
        else:
            await call.message.answer("Ошибка получения списка транзакций.")
    except Exception as e:
        await call.message.answer(f"Ошибка: {e}")
    await call.answer()

@router.callback_query(F.data.startswith("txstatus:"))
async def txstatus_callback(call: CallbackQuery):
    await call.message.delete()
    user_id = call.from_user.id
    tx_id = call.data[len("txstatus:"):]
    try:
        resp = requests.get(f"{BACKEND_URL}/donations/{user_id}")
        if resp.status_code == 200:
            donations = resp.json()
            tx = next((d for d in donations if str(d['id']) == tx_id), None)
            if not tx:
                await call.message.answer("Транзакция не найдена.", reply_markup=get_main_menu_keyboard(user_id=call.from_user.id))
                await call.answer()
                return
            tx_hash = tx.get('tx_hash')
            if not tx_hash:
                await call.message.answer("Для этой транзакции нет tx_hash, статус недоступен.", reply_markup=get_main_menu_keyboard(user_id=call.from_user.id))
                await call.answer()
                return
            # Получаем статус транзакции
            resp2 = requests.get(f"{BACKEND_URL}/status/{tx_hash}")
            if resp2.status_code == 200:
                status = resp2.json()
                await call.message.answer(f"📊 Статус транзакции ...{tx_hash[-10:]}:\n{'\n'.join([f'{k}: {v}' for k, v in status.items()])}", reply_markup=get_main_menu_keyboard(user_id=call.from_user.id))
            else:
                await call.message.answer(f"❌ Ошибка получения статуса: {resp2.text}", reply_markup=get_main_menu_keyboard(user_id=call.from_user.id))
        else:
            await call.message.answer("Ошибка получения списка транзакций.", reply_markup=get_main_menu_keyboard(user_id=call.from_user.id))
    except Exception as e:
        await call.message.answer(f"❌ Ошибка: {e}", reply_markup=get_main_menu_keyboard(user_id=call.from_user.id))
    await call.answer()

@router.callback_query(F.data == "register")
async def register_callback(call: CallbackQuery, state: FSMContext):
    await register_start(call.message, state)
    await call.answer()

async def main():
    dp.include_router(router)
    print("🚀 Запуск бота...")
    print(f"Токен: {API_TOKEN[:10]}...")
    try:
        # Попробуем другой подход
        await dp.start_polling(bot, skip_updates=True)
    except Exception as e:
        print(f"❌ Ошибка запуска бота: {e}")
        await bot.session.close()

if __name__ == "__main__":
    asyncio.run(main())
