"""Arborescence des dossiers d'images : ultimes, raids sadiques et défis extrêmes.

Chaque combat est un dossier « CODE - Nom » (les numéros devant ne servent qu'à l'ordre). Le nom (après « - ») est celui du combat sur FFLogs,
en anglais : c'est lui qui permet au programme de retrouver le dossier. Le code devant
(M1S, P4S (1), UCOB...) n'est là que pour la lisibilité.
Les phases sont des sous-dossiers « Phase N - ... » ; seul « Phase N » compte.
"""

ULTIMATES = "1 - Ultimates"
SAVAGE = "2 - Raids sadiques"
EXTREME = "3 - Extrêmes"
OTHER = "4 - Autres contenus"     # créé par le programme pour les combats absents du catalogue


def _phases(*names):
    return [f"Phase {i} - {n}" if n else f"Phase {i}" for i, n in enumerate(names, start=1)]


TWO_PHASES = _phases(None, None)

# {catégorie: {sous-dossier: {combat: [phases]}}} ; sous-dossier None = combats à la racine.
TREE = {
    ULTIMATES: {None: {
        "1. UCOB - The Unending Coil of Bahamut": _phases(
            "Twintania", "Nael deus Darnus", "Bahamut Prime", "Triple Threat", "Golden Bahamut"),
        "2. UWU - The Weapon's Refrain (Ultima Weapon)": _phases("Garuda", "Ifrit", "Titan", "The Ultima Weapon"),
        "3. TEA - The Epic of Alexander": _phases(
            "Living Liquid", "Brute Justice et Cruise Chaser", "Alexander Prime",
            "Perfect Alexander"),
        "4. DSR - Dragonsong's Reprise": _phases(
            "Adelphel, Grinnaux et Charibert", "King Thordan", "Nidhogg", "The Eyes of Nidhogg",
            "Alternate Thordan", "Nidhogg et Hraesvelgr", "Dragon-king Thordan"),
        "5. TOP - The Omega Protocol": _phases(
            "Omega", "Omega-M et Omega-F", "Omega Reconfigured", "Blue Screen",
            "Run Dynamis", "Alpha Omega"),
        "6. FRU - Futures Rewritten": _phases(
            "Fatebreaker", "Usurper of Frost", "Oracle of Darkness", "Usurper et Oracle",
            "Pandora"),
        "7. DMU - Dancing Mad": _phases("Kefka", None, None, None, None),
    }},
    SAVAGE: {
        "2 - Heavensward/1 - Alexander Gordias": {
            "A1S - Oppressor": [], "A2S - Cuff of the Father": [],
            "A3S - Living Liquid": [], "A4S - The Manipulator": []},
        "2 - Heavensward/2 - Alexander Midas": {
            "A5S - Ratfinx Twinkledinks": [], "A6S - Vortexer": [],
            "A7S - Quickthinx Allthoughts": [], "A8S - Brute Justice": []},
        "2 - Heavensward/3 - Alexander The Creator": {
            "A9S - Refurbisher 0": [], "A10S - Lamebrix Strikebocks": [],
            "A11S - Cruise Chaser": [], "A12S - Alexander Prime": []},
        "3 - Stormblood/1 - Deltascape": {
            "O1S - Alte Roite": [], "O2S - Catastrophe": [], "O3S - Halicarnassus": [],
            "O4S (1) - Exdeath": [], "O4S (2) - Neo Exdeath": []},
        "3 - Stormblood/2 - Sigmascape": {
            "O5S - Phantom Train": [], "O6S - Demon Chadarnook": [], "O7S - Guardian": [],
            "O8S (1) - Kefka": [], "O8S (2) - God Kefka": []},
        "3 - Stormblood/3 - Alphascape": {
            "O9S - Chaos": [], "O10S - Midgardsormr": [], "O11S - Omega": [],
            "O12S (1) - Omega-M and Omega-F": [], "O12S (2) - The Final Omega": []},
        "4 - Shadowbringers/1 - Eden's Gate": {
            "E1S - Eden Prime": [], "E2S - Voidwalker": [], "E3S - Leviathan": [],
            "E4S - Titan": []},
        "4 - Shadowbringers/2 - Eden's Verse": {
            "E5S - Ramuh": [], "E6S - Ifrit and Garuda": [], "E7S - The Idol of Darkness": [],
            "E8S - Shiva": []},
        "4 - Shadowbringers/3 - Eden's Promise": {
            "E9S - Cloud of Darkness": [], "E10S - Shadowkeeper": [], "E11S - Fatebreaker": [],
            "E12S (1) - Eden's Promise": [], "E12S (2) - Oracle of Darkness": []},
        "5 - Endwalker/1 - Asphodelos": {
            "P1S - Erichthonios": [], "P2S - Hippokampos": [], "P3S - Phoinix": [],
            "P4S (1) - Hesperos": [], "P4S (2) - Hesperos II": []},
        "5 - Endwalker/2 - Abyssos": {
            "P5S - Proto-Carbuncle": [], "P6S - Hegemone": [], "P7S - Agdistis": [],
            "P8S (1) - Hephaistos": [], "P8S (2) - Hephaistos II": []},
        "5 - Endwalker/3 - Anabaseis": {
            "P9S - Kokytos": [], "P10S - Pandaemonium": [], "P11S - Themis": [],
            "P12S (1) - Athena": [], "P12S (2) - Pallas Athena": []},
        "6 - Dawntrail/1 - AAC Light-heavyweight": {
            "M1S - Black Cat": [], "M2S - Honey B. Lovely": [], "M3S - Brute Bomber": [],
            "M4S - Wicked Thunder": TWO_PHASES},
        "6 - Dawntrail/2 - AAC Cruiserweight": {
            "M5S - Dancing Green": [], "M6S - Sugar Riot": [], "M7S - Brute Abombinator": [],
            "M8S - Howling Blade": TWO_PHASES},
        "6 - Dawntrail/3 - AAC Heavyweight": {
            "M9S - Vamp Fatale": [], "M10S - Red Hot and Deep Blue": [],
            "M11S - The Tyrant": [], "M12S - Lindwurm": TWO_PHASES},
    },
    EXTREME: {
        "1 - A Realm Reborn": {n: [] for n in (
            "EX1 - Ifrit", "EX2 - Garuda", "EX3 - Titan", "EX4 - Leviathan", "EX5 - Ramuh",
            "EX6 - Good King Moggle Mog XII", "EX7 - Shiva", "EX8 - Ultima Weapon")},
        "2 - Heavensward": {n: [] for n in (
            "EX1 - Bismarck", "EX2 - Ravana", "EX3 - Thordan", "EX4 - Sephirot",
            "EX5 - Nidhogg", "EX6 - Sophia", "EX7 - Zurvan")},
        "3 - Stormblood": {n: [] for n in (
            "EX1 - Susano", "EX2 - Lakshmi", "EX3 - Shinryu", "EX4 - Byakko",
            "EX5 - Tsukuyomi", "EX6 - Suzaku", "EX7 - Seiryu")},
        "4 - Shadowbringers": {n: [] for n in (
            "EX1 - Titania", "EX2 - Innocence", "EX3 - Hades", "EX4 - Ruby Weapon",
            "EX5 - Varis yae Galvus", "EX6 - Warrior of Light", "EX7 - Emerald Weapon",
            "EX8 - Diamond Weapon")},
        "5 - Endwalker": {n: [] for n in (
            "EX1 - Zodiark", "EX2 - Hydaelyn", "EX3 - The Endsinger", "EX4 - Barbariccia",
            "EX5 - Rubicante", "EX6 - Golbez", "EX7 - Zeromus")},
        "6 - Dawntrail": {n: [] for n in (
            "EX1 - Valigarmanda", "EX2 - Zoraal Ja", "EX3 - Queen Eternal", "EX4 - Zelenia",
            "EX5 - Necron")},
    },
}


def folders():
    """Tous les dossiers à créer, en chemins relatifs (catégorie/sous-dossier/combat/phase)."""
    out = [OTHER]
    for category, groups in TREE.items():
        out.append(category)
        for group, fights in groups.items():
            base = f"{category}/{group}" if group else category
            out.append(base)
            for fight, phases in fights.items():
                out.append(f"{base}/{fight}")
                out.extend(f"{base}/{fight}/{p}" for p in phases)
    return out
