from aiogram.utils.keyboard import InlineKeyboardBuilder

def main_menu_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="Список категорій", callback_data="main:cats")
    kb.button(text="Поповнити баланс", callback_data="main:topup")
    kb.adjust(1)
    return kb.as_markup()
