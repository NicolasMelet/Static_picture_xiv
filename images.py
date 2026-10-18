"""Background images, stored locally in one folder per fight: nothing is downloaded from FFLogs.

A fight's folder is found by its FFLogs name ("M12S - Lindwurm" for Lindwurm), wherever it is.
Inside it:
  - "Phase N.png" (or "P N", "phase3"...) is the image of phase N;
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
# "Phase 2", "phase2", "P2", "Phase 2 - Nidhogg"; but not "P4S - Hesperos" (a raid code).
PHASE_PATTERN = re.compile(r"^(phase|p)\s*0*(\d+)(?![0-9a-z])", re.IGNORECASE)
# Display code in front of a fight name: "M1S - ", "P4S (1) - ", "EX3 - ", "6. FRU - ".
CODE_PATTERN = re.compile(r"^[^-]{1,14}?\s-\s")

README_TEXT = """Prog FFLogs - background images
==============================

  1 - Ultimates        one folder per ultimate
  2 - Savage Raids     expansion > tier > one folder per boss
  3 - Extremes         expansion > one folder per extreme trial
  4 - Other Content    fights missing from the catalog (created automatically)

Put the images (.png, .jpg, .jpeg or .webp) in the fight's folder:

  Phase 3.png    image of phase 3 ("Phase 3", "P3" or "phase3", any extension)
  anything.png   image of the fight (used when there is no image for the current phase)

  - Ultimate: only phase images are used. A phase without its own image shows default.jpg,
    so you can add the phases one by one as you reach them.
  - Raid: the phase image if there is one (e.g. M12S phase 2), otherwise the fight image.
  - No image found: default.jpg / default.png here, at the root (otherwise the bundled kitten).

Folder names: "CODE - FFLogs name". Keep the English name after " - ": it identifies the fight.
The code in front (M12S, P4S (1), EX3...) and the numbers are only for sorting.
Recommended size: 850 x 450 (or larger with the same ratio); otherwise it is center-cropped.
"""


def folder_name(name):
    """Folder name that is valid on Windows."""
    name = re.sub(r'[<>:"/\\|?*]', "-", name).strip().rstrip(".")
    return name or "Unnamed"


def normalize(text):
    """Comparable form of a name: lowercase ASCII words, no leading "the"."""
    text = text.replace("æ", "ae").replace("Æ", "AE").replace("&", " and ")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return re.sub(r"^the ", "", text)


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
        key = normalize(CODE_PATTERN.sub("", folder.name, count=1))
        if key == wanted:
            score = 0
        elif len(wanted) >= 4 and re.search(rf"\b{re.escape(wanted)}\b", key):
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
    match = PHASE_PATTERN.match(path.stem)
    return int(match.group(2)) if match else None


def background_path(fight_name, zone_name, phase, ultimate, user_root, bundled_root):
    """Image to use: see the module docstring. The user's images win over the bundled ones."""
    category = category_of(zone_name)
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
    """Creates the catalog folders and README.txt; never deletes or renames anything."""
    root = Path(root)
    for relative in catalog.folders():
        (root / Path(*[folder_name(part) for part in relative.split("/")])).mkdir(
            parents=True, exist_ok=True)
    readme = root / "README.txt"
    if not readme.exists() or readme.read_text(encoding="utf-8") != README_TEXT:
        readme.write_text(README_TEXT, encoding="utf-8")


def ensure_fight_folder(root, zone_name, fight_name):
    """Creates a folder in "4 - Other Content" for a fight that has none yet."""
    if not find_fight_folder(root, fight_name, category_of(zone_name)):
        (Path(root) / catalog.OTHER / folder_name(zone_name) / folder_name(fight_name)).mkdir(
            parents=True, exist_ok=True)
