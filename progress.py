"""Turns the FFLogs fights of a zone into what the image shows.

Raid:     bosses defeated (X/Y), pulls and best % on the first boss not killed yet.
Ultimate: current phase, pull on which each phase was first cleared, total pulls,
          best % in the current phase.
"""


def compute(zone, reports, difficulty=None):
    """
    zone:       {"id", "name", "encounters": [{"id", "name"}]}
    reports:    reports returned by FFLogs.report_fights()
    difficulty: raid difficulty filter (101 = Savage); ignored for single-fight zones
    """
    fights = [{"id": e["id"], "name": e["name"], "pulls": [], "phases": []}
              for e in zone["encounters"]]
    by_id = {f["id"]: f for f in fights}
    single = len(fights) == 1

    # Pulls in chronological order: report start time, then pull start time.
    for report in sorted(reports, key=lambda r: r.get("startTime") or 0):
        for definition in report.get("phases") or []:
            fight = by_id.get(definition["encounterID"])
            if fight and len(definition.get("phases") or []) > len(fight["phases"]):
                fight["phases"] = definition["phases"]
        for pull in sorted(report.get("fights") or [], key=lambda p: p.get("startTime") or 0):
            fight = by_id.get(pull["encounterID"])
            if fight and (single or not difficulty or pull.get("difficulty") == difficulty):
                fight["pulls"].append(pull)

    # Ultimate: one fight split into phases. Before the first log FFLogs gives no phase
    # definitions, so the zone name ("... (Ultimate)", "Ultimates (Legacy)") decides.
    if single and (len(real_phases(fights[0])) > 1 or "ultimate" in zone["name"].lower()):
        return _ultimate(fights[0])
    return _raid(fights)


def real_phases(fight):
    return [p for p in fight["phases"] if not p.get("isIntermission")]


def phases_cleared(fight, pull):
    """Number of real phases (intermissions excluded) cleared during a pull."""
    if pull.get("kill"):
        return max(len(real_phases(fight)), 1)
    index = pull.get("lastPhaseAsAbsoluteIndex")
    if fight["phases"] and index is not None:
        return len([p for p in fight["phases"][:index] if not p.get("isIntermission")])
    # Without phase definitions, lastPhase counts phases and intermissions separately.
    last = pull.get("lastPhase") or 0
    return last if pull.get("lastPhaseIsIntermission") else max(0, last - 1)


def best_percent(pulls, key="fightPercentage"):
    values = [p.get(key) for p in pulls if not p.get("kill") and p.get(key) is not None]
    return min(values) if values else None


def last_boss_counts_twice(fights):
    """Savage: a two-phase last boss counts twice (Arcadion, 4 fights -> X/5).
    Pandaemonium already splits its last boss into two FFLogs fights, so nothing to add there."""
    if len(fights) < 2:
        return False
    last = fights[-1]
    if last["phases"]:
        return len(real_phases(last)) >= 2
    return len(fights) == 4


def _raid(fights):
    killed = [any(p.get("kill") for p in f["pulls"]) for f in fights]
    current = next((f for f, k in zip(fights, killed) if not k), fights[-1])
    cleared = all(killed)
    done, total = sum(killed), len(fights)
    phase, best = None, best_percent(current["pulls"])

    if last_boss_counts_twice(fights):
        total += 1
        last = fights[-1]
        if killed[-1]:
            done += 1
        elif current is last:
            in_phase_2 = [p for p in last["pulls"] if phases_cleared(last, p) >= 1]
            phase = 2 if in_phase_2 else 1
            done += phase - 1
            # Phase 2: best % is the boss health reached on pulls that got there.
            best = best_percent(in_phase_2, "bossPercentage") if in_phase_2 else best

    return {
        "mode": "raid",
        "title": current["name"],
        "phase": phase,
        "done": done,
        "total": total,
        "cleared": cleared,
        "pulls": len(current["pulls"]),
        "best_pct": None if cleared else best,
        "fights": fights,
    }


def _ultimate(fight):
    total = len(real_phases(fight))
    first_clear = {}          # phase -> number of the pull that cleared it for the first time
    best = {}                 # phase -> lowest boss health reached in that phase
    for number, pull in enumerate(fight["pulls"], start=1):
        cleared_count = phases_cleared(fight, pull)
        for phase in range(1, cleared_count + 1):
            first_clear.setdefault(phase, number)
        if pull.get("kill") or pull.get("lastPhaseIsIntermission"):
            continue
        reached = cleared_count + 1
        pct = pull.get("bossPercentage")
        if pct is None:
            pct = pull.get("fightPercentage")
        if pct is not None and pct < best.get(reached, 101):
            best[reached] = pct

    cleared = any(p.get("kill") for p in fight["pulls"])
    current = total if cleared else len(first_clear) + 1
    return {
        "mode": "ultimate",
        "title": fight["name"],
        "phase": current,
        "done": len(first_clear),
        "total": total,
        "cleared": cleared,
        "pulls": len(fight["pulls"]),
        "phase_clears": sorted(first_clear.items()),
        "best_pct": None if cleared else best.get(current),
        "fights": [fight],
    }
