# app/handlers/balance.py
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from app.utils.telegram import safe_answer
from aiogram.fsm.context import FSMContext

from app.states.balance import Balance
from app.utils.balance import get_balance, add_balance, set_balance
from app.keyboards.admin_topup import admin_topup_review_kb
from app.keyboards.main import main_menu_kb
from app.keyboards.shop import confirm_kb, pay_or_cancel_kb
from app.config import get_admin_id, get_card_number
from app.utils.topup import create_topup, set_topup_status, fetch_topup

router = Router()

@router.callback_query(F.data == "main:topup")
async def start_topup(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Введи суму для поповнення від 100 до 8000 грн:")
    await state.set_state(Balance.entering_amount)
    await safe_answer(callback)

@router.message(Balance.entering_amount, F.text.regexp(r"^\d+$"))
async def got_amount(message: Message, state: FSMContext):
    amt = int(message.text)
    if amt < 100 or amt > 8000:
        await message.answer("Сума повинна бути від 100 до 8000. Спробуй ще раз:")
        return
    # На цьому етапі НЕ створюємо заявку. Спершу підтвердження.
    await state.update_data(amount=amt)
    await message.answer(
        f"Поповнення на <b>{amt} грн</b>.\nПідтвердити замовлення?",
        reply_markup=confirm_kb()
    )
    await state.set_state(Balance.confirming)

@router.message(Balance.entering_amount)
async def not_number(message: Message, state: FSMContext):
    await message.answer("Введи ціле число від 100 до 8000.")

# ----- підтвердження / скасування -----

@router.callback_query(Balance.confirming, F.data == "cancel")
async def topup_cancel(callback: CallbackQuery, state: FSMContext):
    bal = get_balance(callback.from_user.id)
    await callback.message.edit_text(
        f"Операцію скасовано.\nВаш баланс: <b>{bal} грн</b>",
        reply_markup=main_menu_kb()
    )
    await state.clear()
    await safe_answer(callback)

@router.callback_query(Balance.confirming, F.data == "confirm")
async def topup_confirm(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    amt = int(data.get("amount", 0))
    if amt < 100 or amt > 8000:
        await safe_answer(callback, "Некоректна сума", show_alert=True)
        await state.clear()
        return

    # Тепер створюємо заявку і показуємо інструкцію з карткою
    topup_id = create_topup(callback.from_user.id, amt)
    await state.update_data(topup_id=topup_id)

    card = get_card_number()
    await callback.message.edit_text(
        f"✅ Поповнення: <b>{amt} грн</b>\n"
        f"Карта для поповнення: <code>{card}</code>\n\n"
        f"Після оплати натисніть «Оплатив» і надішліть квитанцію (фото/скриншот).",
        reply_markup=pay_or_cancel_kb("topup")
    )
    await state.set_state(Balance.awaiting_admin)
    await safe_answer(callback, "Створено")

# ----- прийом квитанції -----

@router.message(Balance.awaiting_admin, F.photo)
async def topup_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    topup_id = data.get("topup_id")
    amount = data.get("amount")
    if not topup_id or not amount:
        await message.answer("Щось пішло не так із заявкою на поповнення.")
        await state.clear()
        return
    admin_id = get_admin_id()
    await message.forward(admin_id)
    await message.bot.send_message(
        chat_id=admin_id,
        text=(
            f"Квитанція на поповнення від {message.from_user.full_name} "
            f"(id={message.from_user.id})\n"
            f"Сума: {amount} грн\nЗаявка ID: {topup_id}"
        ),
        reply_markup=admin_topup_review_kb(int(topup_id), int(message.from_user.id))
    )
    await message.answer("Квитанцію надіслано адміну. Очікуйте рішення.")

@router.message(Balance.awaiting_admin, F.text)
async def topup_receipt_only_photo(message: Message, state: FSMContext):
    await message.answer("Будь ласка, надішліть саме фото/скриншот квитанції.")

# Кнопка «Оплатив» на етапі очікування квитанції (щоб не було «німого» кліку)
@router.callback_query(Balance.awaiting_admin, F.data == "pay:topup")
async def topup_paid_click(callback: CallbackQuery, state: FSMContext):
    await callback.message.edit_text(
        "Надішліть квитанцію про оплату (фото/скриншот) у відповідь на це повідомлення."
    )
    await safe_answer(callback, "Чекаю квитанцію")

# Скасування після створення заявки повертає у старт
@router.callback_query(Balance.awaiting_admin, F.data == "topup:cancel")
async def topup_cancel_after_created(callback: CallbackQuery, state: FSMContext):
    bal = get_balance(callback.from_user.id)
    await callback.message.edit_text(
        f"Операцію скасовано.\nВаш баланс: <b>{bal} грн</b>",
        reply_markup=main_menu_kb()
    )
    await state.clear()
    await safe_answer(callback)

# ----- автоперехід з «бракує N грн» -----

@router.callback_query(F.data.startswith("topup:auto:"))
async def topup_auto_amount(callback: CallbackQuery, state: FSMContext):
    # Викликається зі сторони магазину, коли не вистачає коштів
    try:
        amt = int(callback.data.split("topup:auto:", 1)[1])
    except Exception:
        await safe_answer(callback, "Некоректна сума", show_alert=True)
        return
    if amt < 100:
        amt = 100
    if amt > 8000:
        amt = 8000
    await state.update_data(amount=amt)
    await callback.message.edit_text(
        f"Поповнення на <b>{amt} грн</b>.\nПідтвердити замовлення?",
        reply_markup=confirm_kb()
    )
    await state.set_state(Balance.confirming)
    await safe_answer(callback)
