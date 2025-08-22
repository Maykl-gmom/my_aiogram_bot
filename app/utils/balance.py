import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).resolve().parents[2] / "data" / "db.sqlite3"

def _init():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS users (user_id INTEGER PRIMARY KEY, balance INTEGER)")
    conn.commit()
    conn.close()

def add_balance(user_id: int, delta: int) -> int:
    _init()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("INSERT INTO users(user_id, balance) VALUES (?, 0) ON CONFLICT(user_id) DO NOTHING", (user_id,))
    cur.execute("UPDATE users SET balance = COALESCE(balance,0) + ? WHERE user_id = ?", (delta, user_id))
    conn.commit()
    bal = cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()[0]
    conn.close()
    return bal

def set_balance(user_id: int, amount: int) -> int:
    _init()
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
    _init()
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    row = cur.execute("SELECT balance FROM users WHERE user_id=?", (user_id,)).fetchone()
    conn.close()
    return int(row[0]) if row else 0


# --- TOPUPS (user-initiated recharges) ---
DB_PATH = "data/db.sqlite3"

def _init_topups():
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("CREATE TABLE IF NOT EXISTS topups (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, amount INTEGER NOT NULL, status TEXT NOT NULL, created_at INTEGER NOT NULL)")
        conn.commit()

def create_topup(user_id: int, amount: int) -> int:
    _init_topups()
    import time
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO topups(user_id, amount, status, created_at) VALUES (?, ?, ?, ?)", (user_id, int(amount), "pending", int(time.time())))
        conn.commit()
        return int(cur.lastrowid)

def set_topup_status(topup_id: int, status: str):
    _init_topups()
    status = str(status)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE topups SET status=? WHERE id=?", (status, int(topup_id)))
        conn.commit()

def fetch_topup(topup_id: int):
    _init_topups()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT id, user_id, amount, status, created_at FROM topups WHERE id=?", (int(topup_id),)).fetchone()
        if not row:
            return None
        return {"id": row[0], "user_id": row[1], "amount": row[2], "status": row[3], "created_at": row[4]}
