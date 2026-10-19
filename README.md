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
     the current phase (ultimates only) and the number of pulls (on the
     current boss for a raid, in total for an ultimate);
   - bottom right, for a raid: the progression `X/Y`. A savage tier is always counted out of 5,
     the last boss having two phases. How FFLogs records that last boss:
     - two separate fights (Pandaemonium, AAC Heavyweight: Lindwurm and Lindwurm II): each kill
       counts;
     - one fight with two phases (AAC Cruiserweight, M8S): reaching phase 2 counts, then the
       kill;
     - one fight without phase data (AAC Light-heavyweight, M4S): phase 2 cannot be detected,
       so the tier goes from 3/5 straight to 5/5 when M4S is killed;
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
| `poll.*` | FFLogs query interval while Archon/ACT runs (300 s) and process check interval (30 s) |

To find the IDs (the static's raid teams, every `zone_id` and `encounter_id`): icon menu →
**Find IDs (static, contents)**, or `ProgFFLogs.exe --setup`. The result opens in Notepad.

The icon menu also toggles **Start with Windows** and has **Open settings folder**, which holds
the log file `prog_tracker.log`.

Manual test (renders and publishes once): `ProgFFLogs.exe --once`.

### Logs and testing

The log is `%APPDATA%\ProgFFLogs\prog_tracker.log` (icon menu → **Open settings folder**). Open
it with Notepad and reopen it to see new lines.

- **Archon sync**: the log starts with `Prog FFLogs started` and `Watching for processes named
  like archon, ...`. Start Archon (or ACT): within 30 s the log shows
  `Archon/ACT detected (<process name>): FFLogs checked every 300 s`, then every 5 minutes either
  `No new log (N reports)` or `N reports (M new/updated)`. Close Archon: `Archon/ACT closed: last
  check` appears within 30 s, and no more FFLogs lines after that. A process counts when its name
  contains "archon", "advanced combat tracker" or "ff logs uploader" (Task Manager → Details
  shows the names).
- **Progression update**: upload a log with Archon on the tracked content (or pick a content that
  already has logs in the **Content** menu, which updates at once). The log then shows
  `N reports (1 new/updated)`, `Background: ...` and `Image published: ...` (or
  `Publication postponed by ... s` if an image was published less than 10 minutes ago). Check the
  result with **Open local image** and, after a minute, **Open online image**.

### Background images

No image is downloaded from FFLogs: the backgrounds are your own images, stored in
`%APPDATA%\ProgFFLogs\images` (icon menu → **Open images folder**), one folder per fight. The
folders are created when the program starts; they are also visible in the repository's
[`images/`](images) folder.

**Naming convention** (folders and files): lowercase, no spaces, no accents; words are joined
with `-`, and `_` separates the prefixes (order number, raid code) from the name.

| What | Pattern | Example |
|---|---|---|
| Category / expansion / tier | `<order>_<name>` | `2_savage-raids/6_dawntrail/3_aac-heavyweight` |
| Fight | `<order or code>_<fflogs-name>` | `6_fru_futures-rewritten`, `m8s_howling-blade`, `m12s-2_lindwurm-ii` |
| Phase image | `<anything>-p<n>.<ext>` | `fru-p3.png`, `howling-blade-p2.jpg` |
| Fight image | any other name | `vamp-fatale.png` |
| Default image | `default.<ext>` at the root | `default.jpg` |

The part after the last `_` of a fight folder is the fight's FFLogs name: it is what the program
looks for, keep it. Extensions: `.png`, `.jpg`, `.jpeg`, `.webp`.

```
images/
  default.jpg                          used when no image fits (the kitten)
  readme.txt                           reminder of these rules
  1_ultimates/
    6_fru_futures-rewritten/
      fatebreaker-p1.png
      usurper-p2.png                   add each phase image when you reach it
  2_savage-raids/
    6_dawntrail/2_aac-cruiserweight/
      m5s_dancing-green/
        dancing-green.png              image of the boss
      m8s_howling-blade/
        howling-blade-p1.png           last boss in two phases: one image per phase
        howling-blade-p2.png
  3_extremes/
    6_dawntrail/ex1_valigarmanda/
  4_other-content/                     fights missing from the catalog (created automatically)
```

**Example: savage (AAC Heavyweight)**, in `images/2_savage-raids/6_dawntrail/3_aac-heavyweight/`:

```
m9s_vamp-fatale/vamp-fatale.png            M9S
m10s_red-hot-and-deep-blue/red-hot.png     M10S
m11s_the-tyrant/tyrant.jpg                 M11S
m12s-1_lindwurm/lindwurm.png               M12S, first fight (Lindwurm)
m12s-2_lindwurm-ii/lindwurm-ii.png         M12S, second fight (Lindwurm II)
```

**Example: savage boss in two phases (M8S)**, in
`images/2_savage-raids/6_dawntrail/2_aac-cruiserweight/m8s_howling-blade/`:

```
howling-blade-p1.png      phase 1
howling-blade-p2.png      phase 2
```

**Example: ultimate (Futures Rewritten)**, in `images/1_ultimates/6_fru_futures-rewritten/`:

```
fatebreaker-p1.png        phase 1
usurper-of-frost-p2.png   phase 2
oracle-p3.png             phase 3   (added when the static reaches phase 3)
```

While the static is in phase 4 and there is no `-p4` image yet, the default image is shown.

Which image is used:

- **Ultimate**: the `-p<n>` image of the current phase, otherwise the default image. The number of
  phases of a new ultimate is never spoiled: add each phase image when you reach it.
- **Raid**: the fight image, otherwise the default image. Only a savage boss that FFLogs
  records as one fight with two phases (M8S, Howling Blade) also uses `-p1` and `-p2` images.
  M4S has no phase data on FFLogs and M12S is two separate fights, so they use plain images.
- **Missing folder**: a fight without a folder (content released after this version) gets one in
  `4_other-content/<zone>/<fight>` the first time it is tracked.
- **Recommended size**: 850 × 450 or larger with the same ratio (center-cropped otherwise).
- **Bundled images**: images placed in the repository's `images/` folder are built into the
  executable and are used when you have none for that fight.

A new or replaced image is picked up when the program starts (for the selected content, redrawn
locally without calling FFLogs) or when you select a content in the **Content** menu, even if
there is no new log on FFLogs. If an image is not picked up, the log shows the
background used ("Background: ...").

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

- **Font**: the image uses [Lilita One](https://fonts.google.com/specimen/Lilita+One) by Juan
  Montoreano, bundled under the SIL Open Font License (`fonts/lilita-one-license.txt`).
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
