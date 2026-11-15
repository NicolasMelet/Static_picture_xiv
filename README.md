# Prog FFLogs → fixed-link image

A small Windows program that reads the static's logs on FFLogs when you ask it to, computes the
progression (best % and bosses/phases cleared) and publishes a PNG image on **GitHub Pages**, for
free, at an address that never changes:

```
https://nicolasmelet.github.io/Static_picture_xiv/prog.png
```

## How it works

1. When Windows starts, `ProgFFLogs.exe` runs in the background (orange icon in the taskbar).
   It does nothing on its own: there is no automatic update.
2. The image is updated when you click **Update now** in the icon menu, or when you pick another
   content in the **Content** menu.
3. The program then asks the FFLogs API for the static's reports on the selected content,
   downloads the fights of the new reports, computes the progression and renders the image
   (850 × 450, the size of the background images):
   - in the background, your image for the current boss or phase (see "Background images");
   - top left, the name of the current boss (raid) or of the ultimate;
   - bottom left, in large type, the best percentage reached on the current boss / phase, then
     the current phase (ultimates only) and the number of pulls (on the
     current boss for a raid, in total for an ultimate);
   - bottom right, for a raid: the progression `X/Y`. A savage tier is always counted out of 5,
     the last boss having two phases. How FFLogs records that last boss:
     - two separate fights (Pandaemonium, AAC Heavyweight: Lindwurm and Lindwurm II): each kill
       counts, and a tier of 5 fights is never counted out of more than 5;
     - one fight with two phases (AAC Cruiserweight, M8S): reaching phase 2 counts, then the
       kill;
     - one fight without phase data (AAC Light-heavyweight, M4S): phase 2 cannot be detected,
       so the tier goes from 3/5 straight to 5/5 when M4S is killed;
   - bottom right, for an ultimate: `Pulls:` then the pull on which each phase was cleared for
     the first time (e.g. `P1: 156`, `P2: 824`).
4. The image is pushed to the repository's `gh-pages` branch. GitHub Pages serves it at the same
   address. A notification tells you when it is published (or that the update failed).

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
| `autostart` | `true`: registers itself to start with Windows on first launch |

To find the IDs (the static's raid teams, every `zone_id` and `encounter_id`): icon menu →
**Find IDs (static, contents)**, or `ProgFFLogs.exe --setup`. The result opens in Notepad.

The icon menu also toggles **Start with Windows** and has **Open settings folder**, which holds
the log file `prog_tracker.log`.

Manual test (renders and publishes once): `ProgFFLogs.exe --once`.

### Logs and testing

The log is `%APPDATA%\ProgFFLogs\prog_tracker.log` (icon menu → **Open settings folder**). Open
it with Notepad and reopen it to see new lines.

Click **Update now**: the log shows `N reports (M new/updated)`, `Background: <image used>` and
`Image published: ...`, or `Error during the update` followed by the details. Check the result
with **Open local image** and, after a minute, **Open online image**.

### Background images

No image is downloaded from FFLogs: the backgrounds are your own images, stored in
`%APPDATA%\ProgFFLogs\images` (icon menu → **Open images folder**). The rule is
**one folder = one image**:

- a fight has one folder, and the image you put in it (any name) is its background;
- a fight with phases has one subfolder per phase inside its folder: `p1`, `p2`, ...;
- when the folder is empty, the default image is used.

```
images/
  default.jpg                          used when the folder is empty (the kitten)
  readme.txt                           reminder of these rules
  1_ultimates/
    6_fru_futures-rewritten/
      p1/fatebreaker.png               one folder per phase
      p2/usurper.png
      p3/                              no image yet: default image
  2_savage-raids/
    6_dawntrail/2_aac-cruiserweight/
      m5s_dancing-green/dancing-green.png
      m8s_howling-blade/
        p1/howling-blade.png           one FFLogs fight with two phases
        p2/wolf.png
    6_dawntrail/3_aac-heavyweight/
      m11s_the-tyrant/tyrant.jpg
      m12s-1_lindwurm/lindwurm.png     M12S phase 1 (FFLogs fight "Lindwurm")
      m12s-2_lindwurm-ii/lindwurm.png  M12S phase 2 (FFLogs fight "Lindwurm II")
  3_extremes/
    6_dawntrail/ex1_valigarmanda/
  4_other-content/                     fights missing from the catalog (created automatically)
```

- **Which fights have phases**: every ultimate, and a savage last boss that FFLogs records as one
  fight with two phases (M8S, Howling Blade). M12S is two separate FFLogs fights, so it has two
  folders instead. M4S has no phase data on FFLogs: a single image in its folder.
- **Phase folders** are numbered like the image ("Phase 3" → `p3`; intermissions do not count).
  The folder of the current fight or phase is created during the update when it does not exist
  yet; you can also create `p1`, `p2`, ... yourself beforehand.
- **Finding the folder**: the end of a fight folder's name, after the last `_`, is the fight's
  FFLogs name in lowercase with `-` between words (`m11s_the-tyrant` for *The Tyrant*): keep it.
  The folder can be anywhere under `images/`. A fight without a folder (content released after
  this version) gets one in `4_other-content/<fight>` the first time it is tracked.
- **Image**: `.png`, `.jpg`, `.jpeg` or `.webp`. Only one image per folder is expected: the first
  one in alphabetical order is used. Recommended size: 850 × 450 or larger with the same ratio
  (center-cropped otherwise).
- **Default image**: `default.jpg` or `default.png` at the root of your images folder replaces
  the bundled kitten.

After adding or replacing an image, click **Update now**. The log shows the image used
("Background: ...").

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
- **Deployment limit**: GitHub recommends at most ~10 deployments per hour. Every **Update now**
  is one deployment: avoid clicking it more than a few times per hour.
- **Everything is public**: with a free account, Pages requires a public repository. The code and
  the image are visible to everyone; the keys stay in `.env` on your PC.
- **History**: each update adds a commit on `gh-pages` (a few dozen KB). Irrelevant at the scale
  of a tier, the size limit of a Pages site being 1 GB.
- **The `gh-pages` branch** is independent from `main`: it only holds the site, the code stays on
  `main`. The program only replaces `prog.png` there. The page
  <https://nicolasmelet.github.io/Static_picture_xiv/> shows the image and reloads it every
  5 minutes.
