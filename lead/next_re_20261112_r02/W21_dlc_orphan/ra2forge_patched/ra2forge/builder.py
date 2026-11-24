"""Compile a campaign design (design.py) into game-ready files.

Outputs (all inside <out>/<CampaignName>/):
  *.MAP                 mission maps, chained through [Basic] NextScenario
  BATTLEMD98.INI        appended campaign entry picked up by the engine's
                        BATTLEMD*.INI filesystem wildcard (the official
                        BATTLEMD.INI is never written to - see below)
  expandmd98.mix        map archive (maps only; never any INI)
  BUILD_REPORT.txt      build log: chain, artifacts, sha256, self-check results
  story.md              human-readable storyline dump
  INSTALL.txt           manual install / uninstall notes

Packaging contract (FORGE-1 plan B):
- The engine loads the battle lists with FindFirstFileA("BATTLEMD*.INI")
  (VA 0x52CBA0 -> IAT 0x7E1208) and merges what it finds by battle id
  (0x46CE10). That wildcard only ever sees *loose* files in the game
  directory, so a BATTLEMD*.INI packed inside a MIX is dead code - the package
  therefore ships the INI loose and keeps expandmd98.mix free of INI files.
- Because entries merge by id, re-using ALL1/SOV1 would override the official
  campaign entry in a directory-order-dependent way. The generated file
  therefore uses its own id (default "RA2F1", overridable through the optional
  design field campaign.id) and only *appends* a campaign.
- Description is the campaign-level blurb from campaign.description (R3) and
  the mission that ends the campaign is written EndOfGame=yes (R5).
- Install/uninstall live in ra2forge.install (per-file backups + manifest +
  exact restore).

Usage:
  python -m ra2forge build --design X --out out [--install <game dir>]
"""

from __future__ import annotations

import hashlib
import re
from pathlib import Path

from . import design as design_mod
from .maplib import MissionMap, STANDARD_HOUSES, read_basic_section
from . import triggers as tg
from .mixlib import MixFile, crc_hash, write_mix

HOUSE_INDEX = design_mod.HOUSE_INDEX
SIDES = design_mod.SIDES

BATTLE_FILE_NAME = "BATTLEMD98.INI"   # loose file matching BATTLEMD*.INI on the FS
MIX_FILE_NAME = "expandmd98.mix"
# the official battlemd.ini numbers its [Battles] list 1..14 (RA2 ships the
# ALL02..SOV07 debug placeholders); a fresh index keeps the two lists apart.
# R1 keeps FORGE-1's "never occupy an official index" strategy: we append at 15
# with our own entry id (default RA2F1) instead of rewriting an official entry.
BATTLE_INDEX = 15


class BuildError(RuntimeError):
    """Raised when a build self-check fails (e.g. the NextScenario chain)."""


def build(design: dict, out_dir: str | Path) -> Path:
    """Compile design into <out_dir>/<CampaignName>/ and return the MIX path.

    Self-checks (hard failures, not warnings):
      1. every written .MAP is read back from disk and its [Basic] NextScenario
         must match the design's mission order;
      2. the written MIX must contain exactly the map files and no INI.
    """
    warnings = design_mod.validate(design)
    camp = design["campaign"]
    missions = design["missions"]

    out = Path(out_dir) / _fs_safe(camp["name"])
    out.mkdir(parents=True, exist_ok=True)

    story: list[str] = [f"# {camp['name']}", ""]
    if camp.get("description"):
        story += [camp["description"], ""]

    # --- 1. compile every mission, chaining NextScenario in design order ---
    chain = mission_chain(missions)
    compiled: list[tuple[str, MissionMap]] = []
    for i, m in enumerate(missions):
        mmap, mission_warnings = _build_mission(m, i, design)
        mmap.next_scenario = chain[i]
        # R5: the mission that ends the campaign carries EndOfGame=yes (same
        # convention as the official final missions)
        mmap.end_of_game = not chain[i]
        compiled.append((f"{m['name'].upper()}.MAP", mmap))
        story.append(f"## Mission {i + 1}: {m.get('title', m['name'])}")
        story.append("")
        if m.get("briefing"):
            story.append(m["briefing"])
            story.append("")
        for w in mission_warnings:
            warnings.append(f"{m['name']}: {w}")

    map_texts: dict[str, str] = {}
    for map_name, mmap in compiled:
        text = mmap.to_ini_text()
        map_texts[map_name] = text
        _write_map_file(out / map_name, text)

    # --- 2. P0 self-check: read the maps back from disk, verify the chain ---
    check_lines = _verify_next_scenario_chain(out, compiled, chain)

    # --- 3. campaign registry: a loose, additive BATTLEMD98.INI -----------
    battle_id = battle_id_for(camp)
    _write_map_file(out / BATTLE_FILE_NAME, _battle_ini(camp, missions, battle_id))
    check_lines.extend(_verify_battle_file(out, camp, missions, battle_id))

    # --- 4. MIX carries maps only (no INI may ever end up in it) ----------
    mix_files = {name: text.encode("gbk", errors="replace")
                 for name, text in map_texts.items()}
    mix_path = write_mix(out / MIX_FILE_NAME, mix_files, include_database=False)
    check_lines.append(_verify_mix_contents(mix_path, sorted(mix_files)))

    (out / "story.md").write_text("\n".join(story) + "\n", encoding="utf-8")
    _write_build_report(out, camp, compiled, chain, battle_id, check_lines)
    _write_install_readme(out, len(missions))
    return mix_path


# ---------------------------------------------------------------------------
# campaign chain
# ---------------------------------------------------------------------------

def mission_chain(missions: list[dict]) -> list[str]:
    """Map file each mission must point at through [Basic] NextScenario.

    Default: the next mission in the design order; the last mission ends the
    campaign (empty value). A mission may override the default with an explicit
    "next": "<mission name>" entry (or "next": "" to stop the chain there).
    """
    names = [f"{m['name'].upper()}.MAP" for m in missions]
    by_lower = {str(m["name"]).lower(): f"{m['name'].upper()}.MAP" for m in missions}
    chain: list[str] = []
    for i, m in enumerate(missions):
        if "next" in m:
            raw = str(m.get("next") or "").strip()
            chain.append(by_lower[raw.lower()] if raw else "")
        elif i + 1 < len(names):
            chain.append(names[i + 1])
        else:
            chain.append("")
    return chain


def _verify_next_scenario_chain(out: Path, compiled, chain) -> list[str]:
    """Read every written .MAP back and assert its [Basic] NextScenario.

    An empty NextScenario on a non-final mission is the FORGE-1 P0 breakage
    (all three demo missions were written without a link), so this is a hard
    failure - never a warning.
    """
    lines: list[str] = []
    map_names = {name.upper() for name, _ in compiled}
    for (map_name, _mmap), expected in zip(compiled, chain):
        path = out / map_name
        if not path.is_file():
            raise BuildError(f"{map_name}: map file missing at {path}")
        text = path.read_bytes().decode("gbk", errors="replace")
        basic = read_basic_section(text)
        if "NextScenario" not in basic:
            raise BuildError(f"{map_name}: [Basic] has no NextScenario key")
        got = basic["NextScenario"].strip()
        if got.upper() != expected.upper():
            raise BuildError(
                f"{map_name}: [Basic] NextScenario={got!r} but the design order "
                f"requires {expected!r} (chain self-check failed)")
        # R5: the campaign-ending mission must carry EndOfGame=yes, every other
        # mission EndOfGame=no (official convention: the last mission of a
        # campaign sets it, e.g. extracted/yr_maps/map_133A0CB2.map:267)
        want_eog = "no" if expected else "yes"
        eog = basic.get("EndOfGame", "").strip().lower()
        if eog != want_eog:
            raise BuildError(
                f"{map_name}: [Basic] EndOfGame={eog!r} but "
                f"EndOfGame={want_eog} is required (R5 self-check failed)")
        if expected:
            if got.upper() not in map_names:
                raise BuildError(
                    f"{map_name}: NextScenario={got!r} is not a map of this "
                    f"campaign {sorted(map_names)}")
            lines.append(f"  [PASS] {map_name}: [Basic] NextScenario={got} -> "
                         f"chained, EndOfGame={eog}")
        else:
            lines.append(f"  [PASS] {map_name}: [Basic] NextScenario= (empty) -> "
                         f"campaign ends here, EndOfGame={eog}")
    return lines


def _verify_battle_file(out: Path, camp: dict, missions: list[dict],
                        battle_id: str) -> list[str]:
    """Read the written BATTLEMD98.INI back and assert the appended entry (R1/R3).

    Checks on the bytes that actually landed on disk: the [Battles] index maps to
    our own battle id, that id's section starts the campaign at the first map and
    carries the campaign-level description from the design file, and no official
    entry name is present anywhere in the file.
    """
    path = out / BATTLE_FILE_NAME
    if not path.is_file():
        raise BuildError(f"{BATTLE_FILE_NAME}: file missing at {path}")
    text = path.read_bytes().decode("gbk", errors="replace")
    sections = _parse_ini(text)
    battles = sections.get("Battles", {})
    entry = sections.get(battle_id, {})
    if battles.get(str(BATTLE_INDEX)) != battle_id:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: [Battles] {BATTLE_INDEX}="
            f"{battles.get(str(BATTLE_INDEX))!r}, expected {battle_id!r}")
    if not entry:
        raise BuildError(f"{BATTLE_FILE_NAME}: section [{battle_id}] is missing")
    first_map = f"{missions[0]['name'].upper()}.MAP"
    if entry.get("Scenario", "").upper() != first_map:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: [{battle_id}] Scenario={entry.get('Scenario')!r}, "
            f"expected {first_map!r}")
    want_desc = design_mod.description_for(camp) or str(camp["name"]).strip()
    if entry.get("Description", "") != want_desc:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: [{battle_id}] Description="
            f"{entry.get('Description')!r}, expected the design's campaign "
            f"description {want_desc!r}")
    overrides = sorted(s for s in sections
                       if design_mod.OFFICIAL_BATTLE_ID_RE.match(s))
    if overrides:
        raise BuildError(
            f"{BATTLE_FILE_NAME}: official entry name(s) {overrides} must never "
            f"appear - the file may only append our own campaign")
    return [
        f"  [PASS] {BATTLE_FILE_NAME}: [Battles] {BATTLE_INDEX}={battle_id} -> "
        f"{first_map} (append; official BATTLEMD.INI untouched)",
        f"  [PASS] {BATTLE_FILE_NAME}: [{battle_id}] read back from disk "
        f"(Scenario={entry['Scenario']}, Description={entry['Description'][:40]!r}"
        f"{'...' if len(entry['Description']) > 40 else ''})",
        f"  [PASS] {BATTLE_FILE_NAME}: no official entry name "
        f"(no [ALL1]/[SOV1]/[ALL02]..[SOV07])",
    ]


def _parse_ini(text: str) -> dict[str, dict[str, str]]:
    """Minimal INI reader (sections -> key/value), used by the self-check."""
    sections: dict[str, dict[str, str]] = {}
    current: str | None = None
    for raw in text.splitlines():
        line = raw.strip()
        if not line or line.startswith(";"):
            continue
        if line.startswith("[") and line.endswith("]"):
            current = line[1:-1]
            sections.setdefault(current, {})
            continue
        if current is not None and "=" in line:
            key, _, value = line.partition("=")
            sections[current][key.strip()] = value.strip()
    return sections


def _verify_mix_contents(mix_path: Path, expected_names: list[str]) -> str:
    """Re-open the written MIX and assert it holds exactly the map files."""
    if any(n.upper().endswith(".INI") for n in expected_names):
        raise BuildError(
            f"refusing to pack INI files into {mix_path.name}: {expected_names}")
    want = {crc_hash(n) for n in expected_names}
    with MixFile(mix_path) as mix:
        got = {e.id for e in mix.all_entries()}
    if got != want:
        raise BuildError(
            f"{mix_path.name} entries {sorted(f'{i:08X}' for i in got)} != expected "
            f"{sorted(f'{i:08X}' for i in want)}")
    return (f"  [PASS] {mix_path.name}: {len(got)} entries, 0 INI "
            f"({', '.join(expected_names)})")


# ---------------------------------------------------------------------------
# battle registry
# ---------------------------------------------------------------------------

def battle_id_for(campaign) -> str:
    """Battle id for the appended campaign entry (R1).

    Accepts the campaign dict and delegates to design.campaign_battle_id: the
    optional `campaign.id` field wins, otherwise the stable default RA2F1.
    (A bare name string is tolerated and yields the default: since FORGE-2 the id
    no longer derives from the campaign name - a name hash made every campaign
    register under a different id, which the user ruling replaced with the fixed
    RA2F1 entry.)
    """
    if isinstance(campaign, str):
        return design_mod.DEFAULT_BATTLE_ID
    return design_mod.campaign_battle_id(campaign)


def _battle_ini(camp: dict, missions: list[dict], battle_id: str) -> str:
    # R3: the Description shown in the campaign list is the campaign-level blurb
    # from the design file (campaign.description) - never a hard coded string and
    # never a "DESC:xxx" CSF label. It falls back to the campaign name only when
    # the design omits the field (design.validate warns about that).
    desc = design_mod.description_for(camp) or str(camp["name"]).strip()
    lines = [
        "; Generated by RA2 Campaign Forge - APPENDED campaign entry.",
        "; The game scans the GAME DIRECTORY for BATTLEMD*.INI and merges the",
        "; entries by battle id, so this file only ADDS a campaign; the official",
        "; BATTLEMD.INI is left untouched. Delete this file to unregister.",
        "[Battles]",
        f"{BATTLE_INDEX}={battle_id}",
        "",
        f"[{battle_id}]",
        "CD=2",
        f"Scenario={missions[0]['name'].upper()}.MAP",
        "FinalMovie=",
        f"Description={desc}",
    ]
    return "\n".join(lines) + "\n"


# ---------------------------------------------------------------------------
# mission compilation
# ---------------------------------------------------------------------------

def _build_mission(m: dict, index: int, design: dict) -> tuple[MissionMap, list[str]]:
    warnings: list[str] = []
    size = m.get("size", [90, 90])
    theater = str(m.get("theater", "TEMPERATE")).upper()
    mmap = MissionMap(m["name"], width=size[0], height=size[1], theater=theater)

    side = str(design["campaign"].get("side", "soviet")).lower()
    player_house = str((m.get("player") or {}).get("house") or SIDES[side])
    mmap.player_house = player_house
    mmap.basic["briefing"] = _sanitize_briefing(m.get("briefing", ""))
    mmap.name = str(m.get("title") or m["name"])

    # per-house configuration - the game picks the player by PlayerControl=yes
    # (mirror of official campaign maps like SOV01UMD.MAP)
    enemies = list(dict.fromkeys(
        [str(o["enemy"]) for o in m.get("objectives", [])
         if o.get("type") in ("destroy_all_forces", "destroy_all_buildings")]
        + [str(o["house"]) for o in m.get("objectives", [])
           if o.get("type") == "hunt_wave"]
        + [str(o.get("team", {}).get("house")) for o in m.get("objectives", [])
           if o.get("type") == "reinforce" and o.get("team", {}).get("house")
           and o["team"]["house"] != player_house]))
    player_color = {"soviet": "DarkRed", "allied": "DarkBlue", "yuri": "Gold"}.get(
        side, "DarkRed")
    enemy_colors = ["DarkBlue", "DarkRed", "Gold", "Green", "Orange", "Purple"]
    house_configs = [{
        "name": player_house,
        "player": True,
        "credits": int((m.get("player") or {}).get("credits", 0)),
        "color": player_color,
        "edge": "South",
        "allies": player_house,
        "iq": 0,
    }]
    for j, enemy in enumerate(enemies):
        color = enemy_colors[j % len(enemy_colors)]
        if color == player_color:
            color = enemy_colors[(j + 1) % len(enemy_colors)]
        house_configs.append({
            "name": enemy,
            "player": False,
            "credits": int((m.get("player") or {}).get("enemy_credits", 0)),
            "color": color,
            "edge": "North",
            "allies": ", ".join(enemies),
            "iq": 2,
        })
    mmap.house_configs = house_configs

    tid_gen = _hex_id_gen(0x0B000000 + index * 0x10000)
    tag_gen = _hex_id_gen(0x0C000000 + index * 0x10000)

    # waypoints
    for wp_id, pos in (m.get("waypoints") or {}).items():
        mmap.add_waypoint(int(wp_id), int(pos[0]), int(pos[1]))

    # water
    for wrect in m.get("water", []):
        mmap.add_water_rect(int(wrect["row0"]), int(wrect["col0"]),
                            int(wrect["row1"]), int(wrect["col1"]))

    # scenery: forests, civilian structures, neutral cars, battle smudges
    scenery = m.get("scenery") or {}
    for trect in scenery.get("tree_rects", []):
        mmap.scatter_trees(int(trect["row0"]), int(trect["col0"]),
                           int(trect["row1"]), int(trect["col1"]),
                           density=float(trect.get("density", 0.08)),
                           seed=int(trect.get("seed", 0)))
    for civ in scenery.get("civilians", []):
        mmap.add_structure(str(civ.get("owner", "Neutral")), str(civ["type"]).upper(),
                           int(civ["row"]), int(civ["col"]),
                           health=int(civ.get("health", 256)),
                           sellable=0, rebuildable=0, repairable=0, nominal=0)
    for car in scenery.get("cars", []):
        mmap.add_unit(str(car.get("owner", "Neutral")), str(car["type"]).upper(),
                      int(car["row"]), int(car["col"]), mission="Sleep")
    for sm in scenery.get("smudges", []):
        mmap.add_smudge(int(sm["row"]), int(sm["col"]), str(sm["type"]).upper())

    # objects
    design_tag_to_tagid: dict[str, str] = {}
    for s in m.get("structures", []):
        if s.get("tag"):
            design_tag_to_tagid[str(s["tag"])] = None
    for design_tag in design_tag_to_tagid:
        design_tag_to_tagid[design_tag] = next(tag_gen)
    for s in m.get("structures", []):
        mmap.add_structure(str(s["owner"]), str(s["type"]).upper(),
                           int(s["row"]), int(s["col"]),
                           health=int(s.get("health", 256)),
                           tag=design_tag_to_tagid.get(str(s.get("tag", "")), "None"))
    for u in m.get("units", []):
        mmap.add_unit(str(u["owner"]), str(u["type"]).upper(),
                      int(u["row"]), int(u["col"]),
                      health=int(u.get("health", 256)),
                      mission=str(u.get("mission", "Guard")))
    for inf in m.get("infantry", []):
        mmap.add_infantry(str(inf["owner"]), str(inf["type"]).upper(),
                          int(inf["row"]), int(inf["col"]),
                          health=int(inf.get("health", 256)),
                          mission=str(inf.get("mission", "Guard")))

    # --- triggers ---------------------------------------------------------
    player_idx = HOUSE_INDEX[player_house]
    mission_triggers: list[dict] = []

    # lose trigger: player loses everything
    mission_triggers.append(tg.make_trigger(
        next(tid_gen), next(tag_gen), player_house, "Defeat",
        [tg.ev_all_destroyed(player_idx)],
        [tg.act_loser(player_idx)],
        tag_name="Defeat"))

    # objectives: win-type objectives chain; event-only objectives are freestanding
    win_objs = [o for o in m.get("objectives", [])
                if o["type"] in ("destroy_all_forces", "destroy_all_buildings",
                                 "destroy_building", "survive")]
    event_objs = [o for o in m.get("objectives", [])
                  if o["type"] in design_mod.EVENT_ONLY_OBJECTIVES]

    win_triggers: list[dict] = []
    for o in win_objs:
        otype = o["type"]
        if otype == "destroy_all_forces":
            enemy = str(o["enemy"])
            win_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Objective: destroy {enemy}",
                [tg.ev_all_destroyed(HOUSE_INDEX[enemy])], [],
                tag_name=f"Destroy {enemy}"))
        elif otype == "destroy_all_buildings":
            enemy = str(o["enemy"])
            win_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Objective: raze {enemy}",
                [tg.ev_all_buildings_destroyed(HOUSE_INDEX[enemy])], [],
                tag_name=f"Raze {enemy}"))
        elif otype == "destroy_building":
            tag_id = design_tag_to_tagid[str(o["structure_tag"])]
            win_triggers.append(tg.make_trigger(
                next(tid_gen), tag_id, player_house,
                "Objective: destroy target",
                [tg.ev_destroyed_by_any()], [],
                tag_name=f"Destroy target {o['structure_tag']}"))
        elif otype == "survive":
            win_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Objective: survive {o['seconds']}s",
                [tg.ev_elapsed_time(int(o["seconds"]))], [],
                tag_name=f"Survive {o['seconds']}"))

    # chain win objectives: each enables the next, last declares victory
    if win_triggers:
        for j, trig in enumerate(win_triggers):
            if j + 1 < len(win_triggers):
                trig["disabled"] = 1 if j > 0 else 0
                trig["actions"] = [tg.act_enable_trigger(win_triggers[j + 1]["id"])]
            else:
                trig["actions"] = [tg.act_winner(player_idx)]
        mission_triggers.extend(win_triggers)
    else:
        warnings.append("no win objective - mission can only be lost; "
                        "add destroy_all_forces/survive/destroy_building")

    if len(m.get("objectives", [])) != len(win_objs) + len(event_objs):
        warnings.append("some objectives were not compiled - check objective types")

    # event-only objectives (reinforce/text/speech/timer/reveal/hunt)
    for o in event_objs:
        at = int(o.get("at_second", 0))
        events = [tg.ev_elapsed_time(at)] if at > 0 else [(0, (0, 0))]
        otype = o["type"]
        if otype == "text":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Message",
                events, [tg.act_text(str(o["text"]))], tag_name="Message"))
        elif otype == "speech":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "EVA",
                events, [tg.act_speech(str(o["eva"]))], tag_name="EVA"))
        elif otype == "timer":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Timer",
                events, [tg.act_timer_set(int(o["seconds"])), tg.act_timer_start()],
                tag_name="Timer"))
        elif otype == "reveal_map":
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Reveal",
                events, [tg.act_reveal_all()], tag_name="Reveal"))
        elif otype == "reveal_waypoint":
            wp_id = int(o["waypoint"])
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Recon",
                events, [tg.act_reveal_waypoint(wp_id)], tag_name="Recon"))
        elif otype == "hunt_wave":
            enemy = str(o["house"])
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house,
                f"Enemy assault ({enemy})",
                events, [tg.act_all_to_hunt(HOUSE_INDEX[enemy])],
                tag_name=f"Hunt {enemy}"))
        elif otype == "reinforce":
            team = o["team"]
            team_id = str(team["id"]).upper()
            house = str(team.get("house", player_house))
            entries = [(int(e["count"]), str(e["type"]).upper())
                       for e in team.get("units", [])]
            wp_letter = str(o.get("at_waypoint", "")).upper()
            if wp_letter and len(wp_letter) == 1 and wp_letter.isalpha():
                wp_id = ord(wp_letter) - ord("A")
                if wp_id not in mmap.waypoints:
                    mmap.add_waypoint(wp_id, int(team.get("row", size[1] // 2)),
                                      int(team.get("col", size[0] // 2)))
                mmap.add_reinforcement_team(team_id, house, entries,
                                            waypoint_letter=wp_letter)
                action = tg.act_reinforce_at_waypoint(team_id, wp_letter)
            else:
                mmap.add_reinforcement_team(team_id, house, entries)
                action = tg.act_reinforce(team_id)
            mission_triggers.append(tg.make_trigger(
                next(tid_gen), next(tag_gen), player_house, "Reinforcement",
                events, [action], tag_name="Reinforcement"))

    for t in mission_triggers:
        mmap.add_trigger(t)
    return mmap, warnings


def _hex_id_gen(start: int):
    val = start
    while True:
        yield f"{val:08X}"
        val += 0x1C


def _sanitize_briefing(text: str) -> str:
    # briefings are single-line INI values; use '@' as paragraph separator
    return re.sub(r"[\r\n]+", "@@", str(text)).strip()


def _fs_safe(name: str) -> str:
    # NTFS handles CJK fine; only strip characters Windows forbids in filenames
    return re.sub(r'[\\/:*?"<>|]', "_", name).strip()[:80] or "campaign"


def _write_map_file(path: Path, text: str):
    # the game reads INI-style files as ANSI in the system code page;
    # Chinese installs expect GBK (cp936), a strict superset of ASCII
    data = text.encode("gbk", errors="replace")
    with open(path, "wb") as f:
        f.write(data)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _artifact_line(path: Path) -> str:
    return (f"  {path.name}  {path.stat().st_size} bytes  "
            f"sha256={_sha256(path)[:16]}")


def _write_build_report(out: Path, camp: dict, compiled, chain, battle_id: str,
                        check_lines: list[str]) -> Path:
    lines = [
        "RA2 Campaign Forge - build report",
        f"campaign={camp['name']}",
        f"side={str(camp.get('side', 'soviet')).lower()}",
        f"battle_file={BATTLE_FILE_NAME} (loose, appended entry)",
        f"battle_id={battle_id}",
        f"battle_id_source={'campaign.id' if camp.get('id') else 'default RA2F1'}",
        f"battle_index={BATTLE_INDEX}",
        f"description={design_mod.description_for(camp) or camp['name']}",
        f"first_scenario={compiled[0][0]}",
        f"mix={MIX_FILE_NAME} (maps only)",
        "",
        "NextScenario chain:",
    ]
    for (map_name, mmap), nxt in zip(compiled, chain):
        lines.append(f"  {map_name}  title={mmap.name}  "
                     f"next={nxt or '<campaign end>'}  "
                     f"end_of_game={'yes' if mmap.end_of_game else 'no'}")
    lines += ["", "self-checks:", *check_lines, "", "artifacts:"]
    for map_name, _ in compiled:
        lines.append(_artifact_line(out / map_name))
    lines.append(_artifact_line(out / BATTLE_FILE_NAME))
    lines.append(_artifact_line(out / MIX_FILE_NAME))
    lines.append(_artifact_line(out / "story.md"))
    lines.append("")
    report = out / "BUILD_REPORT.txt"
    report.write_text("\n".join(lines), encoding="utf-8")
    return report


def _write_install_readme(out: Path, mission_count: int):
    (out / "INSTALL.txt").write_text(
        "RA2 Campaign Forge - install instructions\r\n"
        "=========================================\r\n\r\n"
        f"This package contains {mission_count} chained mission(s).\r\n\r\n"
        "Automatic install (recommended - backs up and can restore):\r\n"
        "  python -m ra2forge build --design <design.json> --out out "
        "--install \"<game dir>\"\r\n"
        "  python -m ra2forge uninstall --game \"<game dir>\"\r\n\r\n"
        "Manual install:\r\n"
        "  1. Copy BATTLEMD98.INI, expandmd98.mix and every *.MAP into your\r\n"
        "     Red Alert 2 Yuri's Revenge directory (the folder with gamemd.exe).\r\n"
        "  2. Start the game -> New Campaign -> the campaign list gains one extra\r\n"
        "     entry (its Description is the campaign.description of the design\r\n"
        "     file); the official campaigns stay exactly as they were.\r\n"
        "  3. The last mission of the chain carries EndOfGame=yes; delete that line\r\n"
        "     if a real playthrough shows the campaign ending early.\r\n\r\n"
        "Why BATTLEMD98.INI must stay a loose file:\r\n"
        "  the engine enumerates the battle lists with "
        "FindFirstFileA(\"BATTLEMD*.INI\")\r\n"
        "  in the GAME DIRECTORY and merges them by battle id. A file inside a MIX\r\n"
        "  is never seen by that wildcard, so the registration cannot live in the\r\n"
        "  archive (and nothing else may be packed there either - maps only).\r\n\r\n"
        "Files:\r\n"
        "  *.MAP             mission maps (YR .map format, playable standalone too)\r\n"
        "  BATTLEMD98.INI    appended campaign entry (delete it to unregister)\r\n"
        "  expandmd98.mix    map archive (maps only - no INI inside)\r\n"
        "  story.md          the storyline briefing for every mission\r\n"
        "  BUILD_REPORT.txt  build log: chain + artifact hashes + self-checks\r\n",
        encoding="ascii")
