"""Génération de l'image de progression (PNG).

Fond : image du boss / de la phase. En haut à gauche : nom du boss ou de l'ultime.
En bas à gauche : progression (X/Y boss vaincus, ou « Phase X »).
À droite : pulls (boss en cours, ou pulls par phase) puis, en gros, le meilleur %.
"""
import os
from datetime import datetime

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 800, 300
PAD = 28
BG = (22, 24, 31)
TEXT = (240, 242, 246)
MUTED = (190, 196, 208)
ACCENT = (240, 150, 60)
KILL = (90, 210, 130)
OUTLINE = (10, 11, 15)

_FONT_CANDIDATES = {
    True: ["C:/Windows/Fonts/segoeuib.ttf", "DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    False: ["C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def font(size, bold=False):
    for path in _FONT_CANDIDATES[bold]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def fit(draw, text, fnt, max_w):
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=fnt) > max_w:
        text = text[:-1]
    return text + "…"


def fit_font(draw, text, size, max_w, bold=True, min_size=20):
    """Réduit la taille de police jusqu'à ce que le texte tienne."""
    while size > min_size and draw.textlength(text, font=font(size, bold)) > max_w:
        size -= 2
    return font(size, bold)


def cover(img, w, h):
    """Redimensionne et recadre l'image pour remplir w×h (comme CSS background-size: cover)."""
    scale = max(w / img.width, h / img.height)
    resized = img.resize((max(w, round(img.width * scale)), max(h, round(img.height * scale))),
                         Image.LANCZOS)
    left, top = (resized.width - w) // 2, (resized.height - h) // 2
    out = resized.crop((left, top, left + w, top + h))
    if scale > 2.5:          # image trop petite pour 800×300 : flou pour masquer les pixels
        out = out.filter(ImageFilter.GaussianBlur(radius=min(12, scale * 1.5)))
    return out


def background(img):
    base = cover(img, W, H) if img else Image.new("RGB", (W, H), BG)
    base = base.convert("RGBA")
    # Assombrit l'image, davantage sur les bords où se trouve le texte.
    shade = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(shade)
    for x in range(W):
        edge = abs(x - W / 2) / (W / 2)                # 0 au centre, 1 sur les bords
        d.line([(x, 0), (x, H)], fill=(0, 0, 0, int(95 + 105 * edge)))
    return Image.alpha_composite(base, shade)


def text(d, xy, value, fnt, fill=TEXT, anchor="la"):
    d.text(xy, value, font=fnt, fill=fill, anchor=anchor,
           stroke_width=max(2, fnt.size // 18), stroke_fill=OUTLINE)


def render(view, team_name, out_path, bg_image=None):
    img = background(bg_image)
    d = ImageDraw.Draw(img)
    half = W // 2 + 40

    # En haut à gauche : nom du boss / de l'ultime, puis le static.
    title_font = fit_font(d, view["title"], 44, half - PAD)
    text(d, (PAD, PAD - 4), view["title"], title_font)
    sub = team_name or ""
    now = datetime.now()                     # date en anglais, quelle que soit la langue de Windows
    month = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[now.month - 1]
    sub += ("  ·  " if sub else "") + f"Updated {now.day} {month} {now:%H:%M}"
    text(d, (PAD, PAD + title_font.size + 6), sub, font(16), MUTED)

    # En bas à gauche : progression.
    cleared = view["cleared"]
    caption = "bosses defeated" if view["mode"] == "boss" else \
        ("ultimate" if cleared else "current phase")
    color = KILL if cleared else TEXT
    text(d, (PAD, H - PAD - 74), caption.upper(), font(16, True), MUTED, anchor="ls")
    text(d, (PAD, H - PAD + 4), view["progress_label"], font(72, True), color, anchor="ls")

    # À droite : pulls, puis meilleur %.
    right = W - PAD
    lines = view["pulls_lines"]
    size = 24 if len(lines) <= 4 else 20
    y = PAD - 2
    for line in lines:
        text(d, (right, y), line, font(size, True), TEXT, anchor="ra")
        y += size + 8

    if cleared:
        big, big_color, big_caption = "CLEAR", KILL, ""
    elif view["best_pct"] is not None:
        big, big_color, big_caption = f"{view['best_pct']:.1f}%", ACCENT, "best %"
    else:
        big, big_color, big_caption = "—", MUTED, "best %"
    big_font = fit_font(d, big, 72, W - half - PAD)
    big_y = max(H - PAD + 4, y + 22 + big_font.size)
    text(d, (right, big_y), big, big_font, big_color, anchor="rs")
    if big_caption:
        text(d, (right, big_y - big_font.size - 2), big_caption.upper(),
             font(16, True), MUTED, anchor="rs")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path
