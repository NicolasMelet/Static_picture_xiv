Prog FFLogs - background images
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
