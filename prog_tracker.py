"""
Suivi de progression FFLogs -> image hébergée sur GitHub Pages.

  ProgFFLogs.exe            lance le suivi avec icône dans la barre des tâches
  ProgFFLogs.exe --once     génère et publie l'image une fois, puis quitte
  ProgFFLogs.exe --setup    liste les ID de la Free Company, des statics et des contenus
  ProgFFLogs.exe --selftest vérifie que l'exécutable fonctionne (utilisé par le build)

(En développement : python prog_tracker.py ...)
"""
import argparse
import hashlib
import json
import logging
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

from fflogs import FFLogs
from progress import compute
from publisher import GitHubPages
from render import render

FROZEN = getattr(sys, "frozen", False)          # vrai dans l'exécutable PyInstaller
HERE = Path(__file__).resolve().parent
BUNDLE = Path(getattr(sys, "_MEIPASS", HERE))     # fichiers modèles embarqués dans l'exe
# Exécutable : réglages dans %APPDATA%\ProgFFLogs ; en développement : à côté du script.
DATA = Path(os.environ.get("APPDATA", Path.home())) / "ProgFFLogs" if FROZEN else HERE
DATA.mkdir(parents=True, exist_ok=True)
CONFIG = DATA / "config.json"
ENV_FILE = DATA / ".env"
CACHE = DATA / "cache"
OUTPUT = DATA / "output" / "prog.png"
APP_NAME = "ProgFFLogs"

logging.basicConfig(
    filename=DATA / "prog_tracker.log",
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
log = logging.getLogger("prog")
if sys.stdout and sys.stdout.isatty():
    log.addHandler(logging.StreamHandler(sys.stdout))


def load_env(path=ENV_FILE):
    """Charge les clés depuis .env (KEY=valeur), sans écraser les variables déjà définies."""
    try:
        lines = path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def secret(name):
    value = os.environ.get(name, "").strip()
    if not value or value.startswith("COLLER_ICI"):
        raise SystemExit(f"{name} manquant : renseignez-le dans {ENV_FILE}")
    return value


def fflogs_client():
    return FFLogs(secret("FFLOGS_CLIENT_ID"), secret("FFLOGS_CLIENT_SECRET"))


def message(text, error=False):
    """Affiche un message : boîte de dialogue Windows dans l'exe, console sinon."""
    if FROZEN and os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, str(text), "Prog FFLogs", 0x10 if error else 0x40)
    else:
        print(text)


def open_file(path):
    if os.name == "nt":
        os.startfile(path)
    else:
        print("Fichier :", path)


def first_run():
    """Crée .env et config.json à partir des modèles s'ils n'existent pas encore."""
    created = []
    for name, target in ((".env.example", ENV_FILE), ("config.example.json", CONFIG)):
        if not target.exists():
            target.write_text((BUNDLE / name).read_text(encoding="utf-8"), encoding="utf-8")
            created.append(target)
    if created:
        message("Premier lancement : remplissez les fichiers qui vont s'ouvrir "
                "(clés dans .env, réglages dans config.json), puis relancez Prog FFLogs.\n\n"
                f"Dossier : {DATA}")
        for path in created:
            open_file(path)
    return bool(created)


# --- Lancement au démarrage de Windows (registre, sans droits administrateur) ---

RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"


def autostart_enabled():
    if os.name != "nt":
        return False
    import winreg
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY) as key:
            winreg.QueryValueEx(key, APP_NAME)
        return True
    except OSError:
        return False


def set_autostart(enabled):
    if os.name != "nt":
        return
    import winreg
    with winreg.OpenKey(winreg.HKEY_CURRENT_USER, RUN_KEY, 0, winreg.KEY_SET_VALUE) as key:
        if enabled:
            cmd = f'"{sys.executable}"' if FROZEN else \
                f'"{Path(sys.executable).with_name("pythonw.exe")}" "{HERE / "prog_tracker.py"}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, cmd)
        else:
            try:
                winreg.DeleteValue(key, APP_NAME)
            except OSError:
                pass


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
        self.api = fflogs_client()
        gh = cfg["github"]
        self.pages = GitHubPages(secret("GITHUB_TOKEN"), gh["repo"], gh.get("branch", "gh-pages"),
                                 gh.get("path", "prog.png"))
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.force = False
        self.state = read_json(CACHE / "state.json", {})
        f = cfg["fflogs"]
        if not f.get("static_id"):
            f["static_id"] = resolve_static(self.api, f)["id"]
            save_config(cfg)

    # --- Une itération -------------------------------------------------------

    def check(self, force=False):
        cfg = self.cfg
        zone_id = cfg["zone_id"]
        guild_id = cfg["fflogs"]["static_id"]
        tag_id = cfg["fflogs"].get("raid_team_id")

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
            self.state["pending"] = f"Prog {zone['name']} : {prog['done']}/{prog['total']}"
        else:
            log.info("Progression inchangée, pas de publication")

        self.state.update(signature=signature, digest=digest)
        write_json(CACHE / "state.json", self.state)
        self.publish_if_due()
        return True

    def publish_if_due(self):
        """Publie l'image en attente, au plus une fois toutes les `min_publish_seconds`
        (GitHub Pages limite les déploiements à ~10 par heure). N'appelle pas FFLogs."""
        message = self.state.get("pending")
        if not message or not OUTPUT.exists():
            return
        wait = self.cfg.get("github", {}).get("min_publish_seconds", 600)
        remaining = self.state.get("last_publish", 0) + wait - time.time()
        if remaining > 0:
            log.info("Publication différée de %d s (limite GitHub Pages)", remaining)
            return
        url = self.pages.upload(OUTPUT, message)
        log.info("Image publiée : %s", url)
        self.state.update(pending=None, last_publish=time.time())
        write_json(CACHE / "state.json", self.state)

    # --- Boucle --------------------------------------------------------------

    def loop(self):
        """FFLogs n'est interrogé que si Archon ou ACT est ouvert (toutes les 5 min par
        défaut), plus une dernière fois à leur fermeture pour ne pas rater le dernier envoi.
        Archon/ACT fermés : seule la liste des processus Windows est consultée."""
        poll = self.cfg.get("poll", {})
        interval = poll.get("active_seconds", 300)
        watch = poll.get("process_check_seconds", 30)
        names = poll.get("process_names", ["Archon.exe", "Advanced Combat Tool.exe"])
        was_running, last_check = False, 0.0
        while not self.stop.is_set():
            running = archon_running(names)
            force, self.force = self.force, False
            due = running and time.monotonic() - last_check >= interval
            closed = was_running and not running
            if force or due or closed:
                if closed:
                    log.info("Archon/ACT fermé : dernière vérification")
                try:
                    self.check(force=force)
                except Exception:
                    log.exception("Erreur pendant la mise à jour")
                last_check = time.monotonic()
            else:
                try:
                    self.publish_if_due()
                except Exception:
                    log.exception("Erreur pendant la publication")
            was_running = running
            self.wake.wait(watch)
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

    def toggle_autostart(icon, item):
        set_autostart(not autostart_enabled())

    def show_ids(icon, item):
        threading.Thread(target=lambda: write_setup(tracker.cfg), daemon=True).start()

    menu = pystray.Menu(
        pystray.MenuItem("Contenu", zone_menu),
        pystray.MenuItem("Mettre à jour maintenant", lambda i, it: tracker.refresh_now()),
        pystray.MenuItem("Ouvrir l'image en ligne",
                         lambda i, it: webbrowser.open(tracker.pages.public_url)),
        pystray.MenuItem("Ouvrir l'image locale", lambda i, it: open_file(OUTPUT)),
        pystray.MenuItem("Recharger la liste des contenus", reload_zones),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Trouver les ID (static, contenus)", show_ids),
        pystray.MenuItem("Ouvrir le dossier des réglages", lambda i, it: open_file(DATA)),
        pystray.MenuItem("Lancer au démarrage de Windows", toggle_autostart,
                         checked=lambda item: autostart_enabled()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quitter", quit_app),
    )
    icon_img = Image.new("RGB", (64, 64), (225, 140, 60))
    icon = pystray.Icon("fflogs_prog", icon_img, "Prog FFLogs", menu)
    threading.Thread(target=tracker.loop, daemon=True).start()
    icon.run()


# --- Aide à la configuration -------------------------------------------------

def resolve_static(api, f):
    """Trouve le static (Guild de type 1) : par ID, ou par son nom dans la Free Company."""
    if f.get("static_id"):
        return api.guild(f["static_id"])
    g = api.guild(name=f.get("guild_name"), server=f.get("server"), region=f.get("region"))
    if not g:
        raise SystemExit("Free Company introuvable : vérifiez guild_name / server / region, "
                         "ou renseignez directement static_id.")
    wanted = (f.get("static_name") or "").strip().lower()
    if g["name"].lower() == wanted:
        return g
    for st in g["statics"] or []:
        if st["name"].strip().lower() == wanted:
            return st
    names = ", ".join(st["name"] for st in g["statics"] or []) or "aucun"
    raise SystemExit(f"Static « {f.get('static_name')} » introuvable dans {g['name']} "
                     f"(statics : {names}).")


def setup_lines(cfg):
    out = []
    print = out.append  # noqa: A001 - collecte les lignes au lieu de les afficher
    api = fflogs_client()
    f = cfg["fflogs"]
    if f.get("guild_name"):
        g = api.guild(name=f["guild_name"], server=f.get("server"), region=f.get("region"))
        if g:
            kind = "Static" if str(g["type"]) == "1" else "Free Company"
            print(f"{kind} : {g['name']} ({g['server']['name']})  ->  id = {g['id']}")
            for st in g["statics"] or []:
                print(f"  static : {st['name']:<30} ->  static_id = {st['id']}")
        else:
            print("Free Company introuvable : vérifiez guild_name / server / region.")
    try:
        st = resolve_static(api, f)
        print(f"\nStatic suivi : {st['name']}  ->  static_id = {st['id']}")
        for t in st.get("tags") or []:
            print(f"  équipe : {t['name']:<30} ->  raid_team_id = {t['id']}")
    except SystemExit as e:
        print(f"\n{e}")
    print("\nContenus disponibles :")
    for (_, exp), zones in zone_catalog(api):
        print(f"  [{exp}]")
        for z in zones:
            print(f"    {z['id']:>4}  {z['name']}")
    return out


def write_setup(cfg):
    """Écrit les ID dans setup.txt et l'ouvre (l'exe n'a pas de console)."""
    try:
        text = "\n".join(setup_lines(cfg))
    except SystemExit as e:
        text = str(e)
    path = DATA / "setup.txt"
    path.write_text(text, encoding="utf-8")
    if FROZEN:
        open_file(path)
    else:
        print(text)


def selftest():
    """Vérifie l'exécutable sans réseau obligatoire : modules embarqués, modèles, rendu."""
    import pystray  # noqa: F401
    for name in (".env.example", "config.example.json"):
        assert (BUNDLE / name).read_text(encoding="utf-8")
    zone = {"id": 0, "name": "Selftest", "encounters": [{"id": 0, "name": "Boss"}]}
    fights = [{"encounterID": 0, "kill": False, "fightPercentage": 42.0,
               "bossPercentage": 42.0, "lastPhase": 1}]
    out = DATA / "output" / "selftest.png"
    render(compute(zone, [{"fights": fights}]), "Selftest", out)
    assert out.stat().st_size > 0
    return 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--once", action="store_true")
    ap.add_argument("--setup", action="store_true")
    ap.add_argument("--selftest", action="store_true")
    args = ap.parse_args()
    if args.selftest:
        sys.exit(selftest())
    if first_run():
        return
    load_env()
    cfg = load_config()
    if args.setup:
        write_setup(cfg)
    elif args.once:
        tracker = Tracker(cfg)
        tracker.check(force=True)
        if tracker.state.get("pending"):
            message("Publication différée (limite de fréquence), elle sera faite par le suivi.")
        else:
            message(f"Image publiée : {tracker.pages.public_url}")
    else:
        tracker = Tracker(cfg)
        if cfg.get("autostart", True) and not tracker.state.get("autostart_set"):
            set_autostart(True)   # une seule fois : l'utilisateur peut le désactiver ensuite
            tracker.state["autostart_set"] = True
            write_json(CACHE / "state.json", tracker.state)
        run_tray(tracker)


if __name__ == "__main__":
    try:
        main()
    except SystemExit as e:
        if isinstance(e.code, str):
            message(e.code, error=True)
            sys.exit(1)
        raise
    except Exception as e:
        log.exception("Erreur fatale")
        message(f"Erreur : {e}\n\nDétails dans {DATA / 'prog_tracker.log'}", error=True)
        sys.exit(1)
