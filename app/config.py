# app/config.py
import os


def get_token() -> str:
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError('BOT_TOKEN не задано. export BOT_TOKEN="123456:ABC..."')
    return token


def get_admin_id() -> int:
    raw = os.getenv("ADMIN_ID")
    if not raw:
        raise RuntimeError('ADMIN_ID не задано. export ADMIN_ID="7898735133"')
    try:
        return int(raw)
    except ValueError:
        raise RuntimeError("ADMIN_ID має бути цілим числом")


def get_reserve_seconds() -> int:
    raw = os.getenv("RESERVE_SECONDS", "").strip()
    if not raw:
        return 30 * 60
    try:
        v = int(raw)
        return max(30, v)  # мінімум 30 сек, щоб не було цирку
    except ValueError:
        return 30 * 60


def get_allowed_exts() -> set[str]:
    raw = os.getenv("ALLOWED_EXTS", ".txt,.csv")
    # приклад перевизначення: export ALLOWED_EXTS=".txt,.key,.bin"
    return {
        e.strip().lower() if e.strip().startswith(".") else "." + e.strip().lower()
        for e in raw.split(",")
        if e.strip()
    }


def get_card_number() -> str:
    return os.getenv("CARD_NUMBER", "0000-0000-0000-0000")


# ===== auto-added =====
try:
    from dotenv import load_dotenv

    load_dotenv()
except Exception:
    pass

ADMIN_ID = int(os.getenv("ADMIN_ID", "123456"))  # підстав свій у .env
# ===== end auto-added =====
