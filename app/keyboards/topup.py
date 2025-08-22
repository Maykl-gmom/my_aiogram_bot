from aiogram.utils.keyboard import InlineKeyboardBuilder

def topup_waiting_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Я оплатив (надішлю квитанцію)", callback_data="topup:paid_hint")
    kb.button(text="❌ Скасувати поповнення", callback_data="topup:cancel")
    kb.adjust(1, 1)
    return kb.as_markup()

def topup_resume_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="🔁 Повернутись до поповнення", callback_data="topup:resume")
    kb.button(text="❌ Скасувати поповнення", callback_data="topup:cancel")
    kb.adjust(1, 1)
    return kb.as_markup()

def topup_admin_review_kb(tid: int, user_id: int, amount: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Зарахувати", callback_data=f"topup:approve:{tid}:{user_id}:{amount}")
    kb.button(text="⛔ Відхилити", callback_data=f"topup:reject:{tid}")
    kb.adjust(2)
    return kb.as_markup()
