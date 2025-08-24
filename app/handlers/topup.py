from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
import time

from app.states.topup import TopUp
from app.keyboards.topup import topup_waiting_kb, topup_admin_review_kb
from app.utils.topup import create_topup, fetch_active_topup_for_user, set_topup_status
from app.config import get_card_number, get_admin_id
from app.utils.telegram import safe_answer
from app.keyboards.main import main_menu_kb

router = Router()
MIN_AMOUNT = 100
MAX_AMOUNT = 8000


# Старт топапу
@router.message(Command("topup"))
@router.message(F.text.lower().in_({"поповнити баланс", "поповнення", "поповнення балансу"}))
async def topup_start(message: Message, state: FSMContext):
    await message.answer(
        f"Вкажіть суму поповнення одним числом від {MIN_AMOUNT} до {MAX_AMOUNT} грн."
    )
    await state.set_state(TopUp.enter_amount)


# Ввід суми
@router.message(TopUp.enter_amount, F.text)
async def topup_amount(message: Message, state: FSMContext):
    txt = (message.text or "").strip().replace(" ", "")
    if not txt.isdigit():
        await message.answer("Введи суму цифрами. Напр., 150")
        return
    amount = int(txt)
    if amount < MIN_AMOUNT or amount > MAX_AMOUNT:
        await message.answer(f"Сума має бути від {MIN_AMOUNT} до {MAX_AMOUNT} грн.")
        return

    t = create_topup(message.from_user.id, amount)  # pending + expires_at
    await state.update_data(topup_id=t.id, topup_amount=amount)

    remain = max(0, t.expires_at - int(time.time()))
    mins, secs = divmod(remain, 60)
    await message.answer(
        f"🧾 Сума поповнення: <b>{amount} грн</b>\n"
        f"Карта для переказу: <code>{get_card_number()}</code>\n"
        f"Час на відправку квитанції: <b>{mins} хв {secs} с</b>\n\n"
        f"Після оплати надішліть <b>квитанцію</b> (фото/скрин) у відповідь на це повідомлення.",
        reply_markup=topup_waiting_kb(),
    )
    await state.set_state(TopUp.waiting_receipt)


# Підказка, що робити
@router.callback_query(TopUp.waiting_receipt, F.data == "topup:paid_hint")
async def topup_paid_hint(callback: CallbackQuery, state: FSMContext):
    await callback.answer(
        "Надішліть фото/скрин квитанції у відповідь на повідомлення вище.", show_alert=True
    )


# Скасувати топап
@router.callback_query(F.data == "topup:cancel")
async def topup_cancel(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    tid = data.get("topup_id")
    if tid:
        set_topup_status(int(tid), "canceled")
    await state.clear()
    await callback.message.edit_text("Поповнення скасовано.", reply_markup=main_menu_kb())
    await safe_answer(callback)


# Резюм топапу
@router.callback_query(F.data == "topup:resume")
async def topup_resume(callback: CallbackQuery, state: FSMContext):
    t = fetch_active_topup_for_user(callback.from_user.id)
    if not t:
        await callback.answer("Активних поповнень немає.", show_alert=True)
        return
    await state.set_state(TopUp.waiting_receipt)
    await state.update_data(topup_id=t.id, topup_amount=t.amount)
    remain = max(0, t.expires_at - int(time.time()))
    mins, secs = divmod(remain, 60)
    await callback.message.edit_text(
        f"🧾 Активне поповнення: <b>{t.amount} грн</b>\n"
        f"Залишилось часу: <b>{mins} хв {secs} с</b>\n"
        f"Карту для переказу дивись у попередньому повідомленні.",
        reply_markup=topup_waiting_kb(),
    )
    await safe_answer(callback)


# Прийом квитанції: фото чи документ
@router.message(TopUp.waiting_receipt, F.photo | F.document)
async def topup_receipt(message: Message, state: FSMContext):
    data = await state.get_data()
    tid = data.get("topup_id")
    amount = data.get("topup_amount")
    if not tid or not amount:
        await message.answer("Почніть із введення суми: /topup")
        await state.set_state(TopUp.enter_amount)
        return

    admin_id = get_admin_id()
    # Пересилаємо чек адміну і додаємо інлайн-кнопки для апрува/реджекта
    try:
        await message.forward(admin_id)
        await message.bot.send_message(
            chat_id=admin_id,
            text=(
                f"🧾 Квитанція на поповнення\n"
                f"Користувач: {message.from_user.full_name} (id={message.from_user.id})\n"
                f"Сума: {amount} грн\n"
                f"TopUp ID: {tid}"
            ),
            reply_markup=topup_admin_review_kb(int(tid), int(message.from_user.id), int(amount)),
        )
    except Exception:
        pass

    await message.answer("Квитанцію надіслано на перевірку. Очікуйте рішення адміністратора.")
    await state.set_state(TopUp.awaiting_admin)
