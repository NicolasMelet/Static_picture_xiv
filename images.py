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
README_NAME = "LISEZ-MOI.txt"
# « Phase 2 », « Phase 2 - Nidhogg », « P2 » ; mais pas « P4S - Hesperos » (code de raid).
PHASE_RX = re.compile(r"^(phase|p)\s*0*(\d+)(?![0-9a-z])", re.IGNORECASE)
CODE_RX = re.compile(r"^[^-]{1,14}?\s-\s")       # « M1S - », « P4S (1) - », « EX3 - »


def folder_name(name):
    """Nom de dossier valide sous Windows."""
    name = re.sub(r'[<>:"/\\|?*]', "-", name).strip().rstrip(".")
    return name or "Sans nom"


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
            log.warning("Image illisible %s : %s", path, e)
    return None, None


# --- Création de l'arborescence -------------------------------------------------

README_TEXT = """Images de fond de Prog FFLogs
==============================

  1 - Ultimates          un dossier par ultime, un sous-dossier par phase
  2 - Raids sadiques     extension > palier > un dossier par boss
  3 - Extrêmes           extension > un dossier par défi extrême
  4 - Autres contenus    combats absents du catalogue (créés automatiquement)

Déposez une image (.png, .jpg, .jpeg ou .webp, n'importe quel nom) dans le dossier du combat.
Le programme prend la plus précise disponible :

  1. le dossier de la phase en cours  (ex. « Phase 3 - Oracle of Darkness »)
  2. le dossier du combat             (ex. « M12S - Lindwurm »)
  3. les dossiers au-dessus           (palier, extension, catégorie : image commune)
  4. default.jpg / default.png ici, à la racine (sinon le chaton fourni avec le programme)

Une seule image dans le dossier d'un ultime suffit donc pour toutes ses phases.

Règles de nommage :
  - Dossier d'un combat : « CODE - Nom FFLogs ». Gardez le nom anglais après « - » : c'est lui
    qui identifie le combat. Le code devant (M12S, P4S (1), EX3...) est libre.
  - Dossier d'une phase : commence par « Phase N ». La suite est libre.
  - Vous pouvez créer d'autres dossiers ou phases : ils seront pris en compte.
  - S'il y a plusieurs images dans un dossier, la première par ordre alphabétique est utilisée.

Taille conseillée : 800 x 300 (ou plus grand, même proportion) ; sinon recadrage au centre.
"""


def create_skeleton(base):
    """Crée les dossiers du catalogue et le LISEZ-MOI (n'efface ni ne renomme rien)."""
    base = Path(base)
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
