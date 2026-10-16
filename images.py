"""Images de fond, stockées en local : aucune image n'est téléchargée depuis FFLogs.

Ordre de recherche, du plus prioritaire au moins prioritaire :
  1. vos images, dans le dossier `images` des réglages : `<boss>-p<phase>.png`, puis `<boss>.png`
     (<boss> = ID FFLogs du combat, ex. `1079-p3.png` pour la phase 3 de FRU) ;
  2. les mêmes noms dans les images fournies avec le programme ;
  3. `default.png` (la vôtre, sinon celle fournie avec le programme).
Extensions acceptées : .png, .jpg, .jpeg, .webp.
"""
import logging
from pathlib import Path

from PIL import Image

log = logging.getLogger("prog")
EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")


def _find(directory, name):
    for ext in EXTENSIONS:
        path = Path(directory) / f"{name}{ext}"
        if path.is_file():
            return path
    return None


def background_path(encounter_id, phase, user_dir, bundled_dir):
    names = ([f"{encounter_id}-p{phase}"] if phase else []) + [str(encounter_id)]
    for directory in (user_dir, bundled_dir):
        for name in names:
            path = _find(directory, name)
            if path:
                return path
    return _find(user_dir, "default") or _find(bundled_dir, "default")


def load_background(encounter_id, phase, user_dir, bundled_dir):
    path = background_path(encounter_id, phase, user_dir, bundled_dir)
    if path:
        try:
            return Image.open(path).convert("RGB"), path
        except Exception as e:
            log.warning("Image illisible %s : %s", path, e)
    return None, None
