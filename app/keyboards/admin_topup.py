from aiogram.utils.keyboard import InlineKeyboardBuilder

def admin_topup_review_kb(topup_id: int, user_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Зарахувати", callback_data=f"admin:approve_topup:{topup_id}:{user_id}")
    kb.button(text="❌ Відхилити", callback_data=f"admin:reject_topup:{topup_id}:{user_id}")
    kb.adjust(1)
    return kb.as_markup()
