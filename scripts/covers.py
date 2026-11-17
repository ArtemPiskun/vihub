"""Пул фоновых сцен для запасных обложек новостей (без текста, текст накладывает HTML).

Сцены берутся из общего генератора бота (gta6bot/card.py, репозиторий ArtemPiskun/gta6-bot).
Запуск один раз локально: python scripts/covers.py /path/to/gta6bot/card.py  -> assets/covers/c00..c23.jpg
"""
import importlib.util
import random
import sys
from pathlib import Path

from PIL import Image

src = Path(sys.argv[1] if len(sys.argv) > 1 else "/mnt/project-files/gta6-automation/gta6bot/card.py")
spec = importlib.util.spec_from_file_location("card", src)
card = importlib.util.module_from_spec(spec)
spec.loader.exec_module(card)

out = Path(__file__).resolve().parent.parent / "assets" / "covers"
out.mkdir(parents=True, exist_ok=True)
names = list(card.SCENES)
N = 24
for n in range(N):
    rnd = random.Random(f"vihub-{n}")
    scene = card.SCENES[names[n % len(names)]]
    top, mid, bot = card.PALETTES[rnd.choice(card.SCENE_PALETTES.get(scene.__name__, range(len(card.PALETTES))))]
    img = Image.new("RGB", (card.W, card.H))
    px = img.load()
    for y in range(card.H):
        for x in range(0, card.W, 4):
            t = min(1, max(0, (y / card.H) * 0.75 + (x / card.W) * 0.35))
            c = card._lerp(top, mid, t / 0.6) if t < 0.6 else card._lerp(mid, bot, (t - 0.6) / 0.4)
            for dx in range(4):
                px[x + dx, y] = c
    img = scene(img, rnd).convert("RGB").resize((640, 360), Image.LANCZOS)
    img.save(out / f"c{n:02d}.jpg", "JPEG", quality=78, optimize=True, progressive=True)
print(f"{N} covers -> {out}")
