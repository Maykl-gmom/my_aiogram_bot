# app/handlers/fallback.py
from aiogram import Router, F
from aiogram.types import Message

router = Router()

@router.message(F.text)
async def fallback(message: Message):
    await message.answer("Не знаю такої команди. Напиши «меню» або /start.")
