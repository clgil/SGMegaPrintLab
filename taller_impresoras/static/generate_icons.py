"""
Generador de iconos PNG para la PWA SGMegaPrintLab.

Ejecutar desde la raíz del proyecto:
    python static/generate_icons.py

Genera en static/icons/:
    - icon-192.png, icon-512.png (maskable-ready, fondo sólido)
    - apple-touch-icon.png (180x180)
"""
from PIL import Image, ImageDraw, ImageFont
import os

BASE = os.path.dirname(os.path.abspath(__file__))
ICONS_DIR = os.path.join(BASE, "icons")
os.makedirs(ICONS_DIR, exist_ok=True)

BG_TOP = (37, 99, 235)     # azul primario
BG_BOTTOM = (15, 23, 42)   # slate-900
FG = (255, 255, 255)


def load_font(size):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]
    for c in candidates:
        if os.path.exists(c):
            return ImageFont.truetype(c, size)
    return ImageFont.load_default()


def make_icon(size, path, maskable=False):
    img = Image.new("RGB", (size, size), BG_TOP)
    draw = ImageDraw.Draw(img)

    # Degradado vertical sencillo
    for y in range(size):
        t = y / max(size - 1, 1)
        r = int(BG_TOP[0] + (BG_BOTTOM[0] - BG_TOP[0]) * t)
        g = int(BG_TOP[1] + (BG_BOTTOM[1] - BG_TOP[1]) * t)
        b = int(BG_TOP[2] + (BG_BOTTOM[2] - BG_TOP[2]) * t)
        draw.line([(0, y), (size, y)], fill=(r, g, b))

    pad = int(size * 0.18) if maskable else int(size * 0.10)

    # Cuerpo de la impresora
    body = (pad, int(size * 0.40), size - pad, int(size * 0.72))
    draw.rounded_rectangle(body, radius=int(size * 0.05), fill=FG)

    # Hoja saliendo por arriba
    sheet = (int(size * 0.30), pad, int(size * 0.70), int(size * 0.44))
    draw.rounded_rectangle(sheet, radius=int(size * 0.02), fill=(226, 232, 240))
    line_w = max(2, int(size * 0.012))
    for i in range(3):
        ly = pad + int(size * 0.05) + i * int(size * 0.06)
        draw.line([(sheet[0] + int(size * 0.06), ly),
                   (sheet[2] - int(size * 0.06), ly)],
                  fill=(100, 116, 139), width=line_w)

    # Bandeja de salida inferior
    tray = (int(size * 0.24), int(size * 0.72), int(size * 0.76), int(size * 0.82))
    draw.rounded_rectangle(tray, radius=int(size * 0.02), fill=(203, 213, 225))

    # LED de estado
    led_r = int(size * 0.025)
    led_cx = size - pad - int(size * 0.06)
    led_cy = body[1] + int(size * 0.06)
    draw.ellipse([led_cx - led_r, led_cy - led_r, led_cx + led_r, led_cy + led_r],
                 fill=(34, 197, 94))

    # Texto "SG" sobre el cuerpo
    font = load_font(int(size * 0.16))
    text = "SG"
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    tx = (size - tw) // 2 - bbox[0]
    ty = (body[1] + body[3]) // 2 - th // 2 - bbox[1]
    draw.text((tx, ty), text, font=font, fill=BG_BOTTOM)

    img.save(path, "PNG")
    print(f"Creado: {path} ({size}x{size})")


if __name__ == "__main__":
    make_icon(192, os.path.join(ICONS_DIR, "icon-192.png"))
    make_icon(512, os.path.join(ICONS_DIR, "icon-512.png"))
    # Variantes maskable (contenido dentro del safe zone del 80%)
    make_icon(192, os.path.join(ICONS_DIR, "icon-maskable-192.png"), maskable=True)
    make_icon(512, os.path.join(ICONS_DIR, "icon-maskable-512.png"), maskable=True)
    # iOS / Android home screen
    make_icon(180, os.path.join(ICONS_DIR, "apple-touch-icon.png"))
    print("Iconos PWA generados correctamente.")
