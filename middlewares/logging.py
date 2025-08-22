# middlewares/logging.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, User
from typing import Callable, Dict, Any, Awaitable
import logging
import html

logger = logging.getLogger("bot")

def user_tag(u: User) -> str:
    if u.username:
        return f"@{u.username} ({u.id})"
    if u.full_name:
        return f"{u.full_name} ({u.id})"
    return f"id={u.id}"

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            u = event.from_user
            text = event.text or event.caption or ""
            # екранимо, щоб у лог не полетіли сирі теги
            text = html.escape(text)
            logger.info(f"[MSG] {user_tag(u)} | chat={event.chat.id} | {text}")

        elif isinstance(event, CallbackQuery):
            u = event.from_user
            data_str = event.data or ""
            logger.info(f"[CB ] {user_tag(u)} | chat={event.message.chat.id} | {data_str}")

        return await handler(event, data)
