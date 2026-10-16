"""
Suivi de progression FFLogs -> image hébergée sur GitHub Pages.

  pythonw prog_tracker.py          lance le suivi avec icône dans la barre des tâches
  python  prog_tracker.py --once   génère et publie l'image une fois, puis quitte
  python  prog_tracker.py --setup  affiche l'ID de la guilde, ses statics et les contenus
"""
import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path

from fflogs import FFLogs
from progress import compute
from publisher import GitHubPages
from render import render

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
CACHE = HERE / "cache"
OUTPUT = HERE / "output" / "prog.png"

logging.basicConfig(
    filename=HERE / "prog_tracker.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("prog")
if sys.stdout and sys.stdout.isatty():
    log.addHandler(logging.StreamHandler(sys.stdout))


def load_config():
    with open(CONFIG, encoding="utf-8") as fh:
        return json.load(fh)


def save_config(cfg):
    with open(CONFIG, "w", encoding="utf-8") as fh:
        json.dump(cfg, fh, indent=2, ensure_ascii=False)


def read_json(path, default=None):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except (OSError, ValueError):
        return default


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False)


def archon_running(names):
    """Vrai si l'application Archon (ou ACT) tourne : on interroge FFLogs plus souvent."""
    if os.name != "nt":
        return False
    try:
        out = subprocess.run(
            ["tasklist", "/fo", "csv", "/nh"], capture_output=True, text=True,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        ).stdout.lower()
    except OSError:
        return False
    return any(f'"{n.lower()}"' in out for n in names)


class Tracker:
    def __init__(self, cfg):
        self.cfg = cfg
        self.api = FFLogs(cfg["fflogs"]["client_id"], cfg["fflogs"]["client_secret"])
        gh = cfg["github"]
        self.pages = GitHubPages(gh["token"], gh["repo"], gh.get("branch", "gh-pages"),
                                 gh.get("path", "prog.png"))
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.force = False
        self.state = read_json(CACHE / "state.json", {})
        f = cfg["fflogs"]
        if not f.get("guild_id"):
            g = self.api.guild(name=f["guild_name"], server=f["server"], region=f["region"])
            if not g:
                raise SystemExit("Guilde introuvable : vérifiez guild_name / server / region.")
            f["guild_id"] = g["id"]
            save_config(cfg)

    # --- Une itération -------------------------------------------------------

    def check(self, force=False):
        cfg = self.cfg
        zone_id = cfg["zone_id"]
        guild_id = cfg["fflogs"]["guild_id"]
        tag_id = cfg["fflogs"].get("static_tag_id")

        reports = self.api.report_list(guild_id, zone_id, tag_id)
        signature = hashlib.sha1(json.dumps(
            [zone_id, tag_id, sorted((r["code"], r["endTime"]) for r in reports)]
        ).encode()).hexdigest()
        if not force and signature == self.state.get("signature"):
            log.info("Aucun nouveau log (%d rapports)", len(reports))
            return False

        # Ne retélécharge que les rapports nouveaux ou encore en cours d'envoi.
        fights_cache = CACHE / "fights"
        to_fetch, loaded = [], []
        for r in reports:
            cached = read_json(fights_cache / f"{r['code']}.json")
            if cached and cached.get("endTime") == r["endTime"]:
                loaded.append(cached["report"])
            else:
                to_fetch.append(r)
        for i in range(0, len(to_fetch), 10):
            chunk = to_fetch[i:i + 10]
            fetched = self.api.report_fights([r["code"] for r in chunk])
            for r in chunk:
                rep = fetched.get(r["code"])
                if rep:
                    write_json(fights_cache / f"{r['code']}.json",
                               {"endTime": r["endTime"], "report": rep})
                    loaded.append(rep)
        log.info("%d rapports (%d nouveaux/modifiés)", len(reports), len(to_fetch))

        zone = self.api.zone(zone_id)
        prog = compute(zone, loaded, cfg.get("difficulty"))
        render(prog, cfg.get("team_name", ""), OUTPUT)

        digest = hashlib.sha1(json.dumps(
            prog, sort_keys=True, default=str).encode()).hexdigest()
        if force or digest != self.state.get("digest"):
            url = self.pages.upload(OUTPUT, f"Prog {zone['name']} : {prog['done']}/{prog['total']}")
            log.info("Image publiée : %s", url)
        else:
            log.info("Progression inchangée, pas de publication")

        self.state.update(signature=signature, digest=digest)
        write_json(CACHE / "state.json", self.state)
        return True

    # --- Boucle --------------------------------------------------------------

    def loop(self):
        poll = self.cfg.get("poll", {})
        fast = poll.get("active_seconds", 120)
        slow = poll.get("idle_seconds", 900)
        names = poll.get("process_names", ["Archon.exe", "Advanced Combat Tool.exe"])
        while not self.stop.is_set():
            try:
                force, self.force = self.force, False
                self.check(force=force)
            except Exception:
                log.exception("Erreur pendant la mise à jour")
            delay = fast if archon_running(names) else slow
            self.wake.wait(delay)
            self.wake.clear()

    def refresh_now(self, force=True):
        self.force = force
        self.wake.set()

    def set_zone(self, zone_id):
        self.cfg["zone_id"] = zone_id
        save_config(self.cfg)
        log.info("Contenu sélectionné : %s", zone_id)
        self.refresh_now()


# --- Icône de la barre des tâches --------------------------------------------

def zone_catalog(api):
    path = CACHE / "zones.json"
    zones = read_json(path)
    if not zones:
        zones = [z for z in api.zones() if z["encounters"]]
        write_json(path, zones)
    by_exp = {}
    for z in zones:
        exp = z["expansion"]
        by_exp.setdefault((exp["id"], exp["name"]), []).append(z)
    return sorted(by_exp.items(), key=lambda kv: -kv[0][0])


def run_tray(tracker):
    import pystray
    from PIL import Image

    def zone_item(z):
        return pystray.MenuItem(
            z["name"], lambda icon, item: tracker.set_zone(z["id"]),
            checked=lambda item: tracker.cfg["zone_id"] == z["id"], radio=True)

    catalog = zone_catalog(tracker.api)
    zone_menu = pystray.Menu(*[
        pystray.MenuItem(exp_name, pystray.Menu(*[zone_item(z) for z in zones]))
        for (_, exp_name), zones in catalog
    ])

    def quit_app(icon, item):
        tracker.stop.set()
        tracker.wake.set()
        icon.stop()

    def reload_zones(icon, item):
        (CACHE / "zones.json").unlink(missing_ok=True)
        icon.notify("Relancez l'application pour voir les nouveaux contenus.")

    menu = pystray.Menu(
        pystray.MenuItem("Contenu", zone_menu),
        pystray.MenuItem("Mettre à jour maintenant", lambda i, it: tracker.refresh_now()),
        pystray.MenuItem("Ouvrir l'image en ligne",
                         lambda i, it: webbrowser.open(tracker.pages.public_url)),
        pystray.MenuItem("Ouvrir l'image locale", lambda i, it: os.startfile(OUTPUT)),
        pystray.MenuItem("Recharger la liste des contenus", reload_zones),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quitter", quit_app),
    )
    icon_img = Image.new("RGB", (64, 64), (225, 140, 60))
    icon = pystray.Icon("fflogs_prog", icon_img, "Prog FFLogs", menu)
    threading.Thread(target=tracker.loop, daemon=True).start()
    icon.run()


# --- Aide à la configuration -------------------------------------------------

def setup(cfg):
    api = FFLogs(cfg["fflogs"]["client_id"], cfg["fflogs"]["client_secret"])
    f = cfg["fflogs"]
    g = api.guild(f.get("guild_id"), f.get("guild_name"), f.get("server"), f.get("region"))
    if not g:
        print("Guilde introuvable : vérifiez guild_name / server / region.")
    else:
        print(f"Guilde : {g['name']} ({g['server']['name']})  ->  guild_id = {g['id']}")
        for t in g["tags"] or []:
            print(f"  static : {t['name']:<30} ->  static_tag_id = {t['id']}")
    print("\nContenus disponibles :")
    for (_, exp), zones in zone_catalog(api):
        print(f"  [{exp}]")
        for z in zones:
            print(f"    {z['id']:>4}  {z['name']}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--setup", action="store_true")
    args = ap.parse_args()
    cfg = load_config()
    if args.setup:
        setup(cfg)
    elif args.once:
        Tracker(cfg).check(force=True)
        print("OK :", OUTPUT)
    else:
        run_tray(Tracker(cfg))


if __name__ == "__main__":
    main()
