"""Génération de l'image de progression (PNG, 850 × 450, même format que les images de fond).

En haut à gauche : nom du boss ou de l'ultime.
En bas à gauche  : meilleur % (en gros), la phase en cours s'il y en a une, puis « N pulls ».
En bas à droite  : raid -> X/Y en gros ; ultime -> « Pulls: » puis le pull auquel chaque phase a
                   été passée pour la première fois (P1: 156, P2: 824...).
"""
import os

from PIL import Image, ImageDraw, ImageFilter, ImageFont

W, H = 850, 450
PAD = 30
BG = (22, 24, 31)
TEXT = (255, 255, 255)
ACCENT = (255, 214, 64)          # meilleur %
KILL = (110, 230, 140)
OUTLINE = (0, 0, 0)

_FONT_CANDIDATES = {
    True: ["C:/Windows/Fonts/segoeuib.ttf", "DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    False: ["C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}


def font(size, bold=True):
    for path in _FONT_CANDIDATES[bold]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


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
    if scale > 2.5:          # image trop petite : flou pour masquer les pixels
        out = out.filter(ImageFilter.GaussianBlur(radius=min(12, scale * 1.5)))
    return out


def background(img):
    base = cover(img, W, H) if img else Image.new("RGB", (W, H), BG)
    base = base.convert("RGBA")
    # Assombrit légèrement le haut (titre) et davantage le bas (chiffres), le centre reste net.
    shade = Image.new("RGBA", (W, H))
    d = ImageDraw.Draw(shade)
    for y in range(H):
        t = y / H
        top = max(0.0, 1 - t / 0.30)            # 1 en haut -> 0 à 30 %
        bottom = max(0.0, (t - 0.45) / 0.55)    # 0 à 45 % -> 1 en bas
        d.line([(0, y), (W, y)], fill=(0, 0, 0, int(25 + 110 * top + 170 * bottom ** 1.3)))
    return Image.alpha_composite(base, shade)


def text(d, xy, value, fnt, fill=TEXT, anchor="la"):
    d.text(xy, value, font=fnt, fill=fill, anchor=anchor,
           stroke_width=max(2, fnt.size // 16), stroke_fill=OUTLINE)


def render(view, team_name, out_path, bg_image=None):
    """team_name n'est plus affiché ; le paramètre est gardé pour compatibilité."""
    img = background(bg_image)
    d = ImageDraw.Draw(img)
    cleared = view["cleared"]

    # En haut à gauche : nom du boss / de l'ultime.
    text(d, (PAD, PAD - 6), view["title"], fit_font(d, view["title"], 52, W - 2 * PAD))

    # En bas à gauche, de bas en haut : « N pulls », phase en cours, meilleur %.
    y = H - PAD + 6
    pulls = view.get("pulls", 0)
    text(d, (PAD, y), f"{pulls} pull{'s' if pulls != 1 else ''}", font(28), TEXT, anchor="ls")
    y -= 28 + 14
    phase_label = view["progress_label"] if view["mode"] == "phases" else \
        (f"Phase {view['phase']}" if view.get("phase") else None)
    if phase_label and not cleared:
        text(d, (PAD, y), phase_label, font(44), TEXT, anchor="ls")
        y -= 44 + 12
    if cleared:
        big, color = "CLEAR", KILL
    elif view["best_pct"] is not None:
        big, color = f"{view['best_pct']:.1f}%", ACCENT
    else:
        big, color = "—", TEXT
    text(d, (PAD, y), big, font(96), color, anchor="ls")

    # En bas à droite.
    right = W - PAD
    if view["mode"] == "phases":
        lines = view["pulls_lines"]
        size = 28 if len(lines) <= 5 else 24
        y = H - PAD + 6
        for line in reversed(lines):
            text(d, (right, y), line, font(size), TEXT, anchor="rs")
            y -= size + 8
        if lines:
            text(d, (right, y), "Pulls:", font(size), TEXT, anchor="rs")
    else:
        text(d, (right, H - PAD + 8), view["progress_label"], font(96),
             KILL if cleared else TEXT, anchor="rs")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path
