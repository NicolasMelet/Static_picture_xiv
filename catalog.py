"""Folder tree of the background images: one folder per fight.

Naming convention (folders and files): lowercase, no spaces, no accents.
  - words are joined with "-":           futures-rewritten, aac-heavyweight
  - "_" separates prefixes from the name: <order>_<name> or <code>_<name>
  - the part after the last "_" is the fight's FFLogs name: it identifies the folder
  - phase images are files named <anything>-p<n>: fru-p1.png, lindwurm-p2.jpg
"""

ULTIMATES = "1_ultimates"
SAVAGE = "2_savage-raids"
EXTREMES = "3_extremes"
OTHER = "4_other-content"     # created by the program for fights missing from the catalog

# {parent folder: [fight folders]}
FIGHTS = {
    ULTIMATES: [
        "1_ucob_the-unending-coil-of-bahamut",
        "2_uwu_the-weapons-refrain-ultima-weapon",
        "3_tea_the-epic-of-alexander",
        "4_dsr_dragonsongs-reprise",
        "5_top_the-omega-protocol",
        "6_fru_futures-rewritten",
        "7_dmu_dancing-mad",
    ],
    f"{SAVAGE}/2_heavensward/1_alexander-gordias": [
        "a1s_oppressor", "a2s_cuff-of-the-father", "a3s_living-liquid", "a4s_the-manipulator"],
    f"{SAVAGE}/2_heavensward/2_alexander-midas": [
        "a5s_ratfinx-twinkledinks", "a6s_vortexer", "a7s_quickthinx-allthoughts",
        "a8s_brute-justice"],
    f"{SAVAGE}/2_heavensward/3_alexander-the-creator": [
        "a9s_refurbisher-0", "a10s_lamebrix-strikebocks", "a11s_cruise-chaser",
        "a12s_alexander-prime"],
    f"{SAVAGE}/3_stormblood/1_deltascape": [
        "o1s_alte-roite", "o2s_catastrophe", "o3s_halicarnassus",
        "o4s-1_exdeath", "o4s-2_neo-exdeath"],
    f"{SAVAGE}/3_stormblood/2_sigmascape": [
        "o5s_phantom-train", "o6s_demon-chadarnook", "o7s_guardian",
        "o8s-1_kefka", "o8s-2_god-kefka"],
    f"{SAVAGE}/3_stormblood/3_alphascape": [
        "o9s_chaos", "o10s_midgardsormr", "o11s_omega",
        "o12s-1_omega-m-and-omega-f", "o12s-2_the-final-omega"],
    f"{SAVAGE}/4_shadowbringers/1_edens-gate": [
        "e1s_eden-prime", "e2s_voidwalker", "e3s_leviathan", "e4s_titan"],
    f"{SAVAGE}/4_shadowbringers/2_edens-verse": [
        "e5s_ramuh", "e6s_ifrit-and-garuda", "e7s_the-idol-of-darkness", "e8s_shiva"],
    f"{SAVAGE}/4_shadowbringers/3_edens-promise": [
        "e9s_cloud-of-darkness", "e10s_shadowkeeper", "e11s_fatebreaker",
        "e12s-1_edens-promise", "e12s-2_oracle-of-darkness"],
    f"{SAVAGE}/5_endwalker/1_asphodelos": [
        "p1s_erichthonios", "p2s_hippokampos", "p3s_phoinix",
        "p4s-1_hesperos", "p4s-2_hesperos-ii"],
    f"{SAVAGE}/5_endwalker/2_abyssos": [
        "p5s_proto-carbuncle", "p6s_hegemone", "p7s_agdistis",
        "p8s-1_hephaistos", "p8s-2_hephaistos-ii"],
    f"{SAVAGE}/5_endwalker/3_anabaseis": [
        "p9s_kokytos", "p10s_pandaemonium", "p11s_themis",
        "p12s-1_athena", "p12s-2_pallas-athena"],
    f"{SAVAGE}/6_dawntrail/1_aac-light-heavyweight": [
        "m1s_black-cat", "m2s_honey-b-lovely", "m3s_brute-bomber", "m4s_wicked-thunder"],
    f"{SAVAGE}/6_dawntrail/2_aac-cruiserweight": [
        "m5s_dancing-green", "m6s_sugar-riot", "m7s_brute-abombinator", "m8s_howling-blade"],
    f"{SAVAGE}/6_dawntrail/3_aac-heavyweight": [
        "m9s_vamp-fatale", "m10s_red-hot-and-deep-blue", "m11s_the-tyrant", "m12s_lindwurm"],
    f"{EXTREMES}/1_a-realm-reborn": [
        "ex1_ifrit", "ex2_garuda", "ex3_titan", "ex4_leviathan", "ex5_ramuh",
        "ex6_good-king-moggle-mog-xii", "ex7_shiva", "ex8_ultima-weapon"],
    f"{EXTREMES}/2_heavensward": [
        "ex1_bismarck", "ex2_ravana", "ex3_thordan", "ex4_sephirot", "ex5_nidhogg",
        "ex6_sophia", "ex7_zurvan"],
    f"{EXTREMES}/3_stormblood": [
        "ex1_susano", "ex2_lakshmi", "ex3_shinryu", "ex4_byakko", "ex5_tsukuyomi",
        "ex6_suzaku", "ex7_seiryu"],
    f"{EXTREMES}/4_shadowbringers": [
        "ex1_titania", "ex2_innocence", "ex3_hades", "ex4_ruby-weapon", "ex5_varis-yae-galvus",
        "ex6_warrior-of-light", "ex7_emerald-weapon", "ex8_diamond-weapon"],
    f"{EXTREMES}/5_endwalker": [
        "ex1_zodiark", "ex2_hydaelyn", "ex3_the-endsinger", "ex4_barbariccia", "ex5_rubicante",
        "ex6_golbez", "ex7_zeromus"],
    f"{EXTREMES}/6_dawntrail": [
        "ex1_valigarmanda", "ex2_zoraal-ja", "ex3_queen-eternal", "ex4_zelenia", "ex5_necron"],
}


def folders():
    """Every fight folder to create, as relative paths (plus the "other content" folder)."""
    return [OTHER] + [f"{parent}/{fight}" for parent, fights in FIGHTS.items() for fight in fights]
