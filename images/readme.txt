prog fflogs - background images
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
