# bot.py
import asyncio
import logging

from aiogram import Bot, Dispatcher
from app.utils.commands import setup_bot_commands
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from app.config import get_token
from app.handlers import setup_routers
from app.utils.inventory import ensure_dirs, init_db, expire_overdue
from app.middlewares.logging import LoggingMiddleware
from app.middlewares.active_reserve import ActiveReserveHintMiddleware
from app.middlewares.ratelimit import RateLimitMiddleware
from app.middlewares.errors import ErrorShieldMiddleware
from dotenv import load_dotenv

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("bot")
load_dotenv()
bot = Bot(token=get_token(), default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

dp.message.middleware(LoggingMiddleware())
dp.message.middleware(ActiveReserveHintMiddleware())
dp.message.middleware(RateLimitMiddleware())
dp.message.middleware(ErrorShieldMiddleware())
dp.callback_query.middleware(LoggingMiddleware())

setup_routers(dp)


async def _expiry_watcher():
    # кожну хвилину перевіряємо прострочені резерви
    while True:
        expire_overdue()
        # можна додати нотифікації, але поки тихо
        await asyncio.sleep(60)


async def main():
    # встановлюємо меню команд для юзерів та адміна
    await setup_bot_commands(bot)
    logger.info("Бот запускається...")
    try:
        ensure_dirs()
        init_db()
        asyncio.create_task(_expiry_watcher())
        await dp.start_polling(bot)
    finally:
        logger.info("Бот зупиняється... Закриваю сесію")
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Зупинено з клавіатури або системою")
