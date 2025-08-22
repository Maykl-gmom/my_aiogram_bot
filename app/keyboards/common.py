# app/keyboards/common.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

def menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Пінг", callback_data="ping")
    kb.button(text="Допомога", callback_data="help")
    kb.adjust(2)
    return kb.as_markup()
