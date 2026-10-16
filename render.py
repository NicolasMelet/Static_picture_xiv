"""Génération de l'image de progression (PNG)."""
import io
import os
from datetime import datetime

import requests
from PIL import Image, ImageDraw, ImageFont

from fflogs import boss_image_url, zone_image_url

W = 640
PAD = 20
ROW_H = 64
BG = (22, 24, 31)
CARD = (32, 35, 45)
TEXT = (235, 237, 242)
MUTED = (150, 156, 170)
TRACK = (52, 56, 70)
BAR = (225, 140, 60)
KILL = (80, 200, 120)

_FONT_CANDIDATES = {
    True: ["C:/Windows/Fonts/segoeuib.ttf", "DejaVuSans-Bold.ttf",
           "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"],
    False: ["C:/Windows/Fonts/segoeui.ttf", "DejaVuSans.ttf",
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"],
}
_img_cache = {}


def font(size, bold=False):
    for path in _FONT_CANDIDATES[bold]:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def fetch_image(url, size):
    key = (url, size)
    if key not in _img_cache:
        try:
            r = requests.get(url, timeout=20)
            r.raise_for_status()
            img = Image.open(io.BytesIO(r.content)).convert("RGBA")
        except Exception:
            img = Image.new("RGBA", (size, size), TRACK)
        _img_cache[key] = img.resize((size, size), Image.LANCZOS)
    return _img_cache[key]


def rounded(img, radius):
    mask = Image.new("L", img.size, 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, *img.size), radius, fill=255)
    out = img.copy()
    out.putalpha(mask)
    return out


def fit(draw, text, fnt, max_w):
    if draw.textlength(text, font=fnt) <= max_w:
        return text
    while text and draw.textlength(text + "…", font=fnt) > max_w:
        text = text[:-1]
    return text + "…"


def render(prog, team_name, out_path):
    encs = prog["encounters"]
    header_h = 120
    h = header_h + len(encs) * (ROW_H + 8) + 44
    img = Image.new("RGBA", (W, h), BG)
    d = ImageDraw.Draw(img)

    # En-tête : image du contenu + nom + compteur
    icon = rounded(fetch_image(zone_image_url(prog["zone_id"]), 84), 12)
    img.alpha_composite(icon, (PAD, PAD))
    x = PAD + 84 + 16
    cleared = prog["total"] and prog["done"] >= prog["total"]
    d.text((x, PAD + 2), fit(d, prog["zone_name"], font(24, True), W - x - PAD - (110 if cleared else 0)),
           font=font(24, True), fill=TEXT)
    d.text((x, PAD + 36), team_name, font=font(17), fill=MUTED)
    unit = "phases" if prog["mode"] == "phases" else "boss"
    d.text((x, PAD + 62), f"{prog['done']}/{prog['total']} {unit} vaincus",
           font=font(17, True), fill=KILL if prog["done"] else BAR)

    # Pastille "CLEAR" si tout est fait
    if cleared:
        d.rounded_rectangle((W - PAD - 96, PAD + 4, W - PAD, PAD + 36), 8, fill=KILL)
        d.text((W - PAD - 48, PAD + 20), "CLEAR", font=font(17, True), fill=BG, anchor="mm")

    # Une ligne par boss
    y = header_h
    for enc in encs:
        d.rounded_rectangle((PAD, y, W - PAD, y + ROW_H), 10, fill=CARD)
        bicon = rounded(fetch_image(boss_image_url(enc["id"]), 48), 8)
        img.alpha_composite(bicon, (PAD + 8, y + 8))
        tx = PAD + 8 + 48 + 12
        right_w = 170
        d.text((tx, y + 9), fit(d, enc["name"], font(17, True), W - tx - PAD - right_w),
               font=font(17, True), fill=TEXT)

        if enc["kills"]:
            progress, color = 1.0, KILL
            label = f"KILL ×{enc['kills']}"
        elif enc["best_pct"] is not None:
            progress, color = max(0.0, 1 - enc["best_pct"] / 100), BAR
            label = f"{enc['best_pct']:.1f}%"
            if enc["phase_name"]:
                label = f"{enc['phase_name']} · {enc['best_boss_pct']:.1f}%" \
                    if enc["best_boss_pct"] is not None else f"{enc['phase_name']} · {label}"
        else:
            progress, color, label = 0.0, MUTED, "Pas encore tenté"

        # Barre de progression
        bx0, bx1, by = tx, W - PAD - right_w, y + 40
        d.rounded_rectangle((bx0, by, bx1, by + 10), 5, fill=TRACK)
        if progress > 0:
            d.rounded_rectangle((bx0, by, bx0 + max(10, int((bx1 - bx0) * progress)), by + 10),
                                5, fill=color)

        d.text((W - PAD - 14, y + 22), fit(d, label, font(18, True), right_w - 20),
               font=font(18, True), fill=color, anchor="rm")
        if enc["pulls"]:
            d.text((W - PAD - 14, y + 46), f"{enc['pulls']} pull{'s' if enc['pulls'] > 1 else ''}", font=font(13),
                   fill=MUTED, anchor="rm")
        y += ROW_H + 8

    d.text((PAD, h - 30), "Données : FFLogs", font=font(13), fill=MUTED)
    d.text((W - PAD, h - 30), "MAJ " + datetime.now().strftime("%d/%m/%Y %H:%M"),
           font=font(13), fill=MUTED, anchor="ra")

    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    img.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path
