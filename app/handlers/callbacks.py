# app/handlers/callbacks.py
from aiogram import Router, F
from aiogram.types import CallbackQuery

router = Router()

@router.callback_query(F.data == "ping")
async def on_ping(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer("Pong ✅")

@router.callback_query(F.data == "help")
async def on_help(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "Команди:\n"
        "/start — привітання\n"
        "/help — список команд\n"
        "Напиши «меню» — побачиш кнопки"
    )
