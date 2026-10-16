"""Images de fond rangées par dossiers : aucune image n'est téléchargée depuis FFLogs.

Le dossier d'un combat est retrouvé par son nom FFLogs (« M12S - Lindwurm » pour Lindwurm),
où qu'il soit rangé. L'image utilisée est la plus précise disponible :
  dossier de la phase en cours → dossier du combat → dossiers parents (palier, extension,
  catégorie) → default.jpg / default.png à la racine.
Dans un dossier, n'importe quel nom de fichier convient (.png, .jpg, .jpeg, .webp) ; s'il y en a
plusieurs, le premier par ordre alphabétique est utilisé.
"""
import logging
import re
import unicodedata
from pathlib import Path

from PIL import Image

import catalog

log = logging.getLogger("prog")
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
README_NAME = "README.txt"
OLD_README_NAME = "LISEZ-MOI.txt"          # v1.1.0
# « Phase 2 », « Phase 2 - Nidhogg », « P2 » ; mais pas « P4S - Hesperos » (code de raid).
PHASE_RX = re.compile(r"^(phase|p)\s*0*(\d+)(?![0-9a-z])", re.IGNORECASE)
CODE_RX = re.compile(r"^[^-]{1,14}?\s-\s")       # « M1S - », « P4S (1) - », « EX3 - »


def folder_name(name):
    """Nom de dossier valide sous Windows."""
    name = re.sub(r'[<>:"/\\|?*]', "-", name).strip().rstrip(".")
    return name or "Unnamed"


def normalize(text):
    text = text.replace("æ", "ae").replace("Æ", "AE").replace("&", " and ")
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    text = re.sub(r"[^a-z0-9]+", " ", text).strip()
    return re.sub(r"^the ", "", text)


def _fight_key(directory_name):
    return normalize(CODE_RX.sub("", directory_name, count=1))


def _images_in(directory):
    if not directory or not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir()
                  if p.is_file() and p.suffix.lower() in EXTENSIONS)


def category_of(zone_name):
    """Catégorie du catalogue d'après le nom de la zone FFLogs."""
    z = zone_name.lower()
    if "ultimate" in z:
        return catalog.ULTIMATES
    if "savage" in z:
        return catalog.SAVAGE
    if "extreme" in z or "trial" in z:
        return catalog.EXTREME
    return None


def find_fight_dir(base, fight_name, category=None):
    """Dossier du combat : nom identique en priorité, puis nom contenu ; la catégorie départage."""
    base = Path(base)
    if not base.is_dir():
        return None
    wanted = normalize(fight_name)
    if not wanted:
        return None
    best = None
    for d in base.rglob("*"):
        if not d.is_dir() or PHASE_RX.match(d.name):
            continue
        key = _fight_key(d.name)
        if key == wanted:
            score = 0
        elif len(wanted) >= 4 and re.search(rf"\b{re.escape(wanted)}\b", key):
            score = 2
        else:
            continue
        rel = d.relative_to(base).parts
        if category and rel[0] != category:
            score += 10                          # la bonne catégorie passe avant tout
        if any(c.is_dir() and not PHASE_RX.match(c.name) for c in d.iterdir()):
            score += 1                           # dossier de palier (contient des combats)
        candidate = (score, len(d.name), str(d))
        if best is None or candidate < best[0]:
            best = (candidate, d)
    return best[1] if best else None


def _phase_dir(directory, phase):
    if not phase or not directory or not directory.is_dir():
        return None
    for d in sorted(directory.iterdir()):
        m = PHASE_RX.match(d.name)
        if d.is_dir() and m and int(m.group(2)) == phase:
            return d
    return None


def background_path(fight_name, zone_name, phase, user_dir, bundled_dir):
    category = category_of(zone_name or "")
    for base in (Path(user_dir), Path(bundled_dir)):
        fight_dir = find_fight_dir(base, fight_name, category)
        if not fight_dir:
            continue
        candidates = [_phase_dir(fight_dir, phase), fight_dir]
        parent = fight_dir.parent
        while parent != base and base in parent.parents:
            candidates.append(parent)
            parent = parent.parent
        for directory in candidates:
            found = _images_in(directory)
            if found:
                return found[0]
    for base in (Path(user_dir), Path(bundled_dir)):
        found = [p for p in _images_in(base) if p.stem.lower() == "default"]
        if found:
            return found[0]
    return None


def load_background(fight_name, zone_name, phase, user_dir, bundled_dir):
    path = background_path(fight_name, zone_name, phase, user_dir, bundled_dir)
    if path:
        try:
            return Image.open(path).convert("RGB"), path
        except Exception as e:
            log.warning("Unreadable image %s: %s", path, e)
    return None, None


# --- Création de l'arborescence -------------------------------------------------

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

Recommended size: 800 x 300 (or larger with the same ratio); otherwise it is center-cropped.
"""


def migrate(base):
    """Renomme les dossiers français de la v1.1.0 (images déjà rangées comprises)."""
    base = Path(base)
    if not base.is_dir():
        return
    for d in sorted(base.rglob("*"), key=lambda p: -len(p.parts)):   # les plus profonds d'abord
        new = catalog.RENAMED.get(d.name)
        if d.is_dir() and new and not (d.parent / new).exists():
            d.rename(d.parent / new)
    old_readme = base / OLD_README_NAME
    if old_readme.is_file():
        old_readme.unlink()


def create_skeleton(base):
    """Crée les dossiers du catalogue et le README.txt (n'efface ni ne renomme rien d'autre que
    les anciens noms français de la v1.1.0)."""
    base = Path(base)
    migrate(base)
    for rel in catalog.folders():
        (base / Path(*[folder_name(part) for part in rel.split("/")])).mkdir(
            parents=True, exist_ok=True)
    readme = base / README_NAME
    if not readme.exists() or readme.read_text(encoding="utf-8") != README_TEXT:
        readme.write_text(README_TEXT, encoding="utf-8")
    return base


def ensure_fight_dir(base, zone_name, fight_name, phase_names=()):
    """Si le combat n'a pas encore de dossier, le crée dans « 4 - Autres contenus »."""
    if find_fight_dir(base, fight_name, category_of(zone_name)):
        return None
    d = Path(base) / catalog.OTHER / folder_name(zone_name) / folder_name(fight_name)
    d.mkdir(parents=True, exist_ok=True)
    if len(phase_names) >= 2:
        for i, name in enumerate(phase_names, start=1):
            label = f"Phase {i}" if re.fullmatch(r"(P|Phase)\s*\d+", name or "", re.I) \
                else f"Phase {i} - {name}"
            (d / folder_name(label)).mkdir(exist_ok=True)
    return d
