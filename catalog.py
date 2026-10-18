"""Folder tree of the background images: one folder per fight.

A fight folder is named "CODE - Name". The name after " - " is the fight's English name on
FFLogs: it is what lets the program find the folder. The code and numbers in front only control
the display order. Phase images are files inside the fight folder ("Phase 3.png"), never
sub-folders, so a new ultimate's phase count is not spoiled.
"""

ULTIMATES = "1 - Ultimates"
SAVAGE = "2 - Savage Raids"
EXTREMES = "3 - Extremes"
OTHER = "4 - Other Content"     # created by the program for fights missing from the catalog

# {parent folder: [fight folders]}
FIGHTS = {
    ULTIMATES: [
        "1. UCOB - The Unending Coil of Bahamut",
        "2. UWU - The Weapon's Refrain (Ultima Weapon)",
        "3. TEA - The Epic of Alexander",
        "4. DSR - Dragonsong's Reprise",
        "5. TOP - The Omega Protocol",
        "6. FRU - Futures Rewritten",
        "7. DMU - Dancing Mad",
    ],
    f"{SAVAGE}/2 - Heavensward/1 - Alexander Gordias": [
        "A1S - Oppressor", "A2S - Cuff of the Father", "A3S - Living Liquid",
        "A4S - The Manipulator"],
    f"{SAVAGE}/2 - Heavensward/2 - Alexander Midas": [
        "A5S - Ratfinx Twinkledinks", "A6S - Vortexer", "A7S - Quickthinx Allthoughts",
        "A8S - Brute Justice"],
    f"{SAVAGE}/2 - Heavensward/3 - Alexander The Creator": [
        "A9S - Refurbisher 0", "A10S - Lamebrix Strikebocks", "A11S - Cruise Chaser",
        "A12S - Alexander Prime"],
    f"{SAVAGE}/3 - Stormblood/1 - Deltascape": [
        "O1S - Alte Roite", "O2S - Catastrophe", "O3S - Halicarnassus",
        "O4S (1) - Exdeath", "O4S (2) - Neo Exdeath"],
    f"{SAVAGE}/3 - Stormblood/2 - Sigmascape": [
        "O5S - Phantom Train", "O6S - Demon Chadarnook", "O7S - Guardian",
        "O8S (1) - Kefka", "O8S (2) - God Kefka"],
    f"{SAVAGE}/3 - Stormblood/3 - Alphascape": [
        "O9S - Chaos", "O10S - Midgardsormr", "O11S - Omega",
        "O12S (1) - Omega-M and Omega-F", "O12S (2) - The Final Omega"],
    f"{SAVAGE}/4 - Shadowbringers/1 - Eden's Gate": [
        "E1S - Eden Prime", "E2S - Voidwalker", "E3S - Leviathan", "E4S - Titan"],
    f"{SAVAGE}/4 - Shadowbringers/2 - Eden's Verse": [
        "E5S - Ramuh", "E6S - Ifrit and Garuda", "E7S - The Idol of Darkness", "E8S - Shiva"],
    f"{SAVAGE}/4 - Shadowbringers/3 - Eden's Promise": [
        "E9S - Cloud of Darkness", "E10S - Shadowkeeper", "E11S - Fatebreaker",
        "E12S (1) - Eden's Promise", "E12S (2) - Oracle of Darkness"],
    f"{SAVAGE}/5 - Endwalker/1 - Asphodelos": [
        "P1S - Erichthonios", "P2S - Hippokampos", "P3S - Phoinix",
        "P4S (1) - Hesperos", "P4S (2) - Hesperos II"],
    f"{SAVAGE}/5 - Endwalker/2 - Abyssos": [
        "P5S - Proto-Carbuncle", "P6S - Hegemone", "P7S - Agdistis",
        "P8S (1) - Hephaistos", "P8S (2) - Hephaistos II"],
    f"{SAVAGE}/5 - Endwalker/3 - Anabaseis": [
        "P9S - Kokytos", "P10S - Pandaemonium", "P11S - Themis",
        "P12S (1) - Athena", "P12S (2) - Pallas Athena"],
    f"{SAVAGE}/6 - Dawntrail/1 - AAC Light-heavyweight": [
        "M1S - Black Cat", "M2S - Honey B. Lovely", "M3S - Brute Bomber", "M4S - Wicked Thunder"],
    f"{SAVAGE}/6 - Dawntrail/2 - AAC Cruiserweight": [
        "M5S - Dancing Green", "M6S - Sugar Riot", "M7S - Brute Abombinator",
        "M8S - Howling Blade"],
    f"{SAVAGE}/6 - Dawntrail/3 - AAC Heavyweight": [
        "M9S - Vamp Fatale", "M10S - Red Hot and Deep Blue", "M11S - The Tyrant",
        "M12S - Lindwurm"],
    f"{EXTREMES}/1 - A Realm Reborn": [
        "EX1 - Ifrit", "EX2 - Garuda", "EX3 - Titan", "EX4 - Leviathan", "EX5 - Ramuh",
        "EX6 - Good King Moggle Mog XII", "EX7 - Shiva", "EX8 - Ultima Weapon"],
    f"{EXTREMES}/2 - Heavensward": [
        "EX1 - Bismarck", "EX2 - Ravana", "EX3 - Thordan", "EX4 - Sephirot", "EX5 - Nidhogg",
        "EX6 - Sophia", "EX7 - Zurvan"],
    f"{EXTREMES}/3 - Stormblood": [
        "EX1 - Susano", "EX2 - Lakshmi", "EX3 - Shinryu", "EX4 - Byakko", "EX5 - Tsukuyomi",
        "EX6 - Suzaku", "EX7 - Seiryu"],
    f"{EXTREMES}/4 - Shadowbringers": [
        "EX1 - Titania", "EX2 - Innocence", "EX3 - Hades", "EX4 - Ruby Weapon",
        "EX5 - Varis yae Galvus", "EX6 - Warrior of Light", "EX7 - Emerald Weapon",
        "EX8 - Diamond Weapon"],
    f"{EXTREMES}/5 - Endwalker": [
        "EX1 - Zodiark", "EX2 - Hydaelyn", "EX3 - The Endsinger", "EX4 - Barbariccia",
        "EX5 - Rubicante", "EX6 - Golbez", "EX7 - Zeromus"],
    f"{EXTREMES}/6 - Dawntrail": [
        "EX1 - Valigarmanda", "EX2 - Zoraal Ja", "EX3 - Queen Eternal", "EX4 - Zelenia",
        "EX5 - Necron"],
}


def folders():
    """Every fight folder to create, as relative paths (plus the "Other Content" folder)."""
    return [OTHER] + [f"{parent}/{fight}" for parent, fights in FIGHTS.items() for fight in fights]
