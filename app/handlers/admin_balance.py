from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from app.utils.balance import add_balance, set_balance, get_balance

try:
    from app.config import ADMIN_ID
except Exception:
    import os

    ADMIN_ID = int(os.getenv("ADMIN_ID", "123456"))

router = Router()


def _is_admin(message: Message) -> bool:
    return str(message.from_user.id) == str(ADMIN_ID)


@router.message(Command("balance"))
async def cmd_balance(message: Message):
    bal = get_balance(message.from_user.id)
    await message.answer(f"💰 Ваш баланс: <b>{bal}</b>")


@router.message(Command("addbal"))
async def cmd_addbal(message: Message):
    if not _is_admin(message):
        return await message.answer("Нема доступу.")
    parts = message.text.split()
    if len(parts) != 3:
        return await message.answer("Формат: /addbal <user_id> <сума>")
    try:
        uid = int(parts[1])
        delta = int(parts[2])
    except ValueError:
        return await message.answer("user_id і сума мають бути цілими числами.")
    new_bal = add_balance(uid, delta)
    await message.answer(f"✅ User {uid}: баланс {new_bal} (зміна {delta:+d}).")


@router.message(Command("setbal"))
async def cmd_setbal(message: Message):
    if not _is_admin(message):
        return await message.answer("Нема доступу.")
    parts = message.text.split()
    if len(parts) != 3:
        return await message.answer("Формат: /setbal <user_id> <сума>")
    try:
        uid = int(parts[1])
        amount = int(parts[2])
    except ValueError:
        return await message.answer("user_id і сума мають бути цілими числами.")
    new_bal = set_balance(uid, amount)
    await message.answer(f"✅ User {uid}: баланс встановлено {new_bal}.")


@router.message(Command("give"))
async def cmd_give_reply(message: Message):
    """Зручно в групі: відповідаєш на повідомлення юзера і пишеш /give 150"""
    if not _is_admin(message):
        return await message.answer("Нема доступу.")
    if not message.reply_to_message:
        return await message.answer("Зроби команду у відповідь на повідомлення користувача.")
    parts = message.text.split()
    if len(parts) != 2:
        return await message.answer("Формат: у відповіді /give <сума>")
    try:
        delta = int(parts[1])
    except ValueError:
        return await message.answer("Сума має бути цілим числом.")
    uid = message.reply_to_message.from_user.id
    new_bal = add_balance(uid, delta)
    await message.answer(f"✅ User {uid}: баланс {new_bal} (зміна {delta:+d}).")
