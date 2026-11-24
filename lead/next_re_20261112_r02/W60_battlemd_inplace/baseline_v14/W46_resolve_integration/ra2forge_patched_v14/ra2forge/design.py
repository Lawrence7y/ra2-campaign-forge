"""Campaign design JSON schema + validation.

This is the AI-facing contract: an AI (or human) writes a design JSON
describing a full storyline campaign; `ra2forge.builder` compiles it into
game-ready files (mission .map files + loose BATTLEMD98.INI + expandmd98.mix).

Per-mission optional field:
  "next": "<mission name>"   -- override the NextScenario link (default: the
                                next mission in design order; "" ends the
                                campaign at this mission)

Per-campaign optional field (FORGE-2 / R1):
  "id": "RA2F1"              -- battle id of the appended BATTLEMD98.INI entry.
                                ASCII letter + letters/digits/underscore, 1..16
                                chars, must not be an official id (ALL1/SOV1/...).
                                Defaults to "RA2F1" when absent or empty.

See docs/DESIGN.md (or examples/demo_campaign.json) for a documented example.
"""

from __future__ import annotations

import re

from .maplib import STANDARD_HOUSES

HOUSE_INDEX = {name: i for i, name in enumerate(STANDARD_HOUSES)}

# Battle id of our appended BATTLEMD98.INI entry (R1: our own id, never an
# official one). Official ids in the shipped battlemd.ini are ALL1/SOV1 plus the
# ALL02..SOV07 debug placeholders.
DEFAULT_BATTLE_ID = "RA2F1"
BATTLE_ID_MAX_LEN = 16
OFFICIAL_BATTLE_ID_RE = re.compile(r"^(?:ALL|SOV)\d+$", re.IGNORECASE)


SIDES = {
    "soviet": "Russians",
    "allied": "Americans",
    "yuri": "YuriCountry",
}

OBJECTIVE_TYPES = {
    "destroy_all_forces",       # enemy: <country>
    "destroy_all_buildings",    # enemy: <country>
    "destroy_building",         # structure_tag: <tag attached to a structure>
    "survive",                  # seconds: <int>
    "reinforce",                # team: {...}, at_second: <int>, at_waypoint: "A"
    "text",                     # text: str, at_second: <int>
    "speech",                   # eva: str, at_second: <int>
    "timer",                    # seconds: <int> (sets+starts mission timer)
    "reveal_map",               # at_second: <int> (debug/故事用全图侦察)
    "reveal_waypoint",          # waypoint: <id>, at_second: <int>
    "hunt_wave",                # house: <country>, at_second: <int>
}

EVENT_ONLY_OBJECTIVES = {"reinforce", "text", "speech", "timer",
                         "reveal_map", "reveal_waypoint", "hunt_wave"}


class DesignError(ValueError):
    pass


def validate(design: dict) -> list[str]:
    """Validate a campaign design dict; raises DesignError on fatal problems,
    returns a list of warnings otherwise."""
    warnings: list[str] = []
    if not isinstance(design, dict):
        raise DesignError("design must be a JSON object")
    camp = design.get("campaign") or {}
    if not camp.get("name"):
        raise DesignError("campaign.name is required")
    missions = design.get("missions") or []
    if not missions:
        raise DesignError("campaign needs at least one mission")

    side = str(camp.get("side", "soviet")).lower()
    if side not in SIDES:
        raise DesignError(f"campaign.side must be one of {sorted(SIDES)}")

    # R1: optional campaign.id -> the [<id>] section of the appended entry
    campaign_battle_id(camp)
    if not description_for(camp):
        warnings.append(
            "campaign.description is empty — the campaign entry in "
            "BATTLEMD98.INI falls back to campaign.name (R3 wants a "
            "campaign-level blurb shown in the mission-select list)")

    seen_names = set()
    team_ids: set[str] = set()
    for i, m in enumerate(missions):
        prefix = f"missions[{i}]"
        name = str(m.get("name", "")).strip()
        if not name or not _is_ascii_identifier(name):
            raise DesignError(
                f"{prefix}.name must be a non-empty ASCII identifier "
                f"(letters/digits/underscore), got {name!r}")
        if name.lower() in seen_names:
            raise DesignError(f"duplicate mission name {name!r}")
        seen_names.add(name.lower())
        if "next" in m:
            # optional override of the default "next mission in design order"
            nxt = m.get("next")
            if not isinstance(nxt, str):
                raise DesignError(
                    f"{prefix}.next must be a mission name string "
                    f"(use \"\" to end the campaign here), got {nxt!r}")
            if nxt.strip() and nxt.strip().lower() == name.lower():
                raise DesignError(f"{prefix}.next must not point at the mission itself")
        if not m.get("title"):
            warnings.append(f"{prefix}: no title — campaign entry will fall back to name")
        if not m.get("briefing"):
            warnings.append(f"{prefix}: no briefing — mission starts without text")

        size = m.get("size", [90, 90])
        if (not isinstance(size, list) or len(size) != 2
                or not all(isinstance(v, int) and 40 <= v <= 200 for v in size)
                or size[0] % 2 or size[1] % 2):
            raise DesignError(f"{prefix}.size must be [even int, even int] in 40..200")
        if size[0] != size[1]:
            raise DesignError(f"{prefix}.size must be square (e.g. [90, 90])")

        player = m.get("player") or {}
        house = str(player.get("house", "")).strip()
        if house and house not in HOUSE_INDEX:
            raise DesignError(
                f"{prefix}.player.house {house!r} unknown; use one of {STANDARD_HOUSES}")
        for owner_check, label in _owners(m):
            if owner_check not in HOUSE_INDEX:
                raise DesignError(
                    f"{prefix}: unknown owner {owner_check!r} in {label}; "
                    f"use one of {STANDARD_HOUSES}")

        tags = set()
        for s in m.get("structures", []):
            tag = s.get("tag")
            if tag and tag != "None":
                if not _is_ascii_identifier(tag):
                    raise DesignError(f"{prefix}: structure tag {tag!r} must be ASCII identifier")
                tags.add(tag)
        for obj in m.get("objectives", []):
            otype = obj.get("type")
            if otype not in OBJECTIVE_TYPES:
                raise DesignError(
                    f"{prefix}: objective.type must be one of {sorted(OBJECTIVE_TYPES)}")
            if otype == "destroy_building" and obj.get("structure_tag") not in tags:
                raise DesignError(
                    f"{prefix}: objective destroy_building references tag "
                    f"{obj.get('structure_tag')!r} but no structure carries it")
            if otype in ("destroy_all_forces", "destroy_all_buildings"):
                if obj.get("enemy") not in HOUSE_INDEX:
                    raise DesignError(f"{prefix}: objective {otype} needs a valid enemy house")
            if otype == "survive" and not (0 < int(obj.get("seconds", 0)) <= 36000):
                raise DesignError(f"{prefix}: survive needs seconds in 1..36000")
            team = obj.get("team") or {}
            if team:
                tid = team.get("id", "")
                if not _is_hex_id(tid):
                    raise DesignError(
                        f"{prefix}: reinforce team.id must be exactly 8 hex chars "
                        f"(e.g. '0A110001'), got {tid!r}")
                if tid in team_ids:
                    raise DesignError(f"{prefix}: duplicate team id {tid!r}")
                team_ids.add(tid)

        wps = m.get("waypoints") or {}
        for wp_id, pos in wps.items():
            try:
                wid = int(wp_id)
                r, c = pos
            except Exception as exc:  # noqa: BLE001
                raise DesignError(f"{prefix}: bad waypoint {wp_id!r}") from exc
            if not (0 <= wid <= 98):
                raise DesignError(f"{prefix}: waypoint ids must be 0..98")
            if not (0 <= r < size[1] and 0 <= c < size[0]):
                raise DesignError(f"{prefix}: waypoint {wp_id} outside map")

        for s in m.get("scenery", {}).get("civilians", []):
            if str(s.get("owner", "Neutral")) not in HOUSE_INDEX:
                raise DesignError(f"{prefix}: civilian owner must be a valid house")

    # mission chain ([Basic] NextScenario): an explicit "next" must name a
    # mission of this campaign; the builder fills the default chain in order.
    for i, m in enumerate(missions):
        nxt = str(m.get("next", "") or "").strip()
        if nxt and nxt.lower() not in seen_names:
            raise DesignError(
                f"missions[{i}].next {nxt!r} does not name a mission of this campaign")
        if "next" in m and not nxt and i + 1 < len(missions):
            warnings.append(
                f"missions[{i}] ({m.get('name')}): next=\"\" ends the campaign "
                f"here although {len(missions) - i - 1} more mission(s) follow")

    return warnings


def _owners(m: dict):
    for s in m.get("structures", []):
        yield str(s.get("owner", "")), "structures"
    for u in m.get("units", []):
        yield str(u.get("owner", "")), "units"
    for inf in m.get("infantry", []):
        yield str(inf.get("owner", "")), "infantry"
    for obj in m.get("objectives", []):
        if obj.get("type") in ("destroy_all_forces", "destroy_all_buildings"):
            yield str(obj.get("enemy", "")), "objectives"


def _is_ascii_identifier(s: str) -> bool:
    return bool(s) and all(ch.isascii() and (ch.isalnum() or ch == "_") for ch in s)


def _is_hex_id(s: str) -> bool:
    return len(s) == 8 and all(ch in "0123456789ABCDEFabcdef" for ch in s)


def campaign_battle_id(camp: dict) -> str:
    """Battle id for the campaign's appended BATTLEMD98.INI entry (R1).

    A design may name its own id with the optional `campaign.id` field; without
    it the entry uses DEFAULT_BATTLE_ID. Official ids are rejected: entries from
    every BATTLEMD*.INI are merged by battle id, so re-using ALL1/SOV1 would
    override an official campaign entry instead of adding one.
    """
    raw = camp.get("id")
    if raw is None or (isinstance(raw, str) and not raw.strip()):
        return DEFAULT_BATTLE_ID
    if not isinstance(raw, str):
        raise DesignError(f"campaign.id must be a string, got {raw!r}")
    bid = raw.strip()
    if not 1 <= len(bid) <= BATTLE_ID_MAX_LEN:
        raise DesignError(
            f"campaign.id {bid!r} must be 1..{BATTLE_ID_MAX_LEN} characters")
    if not (bid[0].isascii() and bid[0].isalpha()):
        raise DesignError(
            f"campaign.id {bid!r} must start with an ASCII letter")
    if not all(ch.isascii() and (ch.isalnum() or ch == "_") for ch in bid):
        raise DesignError(
            f"campaign.id {bid!r} may only contain ASCII letters, digits and "
            f"underscore (it becomes an INI section name)")
    if OFFICIAL_BATTLE_ID_RE.match(bid):
        raise DesignError(
            f"campaign.id {bid!r} is an official battle id (ALL1/SOV1/...) — "
            f"re-using one overrides an official campaign entry; use your own "
            f"id such as {DEFAULT_BATTLE_ID}")
    return bid


def description_for(camp: dict) -> str:
    """Campaign-level blurb for the BATTLEMD98.INI Description value (R3)."""
    text = str(camp.get("description") or "").strip()
    return re.sub(r"[\r\n]+", " ", text).strip()


def default_design() -> dict:
    """A minimal but complete 1-mission design used by `ra2forge example`."""
    return {
        "campaign": {
            "name": "Example Operation",
            "description": "An example campaign generated by RA2 Campaign Forge.",
            "side": "soviet",
            # optional battle id of the appended BATTLEMD98.INI entry (R1);
            # omit the field to get the default "RA2F1"
            "id": "RA2F1",
        },
        "missions": [
            {
                "name": "EX01",
                "title": "First Strike",
                "briefing": "Commander! Establish a base and wipe out the Allied outpost.",
                "theater": "TEMPERATE",
                "size": [90, 90],
                "player": {"house": "Russians"},
                "structures": [
                    {"owner": "Russians", "type": "NACNST", "row": 60, "col": 45},
                    {"owner": "Americans", "type": "GACNST", "row": 15, "col": 45,
                     "tag": "enemy_hq"},
                ],
                "units": [
                    {"owner": "Russians", "type": "MTNK", "row": 58, "col": 43},
                    {"owner": "Russians", "type": "MTNK", "row": 58, "col": 47},
                ],
                "infantry": [
                    {"owner": "Russians", "type": "E1", "row": 59, "col": 44},
                    {"owner": "Americans", "type": "GI", "row": 17, "col": 44},
                ],
                "objectives": [
                    {"type": "destroy_building", "structure_tag": "enemy_hq"},
                ],
            },
        ],
    }
