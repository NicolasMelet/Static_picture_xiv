"""Draws the progression image (PNG, 850 x 450, the size of the background images).

Top left:     fight name.
Bottom left:  best % (large), current phase (ultimates only), then "N pulls".
Bottom right: raid -> X/Y; ultimate -> "Pulls:" and the pull on which each phase
              was first cleared (P1: 156, P2: 824...).
"""
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont

WIDTH, HEIGHT = 850, 450
MARGIN = 40
TITLE_SIZE, BIG_SIZE, SMALL_SIZE = 38, 68, 22
PHASE_SIZE = BIG_SIZE * 2 // 3      # "Phase X": two thirds of the best %
PULLS_SIZE = BIG_SIZE // 2          # "N pulls": half of the best %

EMPTY_BACKGROUND = (22, 24, 31)
WHITE = (255, 255, 255)
YELLOW = (255, 214, 64)
GREEN = (110, 230, 140)
GREY = (200, 204, 212)             # every pull counter
BLACK = (0, 0, 0)

# Lilita One (SIL Open Font License, see fonts/lilita-one-license.txt), bundled with the program.
FONT_DIR = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent)) / "fonts"
FONT_FILES = [FONT_DIR / "lilita-one-regular.ttf", "C:/Windows/Fonts/segoeuib.ttf",
              "DejaVuSans-Bold.ttf"]


def font(size):
    for path in FONT_FILES:
        try:
            return ImageFont.truetype(path, size)
        except OSError:
            continue
    return ImageFont.load_default(size)


def fitting_font(draw, text, size, max_width, min_size=20):
    """Largest font size (down from `size`) for which the text fits in max_width."""
    while size > min_size and draw.textlength(text, font=font(size)) > max_width:
        size -= 2
    return font(size)


def cover(image, width, height):
    """Scale and center-crop the image to fill width x height (like CSS background-size: cover)."""
    scale = max(width / image.width, height / image.height)
    size = (max(width, round(image.width * scale)), max(height, round(image.height * scale)))
    resized = image.resize(size, Image.LANCZOS)
    left, top = (resized.width - width) // 2, (resized.height - height) // 2
    cropped = resized.crop((left, top, left + width, top + height))
    if scale > 2.5:          # very small source image: blur to hide the pixels
        cropped = cropped.filter(ImageFilter.GaussianBlur(radius=min(12, scale * 1.5)))
    return cropped


def background(image):
    """Background image, slightly darkened at the top (title) and more at the bottom (numbers)."""
    base = cover(image, WIDTH, HEIGHT) if image else Image.new("RGB", (WIDTH, HEIGHT),
                                                               EMPTY_BACKGROUND)
    shade = Image.new("RGBA", (WIDTH, HEIGHT))
    draw = ImageDraw.Draw(shade)
    for y in range(HEIGHT):
        t = y / HEIGHT
        top = max(0.0, 1 - t / 0.30)            # 1 at the top -> 0 at 30 %
        bottom = max(0.0, (t - 0.45) / 0.55)    # 0 at 45 % -> 1 at the bottom
        draw.line([(0, y), (WIDTH, y)], fill=(0, 0, 0, int(25 + 110 * top + 170 * bottom ** 1.3)))
    return Image.alpha_composite(base.convert("RGBA"), shade)


def outlined_text(draw, xy, text, text_font, color=WHITE, anchor="la"):
    draw.text(xy, text, font=text_font, fill=color, anchor=anchor,
              stroke_width=max(2, text_font.size // 16), stroke_fill=BLACK)


def render(view, out_path, background_image=None):
    image = background(background_image)
    draw = ImageDraw.Draw(image)
    cleared = view["cleared"]

    # Top left: fight name.
    outlined_text(draw, (MARGIN, MARGIN - 4), view["title"],
                  fitting_font(draw, view["title"], TITLE_SIZE, WIDTH - 2 * MARGIN))

    # Bottom left, from the bottom up: pulls, current phase, best %.
    y = HEIGHT - MARGIN + 4
    pulls = view["pulls"]
    outlined_text(draw, (MARGIN, y), f"{pulls} pull{'s' if pulls != 1 else ''}",
                  font(PULLS_SIZE), GREY, anchor="ls")
    y -= PULLS_SIZE + 12
    if view["mode"] == "ultimate" and not cleared:      # raids never show their phase
        outlined_text(draw, (MARGIN, y), f"Phase {view['phase']}", font(PHASE_SIZE), anchor="ls")
        y -= PHASE_SIZE + 10
    if cleared:
        big_text, color = "CLEAR", GREEN
    elif view["best_pct"] is not None:
        big_text, color = f"{view['best_pct']:.1f}%", YELLOW
    else:
        big_text, color = "—", WHITE
    outlined_text(draw, (MARGIN, y), big_text, font(BIG_SIZE), color, anchor="ls")

    # Bottom right.
    right = WIDTH - MARGIN
    if view["mode"] == "ultimate":
        lines = [f"P{phase}: {pull}" for phase, pull in view["phase_clears"]]
        if lines:
            lines.insert(0, "Pulls:")
        y = HEIGHT - MARGIN + 4
        for line in reversed(lines):
            outlined_text(draw, (right, y), line, font(SMALL_SIZE), GREY, anchor="rs")
            y -= SMALL_SIZE + 6
    else:
        outlined_text(draw, (right, HEIGHT - MARGIN + 4), f"{view['done']}/{view['total']}",
                      font(PHASE_SIZE), GREEN if cleared else WHITE, anchor="rs")

    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    image.convert("RGB").save(out_path, "PNG", optimize=True)
    return out_path
