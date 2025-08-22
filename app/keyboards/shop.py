from aiogram.utils.keyboard import InlineKeyboardBuilder
from typing import List, Tuple

def categories_kb(categories: list[str]):
    kb = InlineKeyboardBuilder()
    for c in categories:
        kb.button(text=c, callback_data=f"cat:{c}")
    kb.adjust(2)
    return kb.as_markup()

def products_kb(products: List[Tuple[str, int]]):
    kb = InlineKeyboardBuilder()
    for idx, (name, price) in enumerate(products):
        kb.button(text=f"{name}", callback_data=f"prod:{idx}")
    kb.button(text="⬅️ Назад до категорій", callback_data="back:cats")
    kb.adjust(1)
    return kb.as_markup()

def confirm_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Підтвердити", callback_data="confirm")
    kb.button(text="❌ Скасувати", callback_data="cancel")
    kb.adjust(2)
    return kb.as_markup()

def cancel_reserve_kb():
    kb = InlineKeyboardBuilder()
    kb.button(text="❌ Скасувати резерв", callback_data="reserve:cancel")
    return kb.as_markup()


def pay_or_cancel_kb(kind: str = "reserve"):
    # kind: "reserve" або "topup"
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    if kind == "topup":
        kb.button(text="Оплатив", callback_data="pay:topup")
        kb.button(text="Скасувати резерв", callback_data="topup:cancel")
    else:
        kb.button(text="Оплатив", callback_data="pay:reserve")
        kb.button(text="Скасувати резерв", callback_data="reserve:cancel")
    kb.adjust(2)
    # додамо кнопку оплати з балансу лише для режиму reserve
    try:
        if str(mode) == "reserve":
            kb.button(text="💳 Оплатити з балансу", callback_data="paybal:now")
            # Тобі вирішувати як компонувати: один стовпець ок
            kb.adjust(1)
    except Exception:
        pass
    return kb.as_markup()


def confirm_with_balance_kb():
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    kb = InlineKeyboardBuilder()
    kb.button(text="✅ Підтвердити замовлення", callback_data="confirm")
    kb.button(text="❌ Скасувати", callback_data="cancel")
    kb.button(text="💳 Оплатити балансом", callback_data="paybal:try")
    kb.adjust(1)
    return kb.as_markup()
