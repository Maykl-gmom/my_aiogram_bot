from aiogram.utils.keyboard import InlineKeyboardBuilder

def resume_reserve_kb(reservation_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="🔁 Повернутись до резерву", callback_data="reserve:resume")
    kb.button(text="❌ Скасувати резерв", callback_data="reserve:cancel")
    kb.adjust(1)
    return kb.as_markup()
