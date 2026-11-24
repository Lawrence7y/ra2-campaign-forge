"""MAPSELMD.INI registration for appended campaigns (W34 / ra2forge v11).

WHY THIS FILE EXISTS
--------------------
W33 established that both campaign-completion paths require MAPSELMD.INI:

  SkipMapSelect=no  : 0x005AE220 loads MAPSELMD.INI and calls 0x005CF760 with
                      the CURRENT map filename ([Scen+0x125C]) to find the
                      stage; an unknown map name logs
                      "MapSelect: Invalid stage!" and pops MSG:UnableMapSelect.
  SkipMapSelect=yes : 0x005ADF20 loads MAPSELMD.INI, takes the current stage
                      by index (0x005CF810) and walks its numbered children,
                      resolving each child NAME through 0x005CF6B0 and
                      comparing that stage's Scenario= with NextScenario.

The engine loads MAPSELMD.INI through CCFileClass (vtable 0x7E16B0), so a
LOOSE file in the game directory wins over ra2md.mix's copy (W29 Q1).
MAPSELMD.INI is a WHOLE-FILE override, not a merge: a minimal file containing
only our own stages would delete all official progression. Therefore v11
ALWAYS clones the complete official file and appends. Generating a minimal
file is a hard error (MapselmdError), never a warning.

OFFICIAL SYNTAX (reverse engineered in W34/EVIDENCE/step2, step3)
-----------------------------------------------------------------
* faction section [GDI] / [Nod]: numbered keys "1".."100" (loader starts at
  edi=1, inc, cmp edi,0x64; FIRST MISSING KEY STOPS THE LOOP). Each value is
  a STAGE NAME = a section name. Official: 1=ALL01..7=ALL07, 1=Sov01..7=Sov07.
* stage section [ALL01] etc.: "Scenario=<map filename>" ([stage+4], used by
  0x005CF760), plus UI fields (Description/VoiceOver/MapVQ/Overlays/Targets/
  ClickMap/Text1..7) and the NUMBERED CHILD KEYS "0".."255". A child key is a
  CLICK-MAP COLOUR INDEX; its value is a STAGE NAME (resolved by 0x005CF6B0,
  which compares against [stage+0]). The last official stage has NO child.
* all string comparisons in the lookups normalise BOTH operands to lowercase
  (0x7B5B30 -> 0x7CAFF4 adds 0x20 to 'A'..'Z') before a case-sensitive compare
  (0x7B4780), so VALUE matching is case-insensitive. INI section/key names are
  used verbatim: this module reproduces the official spelling exactly.
* line endings: CRLF (official file is 100% CRLF). The generic INI line reader
  (0x65D5C0) terminates on LF and skips CR, so lone LF also parses, but lone
  CR does not terminate a line. This module emits CRLF.

OFFLINE BOUNDARY
----------------
This module is an OFFLINE file generator. Whether the real game actually
advances an appended campaign on its MapSelect screen (interactive click-map
regions, VQA playback) is [待运行验证] and belongs to a later card. Nothing in
this file claims a campaign has been fixed on a live game.
"""
from __future__ import annotations

import hashlib
import re
from pathlib import Path

MAPSEL_FILE_NAME = "MAPSELMD.INI"
BUNDLED_OFFICIAL = Path(__file__).resolve().parent / "data" / "MAPSELMD.OFFICIAL.INI"

# Measured in W34/EVIDENCE/step1_extract_mapsel.py from ra2bench/ra2md.mix
# -> nested LOCALMD.MIX -> id 0x922B8CE7. Used as a self-check that the bundled
# resource is a byte-exact clone, not a reconstruction.
OFFICIAL_SIZE = 5573
OFFICIAL_SHA256 = (
    "074ccccd9e156d586d0ed099ceab78b3d72384c808725d8b5bee2c9799691d52")

# design.campaign.side -> official MAPSELMD.INI faction section.
# The shipped file has NO Yuri faction section (only GDI/Allied and Nod/Soviet);
# inventing [Yuri] would be a guess about the engine's side-name lookup, so a
# Yuri campaign is refused with an explicit error instead. [待运行验证]
SIDE_TO_FACTION = {"allied": "GDI", "soviet": "Nod"}
OFFICIAL_FACTION_STAGES = {
    "GDI": [f"ALL0{i}" for i in range(1, 8)],
    "Nod": [f"Sov0{i}" for i in range(1, 8)],
}
OFFICIAL_UI_FIELDS = ("Description", "VoiceOver", "MapVQ", "Overlays",
                      "Targets", "ClickMap")
# Colour 2 is proven to be a valid click-map region in BOTH official factions:
# [ALL01] 2=ALL02 and [Sov01] 2=Sov02. Each appended stage therefore gets a
# single child link "2=<next stage name>" instead of guessing colours 8+.
CHILD_COLOUR_INDEX = 2
FACTION_KEY_MAX = 100          # loader hard cap: cmp edi,0x64
CHILD_KEY_MAX = 256            # MapStage ctor hard cap: cmp eax,0x100


class MapselmdError(RuntimeError):
    """Raised when a MAPSELMD.INI base is unusable or an append is unsafe."""


# ---------------------------------------------------------------------------
# INI byte-level reader (preserves CRLF and every official line verbatim)
# ---------------------------------------------------------------------------

def _split_crlf(raw: bytes) -> list[bytes]:
    if b"\n" in raw.replace(b"\r\n", b""):
        raise MapselmdError(
            "the MAPSELMD.INI base contains lone-LF line endings; this module "
            "requires the official CRLF form (clone the official file)")
    return raw.split(b"\r\n")


def _section_index(lines: list[bytes]) -> dict[str, int]:
    out: dict[str, int] = {}
    for i, line in enumerate(lines):
        s = line.strip()
        if s.startswith(b"[") and s.endswith(b"]"):
            out.setdefault(s[1:-1].decode("latin-1"), i)
    return out


def _section_bounds(lines: list[bytes], start: int) -> tuple[int, int]:
    """(first content line, line index of the next section or len(lines))."""
    end = len(lines)
    for i in range(start + 1, len(lines)):
        s = lines[i].strip()
        if s.startswith(b"[") and s.endswith(b"]"):
            end = i
            break
    return start + 1, end


def _section_entries(lines: list[bytes], name: str) -> dict[str, str]:
    idx = _section_index(lines)
    if name not in idx:
        raise MapselmdError(f"base MAPSELMD.INI has no [{name}] section")
    a, b = _section_bounds(lines, idx[name])
    out: dict[str, str] = {}
    for line in lines[a:b]:
        s = line.strip()
        if not s or s.startswith(b";") or b"=" not in s:
            continue
        k, _, v = s.partition(b"=")
        out[k.strip().decode("latin-1")] = v.strip().decode("latin-1")
    return out


def _is_numbered_key(key: str) -> bool:
    return bool(re.fullmatch(r"\d+", key))


# ---------------------------------------------------------------------------
# base validation: a FULL clone, never a minimal file
# ---------------------------------------------------------------------------

def validate_official_base(raw: bytes) -> dict:
    """Assert `raw` is a structurally complete official MAPSELMD.INI.

    Rejects a minimal/hand-built file (the W29 CSF warning analogue): all 14
    official stage sections and BOTH faction sequences must be present. The
    exact SHA-256 is NOT required for a user-supplied base (other language
    editions may differ), but the bundled resource is checked against it.
    """
    if not isinstance(raw, (bytes, bytearray)):
        raise MapselmdError("MAPSELMD.INI base must be raw bytes")
    raw = bytes(raw)
    if len(raw) < 1000:
        raise MapselmdError(
            f"MAPSELMD.INI base is {len(raw)} bytes - a minimal file would "
            "wipe out every official campaign stage; refusing to generate")
    lines = _split_crlf(raw)
    idx = _section_index(lines)
    missing_sections = [s for s in ("GDI", "Nod", "GDISFX", "NODSFX", "Anims")
                        if s not in idx]
    all_stages = (OFFICIAL_FACTION_STAGES["GDI"]
                  + OFFICIAL_FACTION_STAGES["Nod"])
    missing_sections += [s for s in all_stages if s not in idx]
    if missing_sections:
        raise MapselmdError(
            "MAPSELMD.INI base is missing official section(s) "
            f"{missing_sections} - a partial/minimal file would break the "
            "official campaigns; clone the complete official file")
    for faction, want in OFFICIAL_FACTION_STAGES.items():
        entries = _section_entries(lines, faction)
        got = [entries.get(str(i), "") for i in range(1, 8)]
        if got != want:
            raise MapselmdError(
                f"[{faction}] official numbered keys 1..7 are {got}, expected "
                f"{want} - refusing to append to a damaged/partial base")
    for stage in all_stages:
        entries = _section_entries(lines, stage)
        if not entries.get("Scenario"):
            raise MapselmdError(
                f"[{stage}] has no Scenario= - refusing to append to a "
                "damaged/partial base")
    return {"size": len(raw), "sha256": hashlib.sha256(raw).hexdigest(),
            "sections": sorted(idx), "crlf": raw.count(b"\r\n"),
            "lone_lf": raw.count(b"\n") - raw.count(b"\r\n")}


def load_bundled_official() -> bytes:
    """Return the byte-exact official clone shipped with v11."""
    if not BUNDLED_OFFICIAL.is_file():
        raise MapselmdError(
            f"bundled official MAPSELMD.INI is missing at {BUNDLED_OFFICIAL}")
    raw = BUNDLED_OFFICIAL.read_bytes()
    if len(raw) != OFFICIAL_SIZE or \
            hashlib.sha256(raw).hexdigest() != OFFICIAL_SHA256:
        raise MapselmdError(
            "bundled MAPSELMD.INI is not the measured byte-exact official "
            "clone (size/sha256 mismatch) - refusing to generate")
    validate_official_base(raw)
    return raw


# ---------------------------------------------------------------------------
# append
# ---------------------------------------------------------------------------

def stage_names_for(design: dict, missions: list[dict]) -> list[str]:
    """Deterministic, collision-free stage section names for our missions."""
    camp = design.get("campaign") or {}
    seed = "|".join((str(camp.get("id") or "RA2F1"),
                     str(camp.get("name") or ""),
                     str((design.get("package") or {}).get("id") or "")))
    names = []
    official = set(OFFICIAL_FACTION_STAGES["GDI"]
                   + OFFICIAL_FACTION_STAGES["Nod"]
                   + list(SIDE_TO_FACTION.values()) + ["Anims", "GDISFX",
                                                         "NODSFX", "ALL00"])
    for m in missions:
        map_name = f"{m['name'].upper()}.MAP"
        digest = hashlib.sha256(f"{seed}|{map_name}".encode("utf-8")) \
            .hexdigest()[:8].upper()
        name = f"RA2F_{m['name'].upper()}_{digest}"
        if name in official:
            raise MapselmdError(f"generated stage name {name!r} collides with "
                                "an official section")
        names.append(name)
    if len(set(names)) != len(names):
        raise MapselmdError("duplicate generated stage names")
    return names


def faction_for(design: dict) -> str:
    side = str((design.get("campaign") or {}).get("side", "soviet")).lower()
    if side not in SIDE_TO_FACTION:
        raise MapselmdError(
            f"campaign.side={side!r} has no official faction section in "
            "MAPSELMD.INI (the shipped file has only [GDI]/[Nod]); refusing "
            "to invent a section the engine may never request. Use "
            "'allied' or 'soviet', or supply a base with a matching faction.")
    return SIDE_TO_FACTION[side]


def build_mapselmd(design: dict, missions: list[dict], chain: list[str], *,
                   base_bytes: bytes | None = None) -> tuple[bytes, dict]:
    """Clone the COMPLETE official MAPSELMD.INI and append our campaign.

    `chain[i]` is the NextScenario of mission i ("" ends the campaign), exactly
    as builder.mission_chain() produces it. Returns (bytes, report).
    """
    if not missions:
        raise MapselmdError("no missions to register")
    raw = load_bundled_official() if base_bytes is None else bytes(base_bytes)
    base_info = validate_official_base(raw)
    faction = faction_for(design)
    names = stage_names_for(design, missions)
    lines = _split_crlf(raw)
    idx = _section_index(lines)
    for name in names:
        if name in idx:
            raise MapselmdError(
                f"stage section [{name}] already exists in the base - "
                "refusing to overwrite an existing stage")

    # --- 1. faction section: append 8=,9=,... after the last numbered key ---
    entries = _section_entries(lines, faction)
    used = sorted(int(k) for k in entries if _is_numbered_key(k))
    last_ordinal = used[-1] if used else 0
    if used != list(range(1, last_ordinal + 1)):
        raise MapselmdError(
            f"[{faction}] numbered keys {used} are not a contiguous 1..N "
            "sequence; the loader would stop at the first gap")
    if last_ordinal + len(names) > FACTION_KEY_MAX:
        raise MapselmdError(
            f"[{faction}] would need key {last_ordinal + len(names)} > the "
            f"loader's hard cap {FACTION_KEY_MAX}")
    a, b = _section_bounds(lines, idx[faction])
    insert_at = a
    for i in range(a, b):
        line = lines[i].strip()
        if not line or line.startswith(b";"):
            continue
        if b"=" in line and _is_numbered_key(
                line.partition(b"=")[0].strip().decode("latin-1")):
            insert_at = i + 1
    new_keys = [(str(last_ordinal + i + 1), name)
                for i, name in enumerate(names)]
    lines[insert_at:insert_at] = [f"{k}={v}".encode("latin-1")
                                  for k, v in new_keys]

    # --- 2. append one stage section per mission ---------------------------
    # UI fields are cloned from the official LAST stage of this faction: they
    # reference real game assets (VQA/SHP/PCX), so the interactive MapSelect
    # screen has the same shape as an official stage. [待运行验证]
    ui = _section_entries(lines, OFFICIAL_FACTION_STAGES[faction][-1])
    trailing_empty = bool(lines) and lines[-1] == b""
    append: list[bytes] = []
    for i, m in enumerate(missions):
        map_name = f"{m['name'].upper()}.MAP"
        append.append(b"")
        append.append(f"; ---- RA2 Campaign Forge appended stage "
                      f"{i + 1}/{len(missions)} ({faction}) ----".encode("latin-1"))
        append.append(f"[{names[i]}]".encode("latin-1"))
        append.append(f"Scenario={map_name}".encode("latin-1"))
        for field in OFFICIAL_UI_FIELDS:
            append.append(f"{field}={ui.get(field, '')}".encode("latin-1"))
        # one child link per non-final stage: key = click-map colour index,
        # value = the NEXT STAGE'S NAME (not a map filename).
        if chain[i]:
            nxt = chain[i]
            next_idx = next((j for j, mm in enumerate(missions)
                             if f"{mm['name'].upper()}.MAP" == nxt.upper()), None)
            if next_idx is None:
                raise MapselmdError(
                    f"{map_name}: NextScenario={nxt!r} is not a mission of "
                    "this campaign; cannot build the child link")
            append.append(f"{CHILD_COLOUR_INDEX}={names[next_idx]}".encode("latin-1"))
        # final mission: NO numbered child -> the stage terminates, mirrored
        # by EndOfGame=yes in the map's [Basic] (builder sets it).
    if trailing_empty:
        lines[-1:-1] = append
    else:
        lines.extend(append)
    out = b"\r\n".join(lines)

    # --- 3. read back and verify the generated BYTES ------------------------
    report = _verify_output(out, raw, faction, names, missions, chain,
                            base_info)
    return out, report


def _verify_output(out: bytes, base: bytes, faction: str,
                   names: list[str], missions: list[dict], chain: list[str],
                   base_info: dict) -> dict:
    """Hard self-check on the exact bytes that will be written to disk."""
    if out.count(b"\r\n") == 0 or \
            out.count(b"\n") != out.count(b"\r\n"):
        raise MapselmdError("generated MAPSELMD.INI is not 100% CRLF")
    # zero loss: every official line survives verbatim, in order
    base_lines = [x for x in _split_crlf(base) if x]
    out_lines = _split_crlf(out)
    pos = 0
    for line in base_lines:
        try:
            pos = out_lines.index(line, pos) + 1
        except ValueError as exc:
            raise MapselmdError(
                f"official line {line!r} was lost or reordered") from exc
    idx = _section_index(out_lines)
    for s in base_info["sections"]:
        if s not in idx:
            raise MapselmdError(f"official section [{s}] lost")
    faction_entries = _section_entries(out_lines, faction)
    for i, want in enumerate(OFFICIAL_FACTION_STAGES[faction], 1):
        if faction_entries.get(str(i)) != want:
            raise MapselmdError(
                f"[{faction}] {i}= was altered (must stay {want})")
    for i, name in enumerate(names):
        if faction_entries.get(str(8 + i)) != name:
            raise MapselmdError(f"[{faction}] {8 + i}={name} not registered")
        entries = _section_entries(out_lines, name)
        want_map = f"{missions[i]['name'].upper()}.MAP"
        if entries.get("Scenario", "").upper() != want_map.upper():
            raise MapselmdError(
                f"[{name}] Scenario={entries.get('Scenario')!r}, expected "
                f"{want_map!r}")
        kids = {k: v for k, v in entries.items() if _is_numbered_key(k)}
        if chain[i]:
            nxt = chain[i]
            next_idx = next((j for j, mm in enumerate(missions)
                             if f"{mm['name'].upper()}.MAP" == nxt.upper()), None)
            if next_idx is None or kids != {str(CHILD_COLOUR_INDEX):
                                            names[next_idx]}:
                raise MapselmdError(
                    f"[{name}] child links {kids} do not point at the next "
                    "stage name")
        else:
            if kids:
                raise MapselmdError(
                    f"[{name}] is the final stage but still has child links "
                    f"{kids}; the campaign could not terminate")
    return {
        "base_size": base_info["size"],
        "base_sha256": base_info["sha256"],
        "out_size": len(out),
        "out_sha256": hashlib.sha256(out).hexdigest(),
        "faction": faction,
        "official_stages_kept": sum(1 for s in base_info["sections"]
                                    if s in OFFICIAL_FACTION_STAGES["GDI"]
                                    + OFFICIAL_FACTION_STAGES["Nod"]),
        "appended_stages": len(names),
        "appended_keys": [f"{8 + i}={n}" for i, n in enumerate(names)],
        "last_stage_terminates": not chain[-1],
        "crlf": out.count(b"\r\n"),
    }


def write_mapselmd(path: str | Path, data: bytes) -> Path:
    """Write the generated bytes verbatim (no encoding, no newline rewrite)."""
    p = Path(path)
    p.write_bytes(data)
    if p.read_bytes() != data:
        raise MapselmdError(f"{p}: MAPSELMD.INI readback mismatch")
    return p
