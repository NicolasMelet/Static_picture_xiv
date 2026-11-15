prog fflogs - background images
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
