# app/handlers/admin.py
from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.types.input_file import FSInputFile

from app.config import get_admin_id
from app.utils.inventory import complete_reservation, cancel_reservation, fetch_reservation
from app.utils.balance import add_balance, set_balance, get_balance

from app.utils.safe_answer import safe_answer
from app.utils.topup import fetch_topup, set_topup_status

router = Router()

def _is_admin(user_id: int) -> bool:
    try:
        return int(user_id) == get_admin_id()
    except Exception:
        return False

@router.callback_query(F.data.regexp(r"^admin:(approve|reject):"))
async def admin_actions(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await safe_answer(callback, "Тільки для адміністратора.", show_alert=True)
        return

    parts = callback.data.split(":")
    if len(parts) < 4:
        await safe_answer(callback, "Некоректні дані.", show_alert=True)
        return

    action, _, res_id_str, user_id_str = parts[0], parts[1], parts[2], parts[3]
    try:
        res_id = int(res_id_str)
        user_id = int(user_id_str)
    except ValueError:
        await safe_answer(callback, "Некоректні ID.", show_alert=True)
        return

    if parts[1] == "approve":
        # Завершити резерв і віддати файл користувачу
        path = complete_reservation(res_id)
        if not path:
            await safe_answer(callback, "Не вдалося завершити резерв (можливо, вже завершений).", show_alert=True)
            return
        # Відправка файлу користувачу
        try:
            await callback.message.bot.send_document(
                chat_id=user_id,
                document=FSInputFile(path),
                caption="Оплату підтверджено. Ваш файл."
            )
        except Exception:
            # Якщо файл не вліз як документ, просто скажемо користувачу
            await callback.message.bot.send_message(
                chat_id=user_id,
                text="Оплату підтверджено. Ваш файл підготовлений, але не вдалося надіслати документ."
            )
        await callback.message.edit_text(f"✅ Підтверджено. Відправив файл користувачу id={user_id}.")
        await safe_answer(callback, "Оплату підтверджено")

    elif parts[1] == "reject":
        ok = cancel_reservation(res_id)
        await callback.message.edit_text("❌ Оплату відхилено. Резерв скасовано.")
        # Попередимо користувача
        try:
            await callback.message.bot.send_message(
                chat_id=user_id,
                text="Оплату не підтверджено. Резерв скасовано."
            )
        except Exception:
            pass
        await safe_answer(callback, "Відхилено")

    else:
        await safe_answer(callback, "Невідома дія.", show_alert=True)

@router.callback_query(F.data.startswith("admin:approve_topup:"))
async def approve_topup(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await safe_answer(callback, "Тільки для адміністратора.", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) < 4:
        await safe_answer(callback, "Некоректні дані.", show_alert=True)
        return
    _, action, topup_id_str, user_id_str = parts
    try:
        topup_id = int(topup_id_str)
        user_id = int(user_id_str)
    except ValueError:
        await safe_answer(callback, "Некоректні ID.", show_alert=True)
        return
    row = fetch_topup(topup_id)
    if not row or row["status"] != "pending":
        await safe_answer(callback, "Заявка неактивна.", show_alert=True)
        return
    amount = int(row["amount"])
    set_topup_status(topup_id, "approved")
    new_bal = add_balance(user_id, amount)
    await callback.message.edit_text(f"✅ Поповнення {amount} грн підтверджено. Баланс користувача: {new_bal} грн.")
    try:
        await callback.message.bot.send_message(user_id, f"✅ Адмін підтвердив поповнення на {amount} грн. Ваш баланс: {new_bal} грн.")
    except Exception:
        pass
    await safe_answer(callback, "Поповнення зараховано")

@router.callback_query(F.data.startswith("admin:reject_topup:"))
async def reject_topup(callback: CallbackQuery):
    if not _is_admin(callback.from_user.id):
        await safe_answer(callback, "Тільки для адміністратора.", show_alert=True)
        return
    parts = callback.data.split(":")
    if len(parts) < 4:
        await safe_answer(callback, "Некоректні дані.", show_alert=True)
        return
    _, action, topup_id_str, user_id_str = parts
    try:
        topup_id = int(topup_id_str)
        user_id = int(user_id_str)
    except ValueError:
        await safe_answer(callback, "Некоректні ID.", show_alert=True)
        return
    row = fetch_topup(topup_id)
    if not row or row["status"] != "pending":
        await safe_answer(callback, "Заявка неактивна.", show_alert=True)
        return
    set_topup_status(topup_id, "rejected")
    await callback.message.edit_text("❌ Поповнення відхилено.")
    try:
        await callback.message.bot.send_message(user_id, "❌ Адмін відхилив поповнення. Звірте дані платежу та спробуйте ще раз.")
    except Exception:
        pass
    await safe_answer(callback, "Відхилено")
