from aiogram import Router, F
from aiogram.types import CallbackQuery
from app.utils.topup import fetch_topup, set_topup_status
from app.utils.balance import add_balance
from app.config import get_admin_id
from app.utils.telegram import safe_answer

router = Router()

@router.callback_query(F.data.startswith("topup:approve:"))
async def topup_approve(callback: CallbackQuery):
    # формат: topup:approve:{tid}:{uid}:{amount}
    try:
        _, _, stid, suid, samt = callback.data.split(":", 4)
        tid = int(stid); uid = int(suid); amount = int(samt)
    except Exception:
        await callback.answer("Некоректні дані.", show_alert=True); return

    t = fetch_topup(tid)
    if not t or t.status != "pending":
        await callback.answer("Заявка неактивна або вже оброблена.", show_alert=True); return

    new_bal = add_balance(uid, amount)
    set_topup_status(tid, "approved")

    # повідомляємо користувача
    try:
        await callback.message.bot.send_message(uid, f"✅ Поповнення підтверджено: +{amount} грн. Ваш баланс: {new_bal} грн")
    except Exception:
        pass

    await callback.message.edit_text(f"✅ TopUp {tid}: +{amount} грн користувачу {uid}. Баланс тепер {new_bal} грн")
    await safe_answer(callback)

@router.callback_query(F.data.startswith("topup:reject:"))
async def topup_reject(callback: CallbackQuery):
    try:
        _, _, stid = callback.data.split(":", 2)
        tid = int(stid)
    except Exception:
        await callback.answer("Некоректні дані.", show_alert=True); return

    t = fetch_topup(tid)
    if not t or t.status != "pending":
        await callback.answer("Заявка неактивна або вже оброблена.", show_alert=True); return

    set_topup_status(tid, "rejected")
    await callback.message.edit_text(f"⛔ TopUp {tid} відхилено.")
    await safe_answer(callback)
