"""Images de fond rangées par dossiers : aucune image n'est téléchargée depuis FFLogs.

    images/
      default.jpg                         contenu sans image
      AAC Heavyweight (Savage)/           un dossier par contenu (créés par le programme)
        fond.jpg                          image commune à tout le contenu (facultatif)
        1 - Vamp Fatale/                  un dossier par boss, numéroté dans l'ordre
        ...
        4 - Lindwurm/
          Phase 1/                        un dossier par phase quand le combat en a plusieurs
          Phase 2/
      Futures Rewritten (Ultimate)/
        Phase 1 - Fatebreaker/            ultime : directement un dossier par phase
        ...

Il suffit de déposer une image (n'importe quel nom) dans le bon dossier. Le programme prend la
plus précise disponible : phase, puis boss, puis contenu, puis default. Seul le début des noms
compte (« 4 - », « Phase 2 ») : le reste peut être renommé librement.
"""
import logging
import re
from pathlib import Path

from PIL import Image

log = logging.getLogger("prog")
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")
README_NAME = "LISEZ-MOI.txt"


def folder_name(name):
    """Nom de dossier valide sous Windows."""
    name = re.sub(r'[<>:"/\\|?*]', "-", name).strip().rstrip(".")
    return name or "Sans nom"


def _images_in(directory):
    if not directory or not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir()
                  if p.is_file() and p.suffix.lower() in EXTENSIONS)


def _child(directory, pattern):
    """Sous-dossier dont le nom commence par le motif (insensible à la casse)."""
    if not directory or not directory.is_dir():
        return None
    rx = re.compile(pattern, re.IGNORECASE)
    for p in sorted(directory.iterdir()):
        if p.is_dir() and rx.match(p.name):
            return p
    return None


def _content_dir(base, content):
    wanted = folder_name(content).lower()
    if base.is_dir():
        for p in base.iterdir():
            if p.is_dir() and p.name.lower() == wanted:
                return p
    return None


def _phase_dir(directory, phase):
    return _child(directory, rf"(phase|p)\s*0*{phase}(\D|$)") if phase else None


def background_path(content, boss_index, phase, user_dir, bundled_dir):
    """content : nom du contenu ; boss_index : n° du boss (raid) ou None (ultime) ; phase : n°."""
    for base in (Path(user_dir), Path(bundled_dir)):
        cdir = _content_dir(base, content) if content else None
        if not cdir:
            continue
        bdir = _child(cdir, rf"0*{boss_index}(\D|$)") if boss_index else None
        candidates = [_phase_dir(bdir, phase), bdir] if bdir else [_phase_dir(cdir, phase)]
        candidates.append(cdir)
        for directory in candidates:
            found = _images_in(directory)
            if found:
                return found[0]
    for base in (Path(user_dir), Path(bundled_dir)):
        found = [p for p in _images_in(base) if p.stem.lower() == "default"]
        if found:
            return found[0]
    return None


def load_background(content, boss_index, phase, user_dir, bundled_dir):
    path = background_path(content, boss_index, phase, user_dir, bundled_dir)
    if path:
        try:
            return Image.open(path).convert("RGB"), path
        except Exception as e:
            log.warning("Image illisible %s : %s", path, e)
    return None, None


# --- Création de l'arborescence -------------------------------------------------

README_TEXT = """Images de fond de Prog FFLogs
==============================

Déposez une image (.png, .jpg, .jpeg ou .webp, n'importe quel nom) dans le dossier qui
correspond au combat. Le programme choisit la plus précise disponible :

  1. le dossier de la phase en cours (« Phase 2 »...)
  2. le dossier du boss en cours (« 4 - Lindwurm »...)
  3. le dossier du contenu (image commune à tout le contenu)
  4. default.png / default.jpg, à la racine de ce dossier (sinon le chaton fourni)

Les dossiers sont créés automatiquement. Ne renommez pas les dossiers de contenu ; pour les
boss et les phases, seul le début compte (« 4 - », « Phase 2 »).
S'il y a plusieurs images dans un dossier, la première par ordre alphabétique est utilisée.
Taille conseillée : 800 x 300 (ou plus grand, même proportion), recadrée au centre sinon.
"""


def create_tree(base, content, bosses=None, phases=None):
    """
    bosses : [(numéro, nom, [noms de phases])] pour un raid
    phases : [noms de phases] pour un ultime
    Ne supprime ni ne renomme rien : ajoute seulement les dossiers manquants.
    """
    base = Path(base)
    base.mkdir(parents=True, exist_ok=True)
    readme = base / README_NAME
    if not readme.exists():
        readme.write_text(README_TEXT, encoding="utf-8")
    cdir = _content_dir(base, content) or base / folder_name(content)
    cdir.mkdir(exist_ok=True)
    for number, name, boss_phases in bosses or []:
        bdir = _child(cdir, rf"0*{number}(\D|$)") or cdir / folder_name(f"{number} - {name}")
        bdir.mkdir(exist_ok=True)
        _create_phases(bdir, boss_phases)
    _create_phases(cdir, phases)
    return cdir


def _create_phases(directory, names):
    if not names or len(names) < 2:
        return
    for i, name in enumerate(names, start=1):
        if _phase_dir(directory, i):
            continue
        label = f"Phase {i}" if not name or re.fullmatch(r"(P|Phase)\s*\d+", name, re.I) \
            else f"Phase {i} - {name}"
        (directory / folder_name(label)).mkdir(exist_ok=True)
