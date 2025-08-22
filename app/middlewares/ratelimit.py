from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from typing import Callable, Dict, Any, Awaitable
import time

# Простий антиспам: 3 повідомлення за 2 секунди; дебаунс однакових кнопок 2 секунди.
class RateLimitMiddleware(BaseMiddleware):
    def __init__(self, msg_quota: int = 3, msg_window: float = 2.0, cb_debounce: float = 2.0):
        self.msg_quota = msg_quota
        self.msg_window = msg_window
        self.cb_debounce = cb_debounce
        self._msg_state: Dict[int, list[float]] = {}         # user_id -> timestamps
        self._cb_state: Dict[int, tuple[str, float]] = {}    # user_id -> (last_data, ts)

    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        now = time.time()

        if isinstance(event, Message):
            uid = event.from_user.id
            hist = self._msg_state.get(uid, [])
            hist = [t for t in hist if now - t <= self.msg_window]
            hist.append(now)
            self._msg_state[uid] = hist
            if len(hist) > self.msg_quota:
                # чемно і тихо ігноруємо флуд
                try:
                    await event.answer("Занадто часто. Повільніше.")
                except Exception:
                    pass
                return  # не викликаємо хендлер
            return await handler(event, data)

        if isinstance(event, CallbackQuery):
            uid = event.from_user.id
            last = self._cb_state.get(uid)
            if last and last[0] == (event.data or "") and (now - last[1]) <= self.cb_debounce:
                # дубль того ж кліку — ігноруємо
                try:
                    await event.answer("В обробці…", show_alert=False)
                except Exception:
                    pass
                return
            self._cb_state[uid] = (event.data or "", now)
            return await handler(event, data)

        return await handler(event, data)
