"""Calcul de la progression d'un groupe à partir des combats FFLogs."""


def compute(zone, reports, difficulty=None):
    """
    zone     : {id, name, encounters: [{id, name}]}
    reports  : liste de rapports renvoyés par FFLogs.report_fights()
    Retourne un dict prêt à être dessiné.
    """
    encounters = {e["id"]: {
        "id": e["id"], "name": e["name"], "pulls": 0, "kills": 0,
        "best_pct": None, "best_phase": None, "best_boss_pct": None,
        "max_phase": 0, "phases": [],
    } for e in zone["encounters"]}

    for rep in reports:
        for ph in rep.get("phases") or []:
            enc = encounters.get(ph["encounterID"])
            if enc and len(ph["phases"]) > len(enc["phases"]):
                enc["phases"] = sorted(ph["phases"], key=lambda p: p["id"])
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
            pct = f.get("fightPercentage")
            if pct is None:
                continue
            if enc["best_pct"] is None or pct < enc["best_pct"]:
                enc["best_pct"] = pct
                enc["best_phase"] = f.get("lastPhase")
                enc["best_boss_pct"] = f.get("bossPercentage")
            enc["max_phase"] = max(enc["max_phase"], f.get("lastPhase") or 0)

    encs = list(encounters.values())
    for enc in encs:
        enc["phase_name"] = _phase_name(enc, enc["best_phase"])

    # Ultime (un seul combat découpé en phases) -> on compte les phases.
    real_phases = [p for p in encs[0]["phases"] if not p.get("isIntermission")] if len(encs) == 1 else []
    if len(encs) == 1 and len(real_phases) > 1:
        enc = encs[0]
        if enc["kills"]:
            done = len(real_phases)
        else:
            done = sum(1 for p in real_phases if p["id"] < enc["max_phase"])
        mode, total = "phases", len(real_phases)
    else:
        done = sum(1 for e in encs if e["kills"])
        mode, total = "boss", len(encs)

    return {
        "zone_id": zone["id"],
        "zone_name": zone["name"],
        "mode": mode,
        "done": done,
        "total": total,
        "encounters": encs,
    }


def _phase_name(enc, phase_id):
    if not phase_id:
        return None
    for p in enc["phases"]:
        if p["id"] == phase_id:
            return p["name"]
    return f"P{phase_id}" if len(enc["phases"]) > 1 else None
