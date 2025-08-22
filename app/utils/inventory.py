
from pathlib import Path
# Абсолютна база: .../ll (app/utils -> parents[2])
BASE_DIR = Path(__file__).resolve().parents[2]
DATA_DIR = BASE_DIR / "data"
STOCK_DIR = str(DATA_DIR / "stock")
RESERVED_DIR = str(DATA_DIR / "reserved")
PROCESSED_DIR = str(DATA_DIR / "processed")

import os
import sqlite3
import time
import shutil
from dataclasses import dataclass
from typing import Optional, List, Tuple, Dict

from app.config import get_reserve_seconds, get_allowed_exts

DB_PATH = os.path.join(DATA_DIR, "db.sqlite3")


RESERVE_SECONDS = get_reserve_seconds()
ALLOWED_EXTS = get_allowed_exts()

def now_ts() -> int:
    return int(time.time())

def ensure_dirs():
    for p in [DATA_DIR, STOCK_DIR, RESERVED_DIR, PROCESSED_DIR]:
        os.makedirs(p, exist_ok=True)

def db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH, isolation_level=None)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with db() as conn:
        conn.execute("""
        CREATE TABLE IF NOT EXISTS reservations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            category TEXT NOT NULL,
            product TEXT NOT NULL,
            file_name TEXT NOT NULL,
            stock_path TEXT NOT NULL,
            reserved_path TEXT NOT NULL,
            status TEXT NOT NULL,      -- reserved | completed | canceled | expired
            created_at INTEGER NOT NULL,
            expires_at INTEGER NOT NULL
        )""")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_res_status ON reservations(status)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_res_user ON reservations(user_id)")

def _allowed_file(name: str) -> bool:
    _, ext = os.path.splitext(name)
    return ext.lower() in ALLOWED_EXTS

def list_stock_files(category: str, product: str) -> list[str]:
    import os
    base = os.path.join(STOCK_DIR, category, product)
    if not os.path.isdir(base):
        return []
    allowed = os.getenv("ALLOWED_EXTS", ".jpg,.jpeg,.png,.webp")
    allowed_set = { (e.strip().lower() if e.strip().startswith(".") else f".{e.strip().lower()}") for e in allowed.split(",") if e.strip() }
    entries = []
    for entry in os.scandir(base):
        if not entry.is_file():
            continue
        name = entry.name
        if name.startswith("."):
            continue
        ext = os.path.splitext(name)[1].lower()
        if allowed_set and ext not in allowed_set:
            continue
        try:
            mtime = entry.stat().st_mtime
        except Exception:
            mtime = 0
        entries.append((mtime, name))
    entries.sort(key=lambda t: (t[0], t[1]))  # найстаріші спочатку
    return [name for _, name in entries]

def has_stock(category: str, product: str) -> bool:
    return len(list_stock_files(category, product)) > 0

def available_products_map(catalog: Dict[str, List[Tuple[str, int]]]) -> Dict[str, List[Tuple[str, int]]]:
    result: Dict[str, List[Tuple[str, int]]] = {}
    for cat, items in catalog.items():
        avail = [(n, p) for (n, p) in items if has_stock(cat, n)]
        if avail:
            result[cat] = avail
    return result

@dataclass
class Reservation:
    id: int
    user_id: int
    category: str
    product: str
    file_name: str
    stock_path: str
    reserved_path: str
    status: str
    created_at: int
    expires_at: int

def fetch_reservation(res_id: int) -> Optional[Reservation]:
    with db() as conn:
        r = conn.execute("SELECT * FROM reservations WHERE id=?", (res_id,)).fetchone()
        if not r: return None
        return Reservation(**dict(r))

def fetch_active_reservation_for_user(user_id: int) -> Optional[Reservation]:
    with db() as conn:
        r = conn.execute(
            "SELECT * FROM reservations WHERE user_id=? AND status='reserved' ORDER BY created_at DESC LIMIT 1",
            (user_id,)
        ).fetchone()
        return Reservation(**dict(r)) if r else None

def reserve_first_file(category: str, product: str, user_id: int) -> Optional[Reservation]:
    ensure_dirs(); init_db()
    files = list_stock_files(category, product)
    if not files:
        return None
    file_name = files[0]
    stock_path = os.path.join(STOCK_DIR, category, product, file_name)

    created = now_ts()
    expires = created + RESERVE_SECONDS
    with db() as conn:
        conn.execute("""INSERT INTO reservations(user_id, category, product, file_name,
                      stock_path, reserved_path, status, created_at, expires_at)
                      VALUES(?,?,?,?,?,?,?,?,?)""",
                     (user_id, category, product, file_name, stock_path, "", "reserved", created, expires))
        res_id = conn.execute("SELECT last_insert_rowid() AS id").fetchone()["id"]

    res_dir = os.path.join(RESERVED_DIR, str(res_id))
    os.makedirs(res_dir, exist_ok=True)
    reserved_path = os.path.join(res_dir, file_name)
    shutil.move(stock_path, reserved_path)
    with db() as conn:
        conn.execute("UPDATE reservations SET reserved_path=? WHERE id=?", (reserved_path, res_id))
    return fetch_reservation(res_id)

def cancel_reservation(res_id: int) -> bool:
    r = fetch_reservation(res_id)
    if not r or r.status != "reserved":
        return False
    dest_dir = os.path.join(STOCK_DIR, r.category, r.product)
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, r.file_name)
    if os.path.exists(r.reserved_path):
        shutil.move(r.reserved_path, dest_path)
    with db() as conn:
        conn.execute("UPDATE reservations SET status='canceled' WHERE id=?", (res_id,))
    return True

def complete_reservation(res_id: int) -> Optional[str]:
    r = fetch_reservation(res_id)
    if not r or r.status != "reserved":
        return None
    dest_dir = os.path.join(PROCESSED_DIR, r.category, r.product, str(r.user_id))
    os.makedirs(dest_dir, exist_ok=True)
    dest_path = os.path.join(dest_dir, r.file_name)
    if os.path.exists(r.reserved_path):
        shutil.move(r.reserved_path, dest_path)
    with db() as conn:
        conn.execute("UPDATE reservations SET status='completed' WHERE id=?", (res_id,))
    return dest_path

def expire_overdue() -> List[int]:
    ensure_dirs(); init_db()
    now = int(time.time())
    expired_ids: List[int] = []
    with db() as conn:
        rows = conn.execute("SELECT id FROM reservations WHERE status='reserved' AND expires_at < ?", (now,)).fetchall()
        expired_ids = [row["id"] for row in rows]
    for rid in expired_ids:
        r = fetch_reservation(rid)
        if not r:
            continue
        if os.path.exists(r.reserved_path):
            dest_dir = os.path.join(STOCK_DIR, r.category, r.product)
            os.makedirs(dest_dir, exist_ok=True)
            dest_path = os.path.join(dest_dir, r.file_name)
            shutil.move(r.reserved_path, dest_path)
        with db() as conn:
            conn.execute("UPDATE reservations SET status='expired' WHERE id=?", (rid,))
    return expired_ids

# ---- агрегації для /stock та /stats ----
def count_reserved_by_product() -> Dict[tuple, int]:
    with db() as conn:
        rows = conn.execute("""
            SELECT category, product, COUNT(*) AS c
            FROM reservations
            WHERE status='reserved'
            GROUP BY category, product
        """).fetchall()
    return {(r["category"], r["product"]): int(r["c"]) for r in rows}

def count_completed_by_product() -> Dict[tuple, int]:
    with db() as conn:
        rows = conn.execute("""
            SELECT category, product, COUNT(*) AS c
            FROM reservations
            WHERE status='completed'
            GROUP BY category, product
        """).fetchall()
    return {(r["category"], r["product"]): int(r["c"]) for r in rows}

def walk_stock_counts() -> Dict[tuple, int]:
    """Рахує кількість файлів у stock для кожного (категорія, товар)."""
    result: Dict[tuple, int] = {}
    if not os.path.isdir(STOCK_DIR):
        return result
    for cat in sorted(os.listdir(STOCK_DIR)):
        cat_dir = os.path.join(STOCK_DIR, cat)
        if not os.path.isdir(cat_dir): 
            continue
        for prod in sorted(os.listdir(cat_dir)):
            prod_dir = os.path.join(cat_dir, prod)
            if not os.path.isdir(prod_dir):
                continue
            cnt = len([f for f in os.listdir(prod_dir) if not f.startswith(".") and _allowed_file(f)])
            result[(cat, prod)] = cnt
    return result
