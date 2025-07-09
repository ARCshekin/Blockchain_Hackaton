import asyncio
import logging
import json
import time

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, Filter
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo, Message
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties

from router import router
from models import DonationData

API_TOKEN = "7673290587:AAGGQMLUpRYi-S8Jp_pcrht31j8ArMrfy2U"
NGROK_URL = "https://8bc757589ee1.ngrok-free.app"

logging.basicConfig(level=logging.DEBUG)

# Инициализируем бота с использованием DefaultBotProperties
bot = Bot(
    token=API_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)


dp = Dispatcher()
# Включаем роутер с нашими хендлерами
dp.include_router(router)


if __name__ == "__main__":
    asyncio.run(dp.start_polling(bot))
