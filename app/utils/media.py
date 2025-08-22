from pathlib import Path
from PIL import Image
import os

CACHE_DIR = Path("data/cache/photos")
CACHE_DIR.mkdir(parents=True, exist_ok=True)

def ensure_jpeg(src_path: Path) -> Path:
    """
    Гарантує JPEG-файл для відправки як фото.
    Якщо src вже .jpg/.jpeg — повертає його.
    Інакше конвертує у data/cache/photos/<stem>.jpg і повертає новий шлях.
    """
    src = Path(src_path)
    if src.suffix.lower() in [".jpg", ".jpeg"]:
        return src

    # Цільовий файл у кеші
    dst = (CACHE_DIR / src.with_suffix(".jpg").name)

    # Уникнути колізій і перезаписів
    i = 1
    while dst.exists():
        dst = CACHE_DIR / f"{src.stem}_{i}.jpg"
        i += 1

    # Конвертація
    with Image.open(src) as im:
        # Якщо прозорий — кладемо на білий фон
        if im.mode in ("RGBA", "LA") or (im.mode == "P" and "transparency" in im.info):
            bg = Image.new("RGB", im.size, (255, 255, 255))
            im = im.convert("RGBA")
            bg.paste(im, mask=im.split()[-1])
            im = bg
        else:
            im = im.convert("RGB")

        # Обмеження, щоб Telegram не бурчав
        max_side = 4096
        w, h = im.size
        if max(w, h) > max_side:
            scale = max_side / float(max(w, h))
            im = im.resize((int(w*scale), int(h*scale)))

        im.save(dst, format="JPEG", quality=85, optimize=True, progressive=True)

    return dst
