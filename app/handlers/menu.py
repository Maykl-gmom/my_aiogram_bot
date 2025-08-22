# app/handlers/menu.py
from aiogram import Router, F
from aiogram.types import Message
from app.keyboards.common import menu_kb

router = Router()

@router.message(F.text.lower() == "меню")
async def show_menu(message: Message):
    await message.answer("Обери дію:", reply_markup=menu_kb())
