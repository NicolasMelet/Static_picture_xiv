"""Calcul de la progression d'un groupe à partir des combats FFLogs."""


def compute(zone, reports, difficulty=None):
    """
    zone     : {id, name, encounters: [{id, name}]}
    reports  : liste de rapports renvoyés par FFLogs.report_fights()
    Retourne un dict prêt à être dessiné.
    """
    encounters = {e["id"]: {
        "id": e["id"], "name": e["name"], "pulls": 0, "kills": 0,
        "best_pct": None, "best_boss_pct": None, "phase_name": None,
        "phases_done": 0, "phases": [],
    } for e in zone["encounters"]}

    # Liste des phases (dans l'ordre du combat, intermissions comprises).
    for rep in reports:
        for ph in rep.get("phases") or []:
            enc = encounters.get(ph["encounterID"])
            if enc and len(ph.get("phases") or []) > len(enc["phases"]):
                enc["phases"] = ph["phases"]

    for rep in reports:
        for f in rep.get("fights") or []:
            enc = encounters.get(f["encounterID"])
            if not enc:
                continue
            if difficulty and f.get("difficulty") != difficulty:
                continue
            enc["pulls"] += 1
            if f.get("kill"):
                enc["kills"] += 1
                continue
            enc["phases_done"] = max(enc["phases_done"], _phases_done(enc, f))
            pct = f.get("fightPercentage")
            if pct is not None and (enc["best_pct"] is None or pct < enc["best_pct"]):
                enc["best_pct"] = pct
                enc["best_boss_pct"] = f.get("bossPercentage")
                enc["phase_name"] = _phase_name(enc, f)

    encs = list(encounters.values())
    real = [p for p in encs[0]["phases"] if not p.get("isIntermission")] if len(encs) == 1 else []
    if len(encs) == 1 and len(real) > 1:
        # Ultime (un seul combat découpé en phases) -> on compte les phases franchies.
        enc = encs[0]
        mode, total = "phases", len(real)
        done = total if enc["kills"] else min(enc["phases_done"], total)
    else:
        mode, total = "boss", len(encs)
        done = sum(1 for e in encs if e["kills"])

    return {
        "zone_id": zone["id"],
        "zone_name": zone["name"],
        "mode": mode,
        "done": done,
        "total": total,
        "encounters": encs,
    }


def _phases_done(enc, fight):
    """Nombre de vraies phases terminées lors d'un wipe."""
    idx = fight.get("lastPhaseAsAbsoluteIndex")
    if enc["phases"] and idx is not None:
        return sum(1 for p in enc["phases"][:idx] if not p.get("isIntermission"))
    # Sans la liste des phases : lastPhase compte séparément phases et intermissions.
    last = fight.get("lastPhase") or 0
    if fight.get("lastPhaseIsIntermission"):
        return last
    return max(0, last - 1)


def _phase_name(enc, fight):
    if len(enc["phases"]) < 2:
        return None
    idx = fight.get("lastPhaseAsAbsoluteIndex")
    if idx is not None and 0 <= idx < len(enc["phases"]):
        return enc["phases"][idx].get("name")
    last = fight.get("lastPhase")
    if not last:
        return None
    return f"I{last}" if fight.get("lastPhaseIsIntermission") else f"P{last}"
