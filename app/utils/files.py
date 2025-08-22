from typing import Dict, List, Tuple
import os
import time

# Кешуємо products.txt по mtime, щоб не читати файл кожен раз
_CACHE: Dict[str, object] = {"mtime": None, "data": {}}

def _read_products_raw(path: str) -> Dict[str, List[Tuple[str, int]]]:
    categories: Dict[str, List[Tuple[str, int]]] = {}
    current: str | None = None
    if not os.path.exists(path):
        return categories
    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                if current is None:
                    continue
                name, price = line.split("=", 1)
                name = name.strip()
                price_str = price.strip().replace(" ", "")
                try:
                    price_val = int(price_str)
                except ValueError:
                    continue
                categories.setdefault(current, []).append((name, price_val))
            else:
                current = line
                categories.setdefault(current, [])
    return categories

def read_products(path: str = "data/products.txt") -> Dict[str, List[Tuple[str, int]]]:
    try:
        mtime = os.path.getmtime(path)
    except FileNotFoundError:
        _CACHE["mtime"] = None
        _CACHE["data"] = {}
        return {}
    if _CACHE["mtime"] != mtime:
        _CACHE["data"] = _read_products_raw(path)
        _CACHE["mtime"] = mtime
    return _CACHE["data"]
