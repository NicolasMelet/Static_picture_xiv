"""Background images, stored locally in folders: nothing is downloaded from FFLogs.

A fight's folder is found by its FFLogs name ("M12S - Lindwurm" for Lindwurm), wherever it is.
The most specific image wins:
  current phase folder -> fight folder -> parent folders (tier, expansion, category)
  -> default.jpg / default.png at the root.
Any file name works (.png, .jpg, .jpeg, .webp); with several images in a folder, the first one
in alphabetical order is used.
"""
import logging
import re
import unicodedata
from pathlib import Path

from PIL import Image

import catalog

log = logging.getLogger("prog")
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
# "Phase 2", "Phase 2 - Nidhogg", "P2"; but not "P4S - Hesperos" (a raid code).
PHASE_PATTERN = re.compile(r"^(phase|p)\s*0*(\d+)(?![0-9a-z])", re.IGNORECASE)
# Sorting/display code in front of a fight name: "M1S - ", "P4S (1) - ", "EX3 - ", "6. FRU - ".
CODE_PATTERN = re.compile(r"^[^-]{1,14}?\s-\s")

README_TEXT = """Prog FFLogs - background images
==============================

  1 - Ultimates        one folder per ultimate, one sub-folder per phase
  2 - Savage Raids     expansion > tier > one folder per boss
  3 - Extremes         expansion > one folder per extreme trial
  4 - Other Content    fights missing from the catalog (created automatically)

Drop an image (.png, .jpg, .jpeg or .webp, any file name) into the fight's folder.
The program uses the most specific one available:

  1. the current phase folder   (e.g. "Phase 3 - Oracle of Darkness")
  2. the fight folder           (e.g. "M12S - Lindwurm")
  3. the folders above it       (tier, expansion, category: shared image)
  4. default.jpg / default.png here, at the root (otherwise the bundled kitten)

A single image in an ultimate's folder is therefore enough for all of its phases.

Naming rules:
  - Fight folder: "CODE - FFLogs name". Keep the English name after " - ": it identifies the
    fight. The code in front (M12S, P4S (1), EX3...) and the numbers are only for sorting.
  - Phase folder: starts with "Phase N" (or "PN"). The rest is free.
  - You can add other folders or phases: they will be picked up.
  - If a folder holds several images, the first one in alphabetical order is used.

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


def images_in(folder):
    if not folder or not folder.is_dir():
        return []
    return sorted(p for p in folder.iterdir() if p.is_file() and p.suffix.lower() in EXTENSIONS)


def is_phase_folder(folder):
    return bool(PHASE_PATTERN.match(folder.name))


def find_fight_folder(root, fight_name, category=None):
    """Folder of a fight. Ranking: same name before name contained in the folder name, right
    category first, fight folders before tier folders, then the shortest name."""
    root = Path(root)
    wanted = normalize(fight_name)
    if not root.is_dir() or not wanted:
        return None
    best = None
    for folder in root.rglob("*"):
        if not folder.is_dir() or is_phase_folder(folder):
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
        if any(child.is_dir() and not is_phase_folder(child) for child in folder.iterdir()):
            score += 1                           # a tier folder (it contains fights)
        candidate = (score, len(folder.name), str(folder))
        if best is None or candidate < best[0]:
            best = (candidate, folder)
    return best[1] if best else None


def phase_folder(fight_folder, phase):
    if not phase or not fight_folder:
        return None
    for folder in sorted(fight_folder.iterdir()):
        match = PHASE_PATTERN.match(folder.name)
        if folder.is_dir() and match and int(match.group(2)) == phase:
            return folder
    return None


def background_path(fight_name, zone_name, phase, user_root, bundled_root):
    """Most specific image for the fight and phase: the user's images first, then the bundled
    ones, then default.*."""
    category = category_of(zone_name)
    for root in (Path(user_root), Path(bundled_root)):
        fight_folder = find_fight_folder(root, fight_name, category)
        if not fight_folder:
            continue
        candidates = [phase_folder(fight_folder, phase), fight_folder]
        candidates += [p for p in fight_folder.parents if root in p.parents]
        for folder in candidates:
            found = images_in(folder)
            if found:
                return found[0]
    for root in (Path(user_root), Path(bundled_root)):
        found = [p for p in images_in(root) if p.stem.lower() == "default"]
        if found:
            return found[0]
    return None


def load_background(fight_name, zone_name, phase, user_root, bundled_root):
    path = background_path(fight_name, zone_name, phase, user_root, bundled_root)
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


def ensure_fight_folder(root, zone_name, fight_name, phase_names=()):
    """Creates a folder in "4 - Other Content" for a fight that has none yet."""
    if find_fight_folder(root, fight_name, category_of(zone_name)):
        return None
    folder = Path(root) / catalog.OTHER / folder_name(zone_name) / folder_name(fight_name)
    folder.mkdir(parents=True, exist_ok=True)
    if len(phase_names) >= 2:
        for number, name in enumerate(phase_names, start=1):
            generic = re.fullmatch(r"(P|Phase)\s*\d+", name or "", re.IGNORECASE)
            label = f"Phase {number}" if generic else f"Phase {number} - {name}"
            (folder / folder_name(label)).mkdir(exist_ok=True)
    return folder
