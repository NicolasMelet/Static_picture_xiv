"""Background images, stored locally in one folder per fight: nothing is downloaded from FFLogs.

Names follow the convention described in catalog.py (lowercase, "-" between words, "_" before
the name). A fight's folder is found by its FFLogs name, the part after the last "_"
("m11s_the-tyrant" for The Tyrant), wherever it is. Inside it:
  - <anything>-p<n>.png is the image of phase n (e.g. fru-p3.png, howling-blade-p2.jpg);
  - any other image is the fight's image.
Ultimate: the current phase's image, otherwise default (no spoiler for phases not reached yet).
Raid:     the current phase's image if any, otherwise the fight's image, otherwise default.
"""
import logging
import re
import unicodedata
from pathlib import Path

from PIL import Image

import catalog

log = logging.getLogger("prog")
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
# Phase image file name (without extension): <anything>-p<n>, e.g. fru-p3 or dsr-dragon-king-p8.
PHASE_PATTERN = re.compile(r"-p0*(\d+)$", re.IGNORECASE)

README_TEXT = """prog fflogs - background images
==============================

  1_ultimates        one folder per ultimate
  2_savage-raids     expansion > tier > one folder per boss
  3_extremes         expansion > one folder per extreme trial
  4_other-content    fights missing from the catalog (created automatically)

Naming convention: lowercase, no spaces, words joined with "-", "_" before the name.
  - folder:  <order or code>_<fflogs-name>     e.g. 6_fru_futures-rewritten, m11s_the-tyrant
             the part after the last "_" is the fight's FFLogs name: keep it
  - files:   <anything>-p<n>.<ext>             image of phase n, e.g. fru-p3.png
             any other name                    image of the fight, e.g. tyrant.png
  - extensions: .png, .jpg, .jpeg, .webp

Which image is used:
  - ultimate: the -p<n> image of the current phase, otherwise default.jpg
    (add the phase images one by one as you reach them: no spoiler)
  - raid:     the -p<n> image of the current phase if any (last savage boss: -p1 and -p2),
    otherwise the fight image, otherwise default.jpg
  - default.jpg / default.png here, at the root, replaces the bundled kitten

Recommended size: 850 x 450 (or larger with the same ratio); otherwise it is center-cropped.
"""


def slug(text):
    """Name following the convention: lowercase ASCII words joined with "-"."""
    text = text.replace("æ", "ae").replace("Æ", "AE").replace("&", " and ")
    text = re.sub(r"['’]", "", text)                    # Dragonsong's -> dragonsongs
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-") or "unnamed"


def normalize(text):
    """Comparable form of a fight name: its slug without a leading "the"."""
    return re.sub(r"^the-", "", slug(text))


def category_of(zone_name):
    """Catalog category matching an FFLogs zone name."""
    zone_name = zone_name.lower()
    if "ultimate" in zone_name:
        return catalog.ULTIMATES
    if "savage" in zone_name:
        return catalog.SAVAGE
    if "extreme" in zone_name or "trial" in zone_name:
        return catalog.EXTREMES
    return None


def find_fight_folder(root, fight_name, category=None):
    """Folder of a fight. Ranking: same name before name contained in the folder name, right
    category first, fight folders before tier folders, then the shortest name."""
    root = Path(root)
    wanted = normalize(fight_name)
    if not root.is_dir() or not wanted:
        return None
    best = None
    for folder in root.rglob("*"):
        if not folder.is_dir():
            continue
        key = normalize(folder.name.rsplit("_", 1)[-1])
        if key == wanted:
            score = 0
        elif len(wanted) >= 4 and f"-{wanted}-" in f"-{key}-":
            score = 2
        else:
            continue
        if category and folder.relative_to(root).parts[0] != category:
            score += 10
        if any(child.is_dir() for child in folder.iterdir()):
            score += 1                           # a tier folder (it contains fights)
        candidate = (score, len(folder.name), str(folder))
        if best is None or candidate < best[0]:
            best = (candidate, folder)
    return best[1] if best else None


def phase_of(path):
    match = PHASE_PATTERN.search(path.stem)
    return int(match.group(1)) if match else None


def background_path(fight_name, zone_name, phase, ultimate, user_root, bundled_root):
    """Image to use: see the module docstring. The user's images win over the bundled ones."""
    category = catalog.ULTIMATES if ultimate else category_of(zone_name)
    for root in (Path(user_root), Path(bundled_root)):
        folder = find_fight_folder(root, fight_name, category)
        if not folder:
            continue
        images = sorted(p for p in folder.iterdir()
                        if p.is_file() and p.suffix.lower() in EXTENSIONS)
        phase_images = [p for p in images if phase and phase_of(p) == phase]
        fight_images = [] if ultimate else [p for p in images if phase_of(p) is None]
        if phase_images or fight_images:
            return (phase_images or fight_images)[0]
    for root in (Path(user_root), Path(bundled_root)):
        for extension in EXTENSIONS:
            if (Path(root) / f"default{extension}").is_file():
                return Path(root) / f"default{extension}"
    return None


def load_background(fight_name, zone_name, phase, ultimate, user_root, bundled_root):
    path = background_path(fight_name, zone_name, phase, ultimate, user_root, bundled_root)
    if path:
        try:
            return Image.open(path).convert("RGB"), path
        except Exception as e:
            log.warning("Unreadable image %s: %s", path, e)
    return None, None


def create_folders(root):
    """Creates the catalog folders and readme.txt; never deletes or renames anything."""
    root = Path(root)
    for relative in catalog.folders():
        (root / relative).mkdir(parents=True, exist_ok=True)
    readme = root / "readme.txt"
    if not readme.exists() or readme.read_text(encoding="utf-8") != README_TEXT:
        readme.write_text(README_TEXT, encoding="utf-8")


def ensure_fight_folder(root, zone_name, fight_name):
    """Creates <other-content>/<zone>/<fight> for a fight that has no folder yet."""
    if not find_fight_folder(root, fight_name, category_of(zone_name)):
        (Path(root) / catalog.OTHER / slug(zone_name) / slug(fight_name)).mkdir(
            parents=True, exist_ok=True)
