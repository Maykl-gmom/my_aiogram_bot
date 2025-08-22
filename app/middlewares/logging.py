# app/middlewares/logging.py
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery, User
from typing import Callable, Dict, Any, Awaitable
import logging
import html

logger = logging.getLogger("bot")

def tag(u: User) -> str:
    return f"@{u.username} ({u.id})" if u.username else f"{u.full_name} ({u.id})"

class LoggingMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Any, Dict[str, Any]], Awaitable[Any]],
        event: Any,
        data: Dict[str, Any]
    ) -> Any:
        if isinstance(event, Message):
            text = html.escape(event.text or event.caption or "")
            logger.info(f"[СВ ] {tag(event.from_user)} | chat={event.chat.id} | {text}")
        elif isinstance(event, CallbackQuery):
            logger.info(f"[BTN] {tag(event.from_user)} | chat={event.message.chat.id} | {event.data or ''}")
        return await handler(event, data)
