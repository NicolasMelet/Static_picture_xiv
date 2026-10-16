"""Calcul de la progression d'un groupe à partir des combats FFLogs.

Raid   : X/Y boss vaincus, pulls et meilleur % sur le premier boss pas encore tué.
Ultime : phase actuelle, pulls nécessaires pour passer chaque phase, meilleur % sur la phase
         actuelle.
"""


def compute(zone, reports, difficulty=None, ultimate_pulls="cumulative", content=None):
    """
    zone           : {id, name, encounters: [{id, name}]}
    reports        : rapports renvoyés par FFLogs.report_fights()
    difficulty     : filtre (101 = Sadique) appliqué aux raids, ignoré pour les ultimes
    ultimate_pulls : "cumulative" (Pn = numéro du pull qui a passé la phase n)
                     ou "per_phase" (Pn = pulls passés dans la phase n)
    content        : nom du dossier d'images (par défaut le nom de la zone)
    """
    encs = [{
        "id": e["id"], "name": e["name"], "pulls": 0, "kills": 0,
        "best_pct": None, "phases": [], "fights": [],
    } for e in zone["encounters"]]
    by_id = {e["id"]: e for e in encs}
    single = len(encs) == 1

    # Pulls dans l'ordre chronologique (début du rapport + début du combat).
    for rep in sorted(reports, key=lambda r: r.get("startTime") or 0):
        for ph in rep.get("phases") or []:
            enc = by_id.get(ph["encounterID"])
            if enc and len(ph.get("phases") or []) > len(enc["phases"]):
                enc["phases"] = ph["phases"]
        for f in sorted(rep.get("fights") or [], key=lambda f: f.get("startTime") or 0):
            enc = by_id.get(f["encounterID"])
            if not enc:
                continue
            if difficulty and not single and f.get("difficulty") != difficulty:
                continue
            enc["fights"].append(f)
            enc["pulls"] += 1
            if f.get("kill"):
                enc["kills"] += 1
            else:
                pct = f.get("fightPercentage")
                if pct is not None and (enc["best_pct"] is None or pct < enc["best_pct"]):
                    enc["best_pct"] = pct

    real = real_phases(encs[0]) if single else []
    if single and len(real) > 1:
        view = _ultimate(encs[0], len(real), ultimate_pulls)
    else:
        view = _raid(encs)
    view.update(zone_id=zone["id"], zone_name=zone["name"], content=content or zone["name"])
    for enc in encs:
        del enc["fights"]
    view["encounters"] = encs
    return view


def real_phases(enc):
    return [p for p in enc["phases"] if not p.get("isIntermission")]


def last_boss_counts_double(encs):
    """Sadique : le dernier boss en deux phases compte double (Arcadion : 4 combats -> X/5).
    Pandaemonium sépare déjà ses derniers boss en deux combats (5 combats) : pas de doublement."""
    if len(encs) < 2:
        return False
    last = encs[-1]
    if last["phases"]:
        return len(real_phases(last)) >= 2
    return len(encs) == 4


def _raid(encs):
    last = encs[-1] if last_boss_counts_double(encs) else None
    total = len(encs) + (1 if last else 0)
    current = next((e for e in encs if not e["kills"]), encs[-1])
    cleared = all(e["kills"] for e in encs)

    done = sum(1 for e in encs if e["kills"])
    phase, best = None, None if current["kills"] else current["best_pct"]
    if last:
        if last["kills"]:
            done += 1                                  # deuxième phase du dernier boss
        elif current is last:
            reached_p2 = [f for f in last["fights"] if _phases_done(last, f) >= 1]
            phase = 2 if reached_p2 else 1
            done += phase - 1
            # Meilleur % de la phase en cours : vie du boss sur les pulls arrivés à cette phase.
            pulls = reached_p2 or last["fights"]
            pcts = [f.get("bossPercentage") if phase == 2 else f.get("fightPercentage")
                    for f in pulls if not f.get("kill")]
            pcts = [p for p in pcts if p is not None]
            best = min(pcts) if pcts else None

    return {
        "mode": "boss",
        "title": current["name"],
        "encounter_id": current["id"],
        "boss_index": encs.index(current) + 1,
        "phase": phase,
        "done": done,
        "total": total,
        "cleared": cleared,
        "progress_label": f"{done}/{total}",
        "pulls_lines": [f"Pulls: {current['pulls']}"],
        "best_pct": None if cleared else best,
    }


def _ultimate(enc, total, mode):
    passed_at = {}            # phase -> numéro du pull qui l'a passée pour la première fois
    best = {}                 # phase -> meilleur % (vie du boss) atteint dans cette phase
    for n, f in enumerate(enc["fights"], start=1):
        reached = total + 1 if f.get("kill") else _phases_done(enc, f) + 1
        for p in range(1, reached):
            passed_at.setdefault(p, n)
        if not f.get("kill") and not f.get("lastPhaseIsIntermission"):
            pct = f.get("bossPercentage")
            if pct is None:
                pct = f.get("fightPercentage")
            if pct is not None and (reached not in best or pct < best[reached]):
                best[reached] = pct

    cleared = enc["kills"] > 0
    current = total if cleared else min(len(passed_at) + 1, total)
    lines, previous = [], 0
    for p in range(1, current + 1):
        at = passed_at.get(p, enc["pulls"])          # phase en cours : pulls jusqu'ici
        count = at if mode == "cumulative" else at - previous
        previous = at
        lines.append(f"P{p}: {count}")

    return {
        "mode": "phases",
        "title": enc["name"],
        "encounter_id": enc["id"],
        "boss_index": None,
        "phase": current,
        "done": total if cleared else current - 1,
        "total": total,
        "cleared": cleared,
        "progress_label": "Clear" if cleared else f"Phase {current}",
        "pulls_lines": lines,
        "best_pct": None if cleared else best.get(current),
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
