# Prog FFLogs → fixed-link image

A small Windows program that watches the logs the **Archon** app uploads to FFLogs, computes the
static's progression (best % and bosses/phases cleared) and publishes a PNG image on
**GitHub Pages**, for free, at an address that never changes:

```
https://nicolasmelet.github.io/Static_picture_xiv/prog.png
```

## How it works

1. When Windows starts, `ProgFFLogs.exe` runs in the background (orange icon in the taskbar).
2. Every 5 minutes while Archon (or ACT) is open, it asks the FFLogs API for the static's reports
   on the selected content, then one last time when they close. While neither Archon nor ACT is
   running, FFLogs is never queried (only the Windows process list is checked every 30 s). The
   **Update now** menu item and changing the content query FFLogs immediately.
3. When there is a new report (or a live report has grown), it downloads the fights, computes the
   progression and renders the image (850 × 450, the size of the background images):
   - in the background, your image for the current boss or phase (see "Background images");
   - top left, the name of the current boss (raid) or of the ultimate;
   - bottom left, in large type, the best percentage reached on the current boss / phase, then
     the current phase (ultimates, and the last savage boss) and the number of pulls (on the
     current boss for a raid, in total for an ultimate);
   - bottom right, for a raid: the progression `X/Y`. In savage, the last fight has two phases
     and counts twice: a 4-fight Arcadion tier is counted out of 5, and reaching phase 2 of the
     last boss is worth one point. Pandaemonium tiers, where FFLogs already splits the last boss
     into two fights, are also counted out of 5;
   - bottom right, for an ultimate: `Pulls:` then the pull on which each phase was cleared for
     the first time (e.g. `P1: 156`, `P2: 824`).
4. If the progression changed, the image is pushed to the repository's `gh-pages` branch (at most
   once every 10 minutes, see below). GitHub Pages serves it at the same address.

The icon menu lets you **change the content** (e.g. *AAC Heavyweight*), force an update and open
the image.

## Installation

### 1. GitHub repository (hosting)

1. The code lives in the public repository `NicolasMelet/Static_picture_xiv`.
2. Create a token: *Settings → Developer settings → Fine-grained tokens* → access to the
   `Static_picture_xiv` repository only, permission **Contents: Read and write**. Pick a distant
   expiration date: once it expires, publishing fails (see the log).
3. The `gh-pages` branch already exists: it only holds the site (`prog.png`, an `index.html`
   page that shows the image, and `.nojekyll` for faster deployments).
4. In the repository: *Settings → Pages → Source: Deploy from a branch → `gh-pages` / `(root)`*.

### 2. FFLogs API access

On <https://www.fflogs.com/api/clients/>, create a client (any name, redirect URL
`http://localhost`) and write down the *Client ID* and *Client Secret*.

### 3. On the Windows PC

1. Download `ProgFFLogs.exe` from the latest
   [release](https://github.com/NicolasMelet/Static_picture_xiv/releases/latest) and put it
   wherever you like (e.g. `Documents\ProgFFLogs`). Python is not required.
2. Run it. Windows SmartScreen may show "Windows protected your PC" because the executable is not
   signed: *More info → Run anyway*.
3. On first launch, it creates two files in `%APPDATA%\ProgFFLogs` and opens them in Notepad.
   Fill them in, then start `ProgFFLogs.exe` again.

**`.env`: the secret keys.** It stays on your PC (`%APPDATA%\ProgFFLogs`): it is never in the
GitHub repository, which only holds the empty template `.env.example`.

| Key | Value |
|---|---|
| `FFLOGS_CLIENT_ID` / `FFLOGS_CLIENT_SECRET` | Step 2 |
| `GITHUB_TOKEN` | Step 1 |

**`config.json`: the settings** (the program edits it when you change the content):

| Key | Value |
|---|---|
| `zone_id` | Tracked content (can be changed later from the icon) |
| `encounter_id` | Fight chosen inside a multi-fight zone (legacy ultimates, extremes), otherwise `null` |
| `difficulty` | `101` = Savage, `100` = Normal, `null` = all (ignored for ultimates) |
| `fflogs.static_id` | Wipe Lotus static ID: `141085` (the number in <https://fr.fflogs.com/guild/id/141085>), already filled in |
| `fflogs.raid_team_id` | Optional: only track one raid team of the static, `null` = the whole static |
| `github.repo` | `NicolasMelet/Static_picture_xiv` |
| `github.min_publish_seconds` | Minimum delay between two publications (default 600 s) |
| `autostart` | `true`: registers itself to start with Windows on first launch |
| `poll.*` | Archon/ACT process names, FFLogs query interval (300 s) and process check interval (30 s) |

To find the IDs (the static's raid teams, every `zone_id` and `encounter_id`): icon menu →
**Find IDs (static, contents)**, or `ProgFFLogs.exe --setup`. The result opens in Notepad.

The icon menu also toggles **Start with Windows** and has **Open settings folder**, which holds
the log file `prog_tracker.log`.

Manual test (renders and publishes once): `ProgFFLogs.exe --once`.

### Background images

No image is downloaded from FFLogs: the backgrounds are your own images, stored in
`%APPDATA%\ProgFFLogs\images` (icon menu → **Open images folder**). The whole folder tree is created when the program starts; it is also visible in the
repository's [`images/`](images) folder.

```
images/
  default.jpg                                   content without an image (the kitten)
  README.txt                                    reminder of the rules below
  1 - Ultimates/
    1. UCOB - The Unending Coil of Bahamut/
      Phase 1 - Twintania/ ... Phase 5 - Golden Bahamut/
    2. UWU ... 7. DMU - Dancing Mad/            one folder per ultimate, one per phase
  2 - Savage Raids/
    2 - Heavensward/ ... 6 - Dawntrail/         expansion
      3 - AAC Heavyweight/                      tier
        M9S - Vamp Fatale/                      one folder per boss
        M12S - Lindwurm/
          Phase 1/  Phase 2/                    last Arcadion boss: two phases
  3 - Extremes/
    1 - A Realm Reborn/ ... 6 - Dawntrail/
      EX1 - Valigarmanda/                       one folder per extreme trial
  4 - Other Content/                            fights missing from the catalog (automatic)
```

Drop an image (any name, `.png`, `.jpg`, `.jpeg`, `.webp`) into the fight's or phase's folder.
The program uses the most specific one available:
**phase → fight → tier / expansion / category → default**. A single image in an ultimate's
folder is therefore enough for all of its phases, and an image in a tier folder is used for all
of its bosses.

- **Naming**: a fight folder is named "CODE - FFLogs name". The English name after " - "
  identifies the fight: keep it. The code and numbers in front are only there for sorting. A
  phase folder starts with `Phase N` (or `PN`); the rest is free.
- **Unknown fight**: if a fight has no folder (content released after this version, different
  FFLogs name), the program creates one in `4 - Other Content` the first time it is tracked.
- **Additions**: you can create other folders or phases, they are picked up. Existing folders are
  never deleted or renamed.
- **Recommended size**: 850 × 450 or larger with the same ratio (center-cropped otherwise).
- **Bundled images**: images placed in the repository's `images/` folder are built into the
  executable and are used when you have none for that fight.

Fight and phase names come from the game and FFLogs; some of them (especially ultimate phases and
older tiers) could not be checked against FFLogs. If an image is not picked up, the log shows the
background used ("Background: ..."): rename the folder after the fight name as shown by
**Find IDs**.

**Legacy ultimates and extremes**: FFLogs groups several fights in a single zone. In the
**Content** menu, these zones open a sub-menu to choose the tracked fight
(`encounter_id` in `config.json`).

### Publishing a new version of the executable

The `.github/workflows/build.yml` workflow builds the executable on a GitHub Actions Windows
machine and tests it on every push to `main` (downloadable from the *Actions* tab). To publish a
release:

```bash
git tag v1.2.0
git push origin v1.2.0
```

### Development (without the executable)

```powershell
py -m venv .venv
.venv\Scripts\pip install -r requirements.txt
.venv\Scripts\python prog_tracker.py --once
```

In development, `.env`, `config.json` and the log sit next to the script (ignored by git).

## Good to know

- **Private logs**: the API in "client" mode cannot see *private* reports. Public reports are
  included; *unlisted* reports are read when FFLogs includes them in the static's report list.
- **Uninstall**: untick **Start with Windows**, **Quit**, then delete `ProgFFLogs.exe` and
  the `%APPDATA%\ProgFFLogs` folder.

## GitHub Pages: what to know

GitHub Pages serves the files of a repository branch as a static website, for free. Here, the
`gh-pages` branch holds `prog.png`, served at
`https://nicolasmelet.github.io/Static_picture_xiv/prog.png`. Every time the program replaces the
image (a commit on `gh-pages`), GitHub redeploys the site.

- **Deployment delay**: usually under a minute (repository *Actions* tab, "pages build and
  deployment").
- **Cache**: GitHub's CDN caches the image for up to ~10 minutes. Discord also keeps images it
  has already shown for a long time; adding a parameter to the link (`prog.png?v=2`) forces a
  reload.
- **Deployment limit**: GitHub recommends at most ~10 deployments per hour. The program therefore
  publishes at most once every 10 minutes; a pending image is published as soon as the delay has
  passed (without querying FFLogs again).
- **Everything is public**: with a free account, Pages requires a public repository. The code and
  the image are visible to everyone; the keys stay in `.env` on your PC.
- **History**: each update adds a commit on `gh-pages` (a few dozen KB). Irrelevant at the scale
  of a tier, the size limit of a Pages site being 1 GB.
- **The `gh-pages` branch** is independent from `main`: it only holds the site, the code stays on
  `main`. The program only replaces `prog.png` there. The page
  <https://nicolasmelet.github.io/Static_picture_xiv/> shows the image and reloads it every
  5 minutes.
