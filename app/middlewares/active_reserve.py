from aiogram import BaseMiddleware
from aiogram.types import Message
from typing import Callable, Dict, Any, Awaitable
import time

from app.utils.inventory import fetch_active_reservation_for_user
from app.keyboards.resume import resume_reserve_kb
from app.states.shop import Shop

class ActiveReserveHintMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        # Працюємо лише для Message від юзерів, щоб не лізти в службові апдейти
        if isinstance(event, Message) and not event.from_user.is_bot:
            state = data.get("state")
            current_state = None
            if state:
                try:
                    current_state = await state.get_state()
                except Exception:
                    current_state = None

            # Якщо вже у процесі оплати/очікування — не заважаємо
            if current_state in {Shop.waiting_receipt.state, Shop.awaiting_admin.state, Shop.reserved.state}:
                return await handler(event, data)

            res = fetch_active_reservation_for_user(event.from_user.id)
            if res:
                # Порахуємо, чи ще живий резерв
                remain = max(0, res.expires_at - int(time.time()))
                mins, secs = divmod(remain, 60)
                await event.answer(
                    "У вас є активний резерв:\n"
                    f"• Категорія: <b>{res.category}</b>\n"
                    f"• Товар: <b>{res.product}</b>\n"
                    f"⏳ Залишилось: {mins} хв {secs} с\n\n"
                    "Повернутись до інструкції або скасувати?",
                    reply_markup=resume_reserve_kb(res.id)
                )
        return await handler(event, data)
