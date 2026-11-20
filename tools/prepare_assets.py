# -*- coding: utf-8 -*-
"""Собирает icon.ico и assets/golden_cookie.png.

Иконка: assets/icon_src.png
Спрайт: assets/cookie_src.png (если нет — кроп из иконки)
"""
import os
import sys
import ctypes

try:
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)
except Exception:
    pass

for stream in (sys.stdout, sys.stderr):
    try:
        stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")
ICO_SRC = os.path.join(ASSETS, "icon_src.png")
TPL_SRC = os.path.join(ASSETS, "cookie_src.png")

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]
TIGHT_UP_TO = 48
TIGHT_FRACTION = 0.60
TPL_FRACTION = 0.58
TPL_SIZE = 64


def center_crop(im, fraction):
    side = max(1, int(min(im.size) * fraction))
    cx, cy = im.width // 2, im.height // 2
    half = side // 2
    return im.crop((cx - half, cy - half, cx - half + side, cy - half + side))


def trim(im):
    im = im.convert("RGBA")
    alpha = im.getchannel("A")
    if alpha.getextrema()[0] < 250:
        bbox = alpha.getbbox()
    else:
        rgb = im.convert("RGB")
        bg = rgb.getpixel((0, 0))
        mask = Image.new("L", im.size, 0)
        src, dst = rgb.load(), mask.load()
        for y in range(im.height):
            for x in range(im.width):
                p = src[x, y]
                if abs(p[0] - bg[0]) + abs(p[1] - bg[1]) + abs(p[2] - bg[2]) > 42:
                    dst[x, y] = 255
        bbox = mask.getbbox()
    return im.crop(bbox) if bbox else im


def square_pad(im, size, pad):
    inner = max(1, int(size * (1 - pad * 2)))
    im = im.convert("RGBA").resize((inner, inner), Image.LANCZOS)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(im, ((size - inner) // 2, (size - inner) // 2), im)
    return out


def main():
    if not os.path.exists(ICO_SRC):
        sys.exit("нет assets/icon_src.png")

    src = Image.open(ICO_SRC).convert("RGBA")
    if abs(src.width - src.height) > 2:
        print("! не квадрат: %s — обрезаю по центру" % (src.size,))
        side = min(src.size)
        src = center_crop(src, side / max(src.size))

    tight = center_crop(src, TIGHT_FRACTION)
    frames = [square_pad(tight if s <= TIGHT_UP_TO else src, s,
                         0.02 if s <= TIGHT_UP_TO else 0.0) for s in ICO_SIZES]
    frames[-1].save(os.path.join(ROOT, "icon.ico"), format="ICO",
                    sizes=[(s, s) for s in ICO_SIZES], append_images=frames[:-1])
    print("icon.ico готов")

    if os.path.exists(TPL_SRC):
        base = Image.open(TPL_SRC)
        print("спрайт: свой (assets/cookie_src.png)")
    else:
        base = center_crop(src, TPL_FRACTION)
        print("спрайт: кроп из иконки (assets/cookie_src.png не найден)")

    tpl = square_pad(trim(base), TPL_SIZE, 0.03)
    bg = Image.new("RGBA", tpl.size, (0, 0, 0, 255))
    bg.alpha_composite(tpl)
    bg.convert("RGB").save(os.path.join(ASSETS, "golden_cookie.png"))
    print("assets/golden_cookie.png готов")


if __name__ == "__main__":
    main()