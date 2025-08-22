
from aiogram.exceptions import TelegramBadRequest

async def safe_answer(callback, *args, **kwargs):
    """
    Безпечно відповідає на callbackQuery.
    Ігнорує "query is too old / query ID is invalid".
    Використовуй на початку кожного callback-хендлера.
    """
    try:
        await callback.answer(*args, **kwargs)
    except TelegramBadRequest as e:
        msg = str(e)
        if "query is too old" in msg or "query ID is invalid" in msg:
            return
        raise
