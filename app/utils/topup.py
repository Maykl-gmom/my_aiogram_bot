import os, sqlite3, time
from dataclasses import dataclass
from typing import Optional, Dict, Any

DB_PATH = "data/db.sqlite3"

@dataclass
class Topup:
    id: int
    user_id: int
    amount: int
    status: str       # pending | approved | rejected | canceled | expired
    created_at: int
    expires_at: int

def _init_db():
    os.makedirs("data", exist_ok=True)
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS topups(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount INTEGER NOT NULL,
            status TEXT NOT NULL,
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL
        )""")
        conn.commit()

def _row_to_topup(row) -> Optional[Topup]:
    if not row: return None
    return Topup(id=row[0], user_id=row[1], amount=row[2], status=row[3], created_at=row[4], expires_at=row[5])

def create_topup(user_id: int, amount: int, ttl_seconds: Optional[int] = None) -> Topup:
    """Створює топап зі статусом pending і дедлайном."""
    _init_db()
    now = int(time.time())
    if ttl_seconds is None:
        ttl_seconds = int(os.getenv("TOPUP_SECONDS", "1800"))
    expires = now + int(ttl_seconds)
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO topups(user_id, amount, status, created_at, expires_at) VALUES(?,?,?,?,?)",
                    (int(user_id), int(amount), "pending", now, expires))
        conn.commit()
        tid = cur.lastrowid
        row = cur.execute("SELECT id,user_id,amount,status,created_at,expires_at FROM topups WHERE id=?", (tid,)).fetchone()
        return _row_to_topup(row)

def set_topup_status(tid: int, status: str):
    _init_db()
    with sqlite3.connect(DB_PATH) as conn:
        conn.execute("UPDATE topups SET status=? WHERE id=?", (str(status), int(tid)))
        conn.commit()

def fetch_topup(tid: int) -> Optional[Topup]:
    _init_db()
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("SELECT id,user_id,amount,status,created_at,expires_at FROM topups WHERE id=?", (int(tid),)).fetchone()
        return _row_to_topup(row)

def fetch_active_topup_for_user(user_id: int) -> Optional[Topup]:
    """Останній PENDING, що ще не прострочений."""
    _init_db()
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        row = conn.execute("""
            SELECT id,user_id,amount,status,created_at,expires_at
            FROM topups
            WHERE user_id=? AND status=pending AND expires_at > ?
            ORDER BY created_at DESC
            LIMIT 1
        """, (int(user_id), now)).fetchone()
        return _row_to_topup(row)

def expire_old_topups() -> int:
    """Скасовує прострочені pending."""
    _init_db()
    now = int(time.time())
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        rows = cur.execute("SELECT id FROM topups WHERE status=pending AND expires_at <= ?", (now,)).fetchall()
        ids = [r[0] for r in rows]
        if ids:
            cur.executemany("UPDATE topups SET status=expired WHERE id=?", [(i,) for i in ids])
            conn.commit()
        return len(ids)
