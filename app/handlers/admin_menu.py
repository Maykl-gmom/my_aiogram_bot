from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from app.config import ADMIN_ID

router = Router()

def _is_admin(user_id: int) -> bool:
    return str(user_id) == str(ADMIN_ID)

@router.message(Command("menu"))
async def admin_menu(message: Message):
    if not _is_admin(message.from_user.id):
        return  # тихо ігноруємо
    kb = InlineKeyboardBuilder()
    kb.button(text="➕ Додати баланс", callback_data="admin:addbal")
    kb.button(text="✏️ Встановити баланс", callback_data="admin:setbal")
    kb.button(text="📦 Склад", callback_data="admin:stock")
    kb.button(text="📊 Статистика", callback_data="admin:stats")
    kb.adjust(2, 2)
    await message.answer("Адмін-меню:", reply_markup=kb.as_markup())

@router.callback_query(F.data == "admin:stock")
async def cb_stock(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer()
    # сюди підв’яжеш свій рендер складу
    await callback.message.answer("Тут буде звіт по складу.")
    await callback.answer()

@router.callback_query(F.data == "admin:stats")
async def cb_stats(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.answer("Тут буде статистика.")
    await callback.answer()

@router.callback_query(F.data == "admin:addbal")
async def cb_addbal(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.answer("Надішли у форматі: <code>/addbal user_id сума</code>")
    await callback.answer()

@router.callback_query(F.data == "admin:setbal")
async def cb_setbal(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        return await callback.answer()
    await callback.message.answer("Надішли у форматі: <code>/setbal user_id сума</code>")
    await callback.answer()
