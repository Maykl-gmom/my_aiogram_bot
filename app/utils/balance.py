import sqlite3
from pathlib import Path


DB_PATH = Path(__file__).resolve().parents[2] / "data" / "db.sqlite3"


def _init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER)")
    conn.commit()
    conn.close()


def add_balance(user_id: int, delta: int) -> int:
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    try:
        cur = conn.cursor()
        # гарантуємо, що користувач є у таблиці
        cur.execute(
            "INSERT OR IGNORE INTO users(user_id, balance) VALUES (?, 0)",
            (user_id,),
        )
        # змінюємо баланс
        cur.execute(
            "UPDATE users SET balance = COALESCE(balance, 0) + ? WHERE user_id = ?",
            (delta, user_id),
        )
        conn.commit()
        bal = cur.execute(
            "SELECT balance FROM users WHERE user_id = ?",
            (user_id,),
        ).fetchone()[0]
        return int(bal)
    finally:
        conn.close()


def set_balance(user_id: int, amount: int) -> int:
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO users(user_id, balance) VALUES (?, ?) "
        "ON CONFLICT(user_id) DO UPDATE SET balance=excluded.balance",
        (user_id, amount),
    )
    conn.commit()
    conn.close()
    return amount


def get_balance(user_id: int) -> int:
    _init_db()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return int(row[0]) if row else 0
