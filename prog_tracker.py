"""
FFLogs progression tracker -> image hosted on GitHub Pages.

  ProgFFLogs.exe            runs the tracker with a taskbar icon
  ProgFFLogs.exe --once     renders and publishes the image once, then exits
  ProgFFLogs.exe --setup    lists the static's raid teams and every content with its fights
  ProgFFLogs.exe --selftest checks that the executable works (used by the build)

(In development: python prog_tracker.py ...)
"""
import argparse
import hashlib
import json
import logging
import os
import sys
import threading
import time
import traceback
import webbrowser
from pathlib import Path

from fflogs import FFLogs
from images import create_folders, ensure_fight_folder, load_background
from progress import compute
from publisher import GitHubPages
from render import render

APP_NAME = "ProgFFLogs"
FROZEN = getattr(sys, "frozen", False)            # True inside the PyInstaller executable
HERE = Path(__file__).resolve().parent
BUNDLE = Path(getattr(sys, "_MEIPASS", HERE))     # files embedded in the executable
# Executable: user data in %APPDATA%\ProgFFLogs; development: next to the script.
DATA = Path(os.environ.get("APPDATA", Path.home())) / APP_NAME if FROZEN else HERE
DATA.mkdir(parents=True, exist_ok=True)
CONFIG = DATA / "config.json"
ENV_FILE = DATA / ".env"
CACHE = DATA / "cache"
STATE = CACHE / "state.json"
OUTPUT = DATA / "output" / "prog.png"
USER_IMAGES = DATA / "images"
BUNDLED_IMAGES = BUNDLE / "images"

logging.basicConfig(filename=DATA / "prog_tracker.log", level=logging.INFO,
                    format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("prog")
if sys.stdout and sys.stdout.isatty():
    log.addHandler(logging.StreamHandler(sys.stdout))


# --- Files --------------------------------------------------------------------------

def read_json(path, default=None):
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return default


def write_json(path, data, indent=None):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=indent), encoding="utf-8")


def load_env():
    """Loads KEY=value lines from .env into the environment (existing variables win)."""
    try:
        lines = ENV_FILE.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return
    for line in lines:
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            key, value = line.split("=", 1)
            os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def secret(name):
    value = os.environ.get(name, "").strip()
    if not value or value == "PASTE_HERE":
        raise SystemExit(f"{name} is missing: fill it in {ENV_FILE}")
    return value


def first_run():
    """Creates .env and config.json from the bundled templates; True if one was missing."""
    created = []
    for template, target in ((".env.example", ENV_FILE), ("config.example.json", CONFIG)):
        if not target.exists():
            target.write_text((BUNDLE / template).read_text(encoding="utf-8"), encoding="utf-8")
            created.append(target)
    if created:
        message("First launch: fill in the files that are about to open "
                "(keys in .env, settings in config.json), then start Prog FFLogs again.\n\n"
                f"Folder: {DATA}")
        for path in created:
            open_file(path)
    return bool(created)


# --- Windows ------------------------------------------------------------------------

def message(text, error=False):
    """Windows message box in the executable, console output otherwise."""
    if FROZEN and os.name == "nt":
        import ctypes
        ctypes.windll.user32.MessageBoxW(None, str(text), "Prog FFLogs", 0x10 if error else 0x40)
    else:
        print(text)


def open_file(path):
    if os.name == "nt":
        os.startfile(path)
    else:
        print("File:", path)


RUN_KEY = r"Software\Microsoft\Windows\CurrentVersion\Run"   # per-user startup programs


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
            command = f'"{sys.executable}"' if FROZEN else \
                f'"{Path(sys.executable).with_name("pythonw.exe")}" "{HERE / "prog_tracker.py"}"'
            winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, command)
        elif autostart_enabled():
            winreg.DeleteValue(key, APP_NAME)


def running_process_names():
    """Lowercase names of the running Windows processes, through CreateToolhelp32Snapshot:
    a few milliseconds, without starting an external program."""
    import ctypes
    from ctypes import wintypes

    class PROCESSENTRY32W(ctypes.Structure):
        _fields_ = [("dwSize", wintypes.DWORD), ("cntUsage", wintypes.DWORD),
                    ("th32ProcessID", wintypes.DWORD), ("th32DefaultHeapID", ctypes.c_size_t),
                    ("th32ModuleID", wintypes.DWORD), ("cntThreads", wintypes.DWORD),
                    ("th32ParentProcessID", wintypes.DWORD), ("pcPriClassBase", ctypes.c_long),
                    ("dwFlags", wintypes.DWORD), ("szExeFile", ctypes.c_wchar * 260)]

    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateToolhelp32Snapshot.restype = wintypes.HANDLE
    kernel32.CreateToolhelp32Snapshot.argtypes = [wintypes.DWORD, wintypes.DWORD]
    kernel32.Process32FirstW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.Process32NextW.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESSENTRY32W)]
    kernel32.CloseHandle.argtypes = [wintypes.HANDLE]

    snapshot = kernel32.CreateToolhelp32Snapshot(0x00000002, 0)    # TH32CS_SNAPPROCESS
    if snapshot in (None, wintypes.HANDLE(-1).value):
        raise OSError(ctypes.get_last_error(), "CreateToolhelp32Snapshot")
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = ctypes.sizeof(PROCESSENTRY32W)
        names = set()
        found = kernel32.Process32FirstW(snapshot, ctypes.byref(entry))
        while found:
            names.add(entry.szExeFile.lower())
            found = kernel32.Process32NextW(snapshot, ctypes.byref(entry))
        return names
    finally:
        kernel32.CloseHandle(snapshot)


def any_process_running(names):
    if os.name != "nt":
        return False
    running = running_process_names()
    return any(name.lower() in running for name in names)


# --- Contents -----------------------------------------------------------------------

def is_pick_one(zone):
    """Zone grouping independent fights (legacy ultimates, extreme trials...): one fight is
    chosen in a sub-menu instead of tracking the whole zone."""
    name = zone["name"].lower()
    return len(zone["encounters"]) > 1 and any(
        word in name for word in ("ultimate", "extreme", "trial", "unreal"))


def zone_catalog(api):
    """FFLogs zones grouped by expansion, newest expansion first (cached on disk)."""
    zones = read_json(CACHE / "zones.json")
    if not zones:
        zones = [z for z in api.zones() if z["encounters"]]
        write_json(CACHE / "zones.json", zones)
    by_expansion = {}
    for zone in zones:
        expansion = zone["expansion"]
        by_expansion.setdefault((expansion["id"], expansion["name"]), []).append(zone)
    return sorted(by_expansion.items(), key=lambda item: -item[0][0])


def setup_images():
    try:
        create_folders(USER_IMAGES)
    except OSError:
        log.exception("Cannot create the image folders")


# --- Tracker ------------------------------------------------------------------------

class Tracker:
    def __init__(self, cfg):
        self.cfg = cfg
        if not cfg["fflogs"].get("static_id"):
            raise SystemExit(f"fflogs.static_id is missing in {CONFIG}")
        self.api = FFLogs(secret("FFLOGS_CLIENT_ID"), secret("FFLOGS_CLIENT_SECRET"))
        github = cfg["github"]
        self.pages = GitHubPages(secret("GITHUB_TOKEN"), github["repo"],
                                 github.get("branch", "gh-pages"), github.get("path", "prog.png"))
        self.state = read_json(STATE, {})
        self.wake = threading.Event()
        self.stop = threading.Event()
        self.force = False

    def save_state(self):
        write_json(STATE, self.state)

    def update(self, force=False):
        """Fetches the static's reports, renders the image and queues it for publishing.
        Without force, nothing happens when no report was added or extended."""
        cfg = self.cfg
        zone_id, encounter_id = cfg["zone_id"], cfg.get("encounter_id")
        static_id, raid_team_id = cfg["fflogs"]["static_id"], cfg["fflogs"].get("raid_team_id")

        reports = self.api.report_list(static_id, zone_id, raid_team_id)
        signature = hashlib.sha1(json.dumps(
            [zone_id, encounter_id, raid_team_id, sorted((r["code"], r["endTime"]) for r in reports)]
        ).encode()).hexdigest()
        if not force and signature == self.state.get("signature"):
            log.info("No new log (%d reports)", len(reports))
            return

        # Only download reports that are new or still growing (live logging).
        loaded, to_fetch = [], []
        for report in reports:
            cached = read_json(CACHE / "fights" / f"{report['code']}.json")
            if cached and cached["endTime"] == report["endTime"]:
                loaded.append(cached["report"])
            else:
                to_fetch.append(report)
        for start in range(0, len(to_fetch), 10):
            batch = to_fetch[start:start + 10]
            fetched = self.api.report_fights([r["code"] for r in batch])
            for report in batch:
                if report["code"] in fetched:
                    write_json(CACHE / "fights" / f"{report['code']}.json",
                               {"endTime": report["endTime"], "report": fetched[report["code"]]})
                    loaded.append(fetched[report["code"]])
        log.info("%d reports (%d new/updated)", len(reports), len(to_fetch))

        zone = self.api.zone(zone_id)
        if encounter_id:
            zone["encounters"] = [e for e in zone["encounters"] if e["id"] == encounter_id]
        view = compute(zone, loaded, cfg.get("difficulty"))

        for fight in view["fights"]:
            ensure_fight_folder(USER_IMAGES, zone["name"], fight["name"])
        image, path = load_background(view["title"], zone["name"], view["phase"],
                                      view["mode"] == "ultimate", USER_IMAGES, BUNDLED_IMAGES)
        log.info("Background: %s", path)
        render(view, OUTPUT, image)

        shown = {k: v for k, v in view.items() if k != "fights"}
        digest = hashlib.sha1(json.dumps(shown, sort_keys=True).encode()).hexdigest()
        if force or digest != self.state.get("digest"):
            self.state["pending"] = f"Prog {view['title']}: {view['done']}/{view['total']}"
        else:
            log.info("Progression unchanged, nothing to publish")
        self.state.update(signature=signature, digest=digest)
        self.save_state()
        self.publish_if_due()

    def publish_if_due(self):
        """Publishes the pending image, at most once every `min_publish_seconds` (GitHub Pages
        allows about 10 deployments per hour). Never calls FFLogs."""
        commit_message = self.state.get("pending")
        if not commit_message or not OUTPUT.exists():
            return
        delay = self.cfg["github"].get("min_publish_seconds", 600)
        remaining = self.state.get("last_publish", 0) + delay - time.time()
        if remaining > 0:
            log.info("Publication postponed by %d s (GitHub Pages limit)", remaining)
            return
        log.info("Image published: %s", self.pages.upload(OUTPUT, commit_message))
        self.state.update(pending=None, last_publish=time.time())
        self.save_state()

    def loop(self):
        """FFLogs is only queried while Archon or ACT runs (every 5 min by default), plus once
        when they close so the last upload is not missed. Otherwise only the local process list
        is checked."""
        poll = self.cfg.get("poll", {})
        interval = poll.get("active_seconds", 300)
        check_every = poll.get("process_check_seconds", 30)
        names = poll.get("process_names", ["Archon.exe", "Advanced Combat Tool.exe"])
        was_running, last_update = False, 0.0
        while not self.stop.is_set():
            force, self.force = self.force, False
            try:
                running = any_process_running(names)
                due = running and time.monotonic() - last_update >= interval
                closed = was_running and not running
                if running and not was_running:
                    log.info("Archon/ACT detected: FFLogs checked every %d s", interval)
                if force or due or closed:
                    if closed:
                        log.info("Archon/ACT closed: last check")
                    last_update = time.monotonic()
                    self.update(force=force)
                else:
                    self.publish_if_due()
                was_running = running
            except Exception:
                log.exception("Error during the update")
            self.wake.wait(check_every)
            self.wake.clear()

    def update_now(self):
        self.force = True
        self.wake.set()

    def select(self, zone_id, encounter_id=None):
        self.cfg["zone_id"], self.cfg["encounter_id"] = zone_id, encounter_id
        write_json(CONFIG, self.cfg, indent=2)
        log.info("Selected content: zone %s, fight %s", zone_id, encounter_id)
        self.update_now()


# --- Taskbar icon -------------------------------------------------------------------

def run_tray(tracker):
    import pystray
    from PIL import Image

    def zone_item(zone):
        if is_pick_one(zone):
            return pystray.MenuItem(zone["name"], pystray.Menu(
                *[fight_item(zone, fight) for fight in zone["encounters"]]))
        return pystray.MenuItem(
            zone["name"], lambda icon, item: tracker.select(zone["id"]), radio=True,
            checked=lambda item: tracker.cfg["zone_id"] == zone["id"]
            and not tracker.cfg.get("encounter_id"))

    def fight_item(zone, fight):
        return pystray.MenuItem(
            fight["name"], lambda icon, item: tracker.select(zone["id"], fight["id"]), radio=True,
            checked=lambda item: tracker.cfg.get("encounter_id") == fight["id"])

    content_menu = pystray.Menu(*[
        pystray.MenuItem(expansion, pystray.Menu(*[zone_item(z) for z in zones]))
        for (_, expansion), zones in zone_catalog(tracker.api)])

    def reload_contents(icon, item):
        (CACHE / "zones.json").unlink(missing_ok=True)
        icon.notify("Restart the application to see the new contents.")

    def open_images(icon, item):
        setup_images()
        open_file(USER_IMAGES)

    def quit_app(icon, item):
        tracker.stop.set()
        tracker.wake.set()
        icon.stop()

    menu = pystray.Menu(
        pystray.MenuItem("Content", content_menu),
        pystray.MenuItem("Update now", lambda icon, item: tracker.update_now()),
        pystray.MenuItem("Open online image",
                         lambda icon, item: webbrowser.open(tracker.pages.public_url)),
        pystray.MenuItem("Open local image", lambda icon, item: open_file(OUTPUT)),
        pystray.MenuItem("Reload content list", reload_contents),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Find IDs (static, contents)", lambda icon, item: threading.Thread(
            target=write_setup, args=(tracker.cfg,), daemon=True).start()),
        pystray.MenuItem("Open settings folder", lambda icon, item: open_file(DATA)),
        pystray.MenuItem("Open images folder", open_images),
        pystray.MenuItem("Start with Windows",
                         lambda icon, item: set_autostart(not autostart_enabled()),
                         checked=lambda item: autostart_enabled()),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Quit", quit_app),
    )
    icon = pystray.Icon("fflogs_prog", Image.open(BUNDLE / "icon.ico"), "Prog FFLogs", menu)
    threading.Thread(target=tracker.loop, daemon=True).start()
    icon.run()


# --- Commands -----------------------------------------------------------------------

def write_setup(cfg):
    """Writes the static's raid teams and every content with its fights to setup.txt."""
    try:
        api = FFLogs(secret("FFLOGS_CLIENT_ID"), secret("FFLOGS_CLIENT_SECRET"))
        lines = []
        static = api.static(cfg["fflogs"]["static_id"])
        if static:
            lines.append(f"Static: {static['name']} ({static['server']['name']})  "
                         f"->  static_id = {static['id']}")
            for team in static["tags"] or []:
                lines.append(f"  raid team: {team['name']:<30} ->  raid_team_id = {team['id']}")
        else:
            lines.append(f"No static with id {cfg['fflogs']['static_id']} on FFLogs.")
        lines.append("\nContents:")
        for (_, expansion), zones in zone_catalog(api):
            lines.append(f"  [{expansion}]")
            for zone in zones:
                lines.append(f"    zone_id = {zone['id']:>4}  {zone['name']}")
                for fight in zone["encounters"]:
                    lines.append(f"        encounter_id = {fight['id']:>5}  {fight['name']}")
        text = "\n".join(lines)
    except Exception as e:
        text = f"Error: {e}"
    path = DATA / "setup.txt"
    path.write_text(text, encoding="utf-8")
    if FROZEN:
        open_file(path)
    else:
        print(text)


def selftest():
    """Checks the executable without network access: embedded files, image folders, rendering,
    process detection."""
    import pystray  # noqa: F401  (the tray library must be bundled)
    for template in (".env.example", "config.example.json"):
        assert (BUNDLE / template).read_text(encoding="utf-8")
    from PIL import Image
    assert Image.open(BUNDLE / "icon.ico").size[0] > 0
    assert (BUNDLE / "fonts" / "titan-one-regular.ttf").is_file()
    folders = DATA / "selftest-images"
    create_folders(folders)
    assert (folders / "1_ultimates" / "6_fru_futures-rewritten").is_dir()
    image, path = load_background("Selftest", "Selftest", None, False, folders, BUNDLED_IMAGES)
    assert path and path.stem == "default", path
    zone = {"id": 0, "name": "Selftest", "encounters": [{"id": 0, "name": "Boss"}]}
    pull = {"encounterID": 0, "kill": False, "fightPercentage": 42.0, "lastPhase": 1}
    out = DATA / "output" / "selftest.png"
    render(compute(zone, [{"fights": [pull]}]), out, image)
    assert out.stat().st_size > 0
    if os.name == "nt":
        own = Path(sys.executable).name
        start = time.perf_counter()
        names = running_process_names()
        elapsed = (time.perf_counter() - start) * 1000
        (DATA / "selftest.txt").write_text(          # read by the build (no console)
            f"{len(names)} processes listed in {elapsed:.1f} ms\n", encoding="utf-8")
        assert own.lower() in names, f"{own} missing from the process list"
        assert any_process_running([own]) and not any_process_running(["missing-xyz.exe"])
    return 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--setup", action="store_true")
    parser.add_argument("--selftest", action="store_true")
    args = parser.parse_args()
    if args.selftest:
        # Never show a dialog here: nobody can click it on the build machine.
        try:
            sys.exit(selftest())
        except Exception:
            traceback.print_exc()
            (DATA / "selftest-error.txt").write_text(traceback.format_exc(), encoding="utf-8")
            sys.exit(1)
    if first_run():
        return
    load_env()
    cfg = read_json(CONFIG)
    if cfg is None:
        raise SystemExit(f"Cannot read {CONFIG}")
    setup_images()
    if args.setup:
        write_setup(cfg)
        return
    tracker = Tracker(cfg)
    if args.once:
        tracker.update(force=True)
        if tracker.state.get("pending"):
            message("Publication postponed (rate limit); the background tracker will publish it.")
        else:
            message(f"Image published: {tracker.pages.public_url}")
        return
    if cfg.get("autostart", True) and not tracker.state.get("autostart_set"):
        set_autostart(True)              # only once: the user can turn it off afterwards
        tracker.state["autostart_set"] = True
        tracker.save_state()
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
        log.exception("Fatal error")
        message(f"Error: {e}\n\nDetails in {DATA / 'prog_tracker.log'}", error=True)
        sys.exit(1)
