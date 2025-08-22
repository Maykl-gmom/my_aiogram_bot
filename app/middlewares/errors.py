from aiogram import BaseMiddleware
from typing import Callable, Dict, Any, Awaitable
from aiogram.types import Message, CallbackQuery
import logging

logger = logging.getLogger("bot")

class ErrorShieldMiddleware(BaseMiddleware):
    async def __call__(self, handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]], event: Any, data: Dict[str, Any]) -> Any:
        try:
            return await handler(event, data)
        except Exception as e:
            logger.exception("Handler error: %s", e)
            try:
                if isinstance(event, CallbackQuery):
                    await event.answer("Сталася помилка. Спробуйте ще раз.")
                    await event.message.answer("Сталася помилка. Спробуйте ще раз.")
                elif isinstance(event, Message):
                    await event.answer("Сталася помилка. Спробуйте ще раз.")
            except Exception:
                pass
