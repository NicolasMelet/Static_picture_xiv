"""Background images: one folder per fight or per phase, one image per folder.

A fight's folder is the one whose name ends with the fight's FFLogs name ("m11s_the-tyrant"
for The Tyrant), wherever it is under the images folder. A fight with phases (every ultimate,
M8S) has one subfolder per phase inside its folder: p1, p2, ...
The first image found in the folder is used, otherwise default.jpg at the root.
"""
import re
import unicodedata
from pathlib import Path

import catalog

EXTENSIONS = (".png", ".jpg", ".jpeg", ".webp")

README_TEXT = """prog fflogs - background images
==============================

  1_ultimates        one folder per ultimate
  2_savage-raids     expansion > tier > one folder per boss
  3_extremes         expansion > one folder per extreme trial
  4_other-content    fights missing from the catalog (created automatically)

One folder = one image. Put a single image (.png, .jpg, .jpeg, .webp, any name) in:
  - the fight's folder                      e.g. m11s_the-tyrant/tyrant.png
  - or, for a fight with phases, the phase's subfolder p1, p2, ... of the fight's folder
                                            e.g. 6_fru_futures-rewritten/p3/oracle.png

Fights with phases: every ultimate, and a savage boss recorded by FFLogs as one fight with
two phases (m8s_howling-blade/p1 and p2). M12S is two FFLogs fights, so it has two folders:
m12s-1_lindwurm (phase 1) and m12s-2_lindwurm-ii (phase 2).

The folder of the current fight or phase is created on update when it does not exist yet;
you can also create p1, p2, ... yourself beforehand. The end of a fight folder's name (after
the last "_") is the fight's FFLogs name: keep it.

No image in the folder: default.jpg (or default.png) of this folder is used, otherwise the
bundled kitten.

Recommended size: 850 x 450 (or larger with the same ratio); otherwise it is center-cropped.
"""


def slug(text):
    """Folder name of a fight: lowercase ASCII words joined with "-"."""
    text = text.replace("æ", "ae").replace("Æ", "AE").replace("&", " and ")
    text = re.sub(r"['’]", "", text)                    # Dragonsong's -> dragonsongs
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", text).strip("-")


def fight_folder(root, fight_name, phase=None):
    """Folder of a fight, or of one of its phases (subfolder p<n>); created if missing."""
    wanted = slug(fight_name).removeprefix("the-")
    folder = next(
        (f for f in sorted(Path(root).rglob("*"))
         if f.is_dir() and slug(f.name.rsplit("_", 1)[-1]).removeprefix("the-") == wanted),
        Path(root) / catalog.OTHER / slug(fight_name))
    if phase:
        folder = folder / f"p{phase}"
    folder.mkdir(parents=True, exist_ok=True)
    return folder


def background(folder, *default_roots):
    """First image of the folder, otherwise the first default image of the given roots."""
    candidates = sorted(folder.iterdir())
    for root in default_roots:
        candidates += sorted(Path(root).glob("default.*"))
    return next(path for path in candidates if path.suffix.lower() in EXTENSIONS)


def create_folders(root):
    """Creates the catalog folders and readme.txt; never deletes or renames anything."""
    root = Path(root)
    for relative in catalog.folders():
        (root / relative).mkdir(parents=True, exist_ok=True)
    (root / "readme.txt").write_text(README_TEXT, encoding="utf-8")
