from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message
from pathlib import Path
import os, time
from app.config import ADMIN_ID
from app.utils.inventory import STOCK_DIR

router = Router()

# Білий список фото-розширень
ALLOWED_PHOTO_EXTS = {".jpg", ".jpeg", ".png", ".webp"}

def _is_admin(uid: int) -> bool:
    return str(uid) == str(ADMIN_ID)

@router.message(F.chat.type == "private", Command("addstock"))
async def addstock_cmd(message: Message):
    # Доступ: лише ПМ і лише адмін
    if not _is_admin(message.from_user.id):
        return

    # Формат: /addstock Категорія | Товар (у ВІДПОВІДІ на фото/документ)
    parts = message.text.split(None, 1)
    if len(parts) < 2 or "|" not in parts[1]:
        return await message.answer("Формат: /addstock Категорія | Товар (у ВІДПОВІДІ на фото/документ)")

    category, product = [x.strip() for x in parts[1].split("|", 1)]
    if not category or not product:
        return await message.answer("Вкажи обидва поля: Категорія | Товар")

    if not message.reply_to_message:
        return await message.answer("Зроби /addstock у ВІДПОВІДІ на повідомлення з фото або документом.")

    reply = message.reply_to_message

    # Витягуємо файл з reply
    file_id = None
    filename = None
    ext = None

    if reply.photo:
        # Найбільше фото; Telegram зберігає як jpeg
        file_id = reply.photo[-1].file_id
        ext = ".jpg"
        filename = f"{int(time.time())}{ext}"
    elif reply.document:
        file_id = reply.document.file_id
        name = reply.document.file_name or f"file_{int(time.time())}"
        ext = os.path.splitext(name)[1].lower()
        if ext not in ALLOWED_PHOTO_EXTS:
            return await message.answer("Тільки формати .jpg, .jpeg, .png, .webp будуть завантажені. Будь уважним!")
        filename = f"{int(time.time())}{ext}"
    else:
        return await message.answer("Потрібно фото або документ-ізображення (.jpg/.jpeg/.png/.webp).")

    # Папка призначення
    dest_dir = Path(STOCK_DIR) / category / product
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / filename

    # Завантажуємо файл з Telegram
    await message.bot.download(file_id, destination=dest_path)

    # Щоб черга була FIFO: нові файли в кінець (свіжий mtime)
    os.utime(dest_path, None)

    await message.answer(f"✅ Додано у сток:\nКатегорія: <b>{category}</b>\nТовар: <b>{product}</b>\nФайл: <code>{dest_path.name}</code>")
