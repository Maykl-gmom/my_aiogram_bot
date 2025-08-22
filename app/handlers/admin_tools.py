from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.config import get_admin_id
from app.utils.inventory import walk_stock_counts, count_reserved_by_product, count_completed_by_product
from app.utils.files import read_products

router = Router()

def _is_admin(uid: int) -> bool:
    try:
        return uid == get_admin_id()
    except Exception:
        return False

@router.message(Command("stock"))
async def cmd_stock(message: Message):
    if not _is_admin(message.from_user.id):
        return
    stock = walk_stock_counts()
    reserved = count_reserved_by_product()
    if not stock and not reserved:
        await message.answer("Склад порожній. Резервів немає.")
        return
    # Формуємо звіт
    lines = ["<b>Склад</b> (avail | reserved):"]
    # злиття ключів
    keys = set(stock.keys()) | set(reserved.keys())
    for cat, prod in sorted(keys):
        a = stock.get((cat, prod), 0)
        r = reserved.get((cat, prod), 0)
        if a == 0 and r == 0:
            continue
        lines.append(f"• <b>{cat}</b> / {prod}: <code>{a}</code> | <code>{r}</code>")
    await message.answer("\n".join(lines))

@router.message(Command("stats"))
async def cmd_stats(message: Message):
    if not _is_admin(message.from_user.id):
        return
    completed = count_completed_by_product()
    if not completed:
        await message.answer("Ще немає завершених замовлень.")
        return
    catalog = read_products()
    # ціни беремо з поточного каталогу; якщо товару вже немає — вважаємо 0
    total_orders = 0
    total_amount = 0
    lines = ["<b>Статистика продажів</b>:"]
    for (cat, prod), n in sorted(completed.items()):
        price = 0
        for name, p in catalog.get(cat, []):
            if name == prod:
                price = p
                break
        total_orders += n
        total_amount += n * price
        lines.append(f"• <b>{cat}</b> / {prod}: {n} шт × {price} = <b>{n*price}</b>")
    lines.append(f"\nРазом: <b>{total_orders}</b> шт на суму <b>{total_amount}</b>")
    await message.answer("\n".join(lines))
