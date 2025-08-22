# app/keyboards/admin.py
from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_review_kb(reservation_id: int, user_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Підтвердити оплату", callback_data=f"admin:approve:{reservation_id}:{user_id}")
    kb.button(text="❌ Відхилити", callback_data=f"admin:reject:{reservation_id}:{user_id}")
    kb.adjust(1)
    return kb.as_markup()
