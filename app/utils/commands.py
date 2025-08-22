from aiogram.types import BotCommand, BotCommandScopeAllChatAdministrators, BotCommandScopeChat
from app.config import ADMIN_ID

async def setup_bot_commands(bot):
    # Команди для звичайних користувачів (мінімум)
    user_cmds = [
        BotCommand(command="start", description="Почати"),
        BotCommand(command="balance", description="Мій баланс"),
        BotCommand(command="shop", description="Магазин"),
        BotCommand(command="help", description="Допомога"),
    ]

    # Команди для адміна
    admin_cmds = [
        BotCommand(command="menu", description="Адмін-меню"),
        BotCommand(command="addbal", description="Додати баланс"),
        BotCommand(command="setbal", description="Встановити баланс"),
        BotCommand(command="stock", description="Склад: залишки"),
        BotCommand(command="stats", description="Статистика"),
    ]

    # 1) За замовчуванням для всіх — юзерські
    await bot.set_my_commands(user_cmds)

    # 2) Для всіх адміністраторів у групах — адмінський набір
    await bot.set_my_commands(admin_cmds, scope=BotCommandScopeAllChatAdministrators())

    # 3) Для приватного чату з конкретним ADMIN_ID — адмінський набір
    #    Це дає тобі свої команди у ПМ, іншим — ні.
    try:
        await bot.set_my_commands(admin_cmds, scope=BotCommandScopeChat(chat_id=int(ADMIN_ID)))
    except Exception:
        # якщо ADMIN_ID не валідний/не заданий — просто пропускаємо
        pass
